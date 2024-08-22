import os
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename
from scripts.process_data import process_data
import traceback
from flask import current_app

from scripts.generate_pdf import PDFGenerator
from app.models import Student, StudentHistory


main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('index/index.html')


@main.route('/upload', methods=['POST'])
def upload_file():
    uploaded_files = request.files.getlist("file")
    for file in uploaded_files:
        if file:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            _, file_extension = os.path.splitext(file.filename)
            filename = secure_filename(f"{timestamp}{file_extension}")
            file_path = f"userfiles/{filename}"
            file.save(file_path)

            # Обрабатываем данные и генерируем PDF
            pdf_filename = f"{timestamp}.html"
            pdf_path = f"pdfs/{pdf_filename}"
            process_data(file_path)

            try:
                generator = PDFGenerator(file_path, pdf_path)
                generator.generate_pdf()
            except Exception as e:
                print(e)

            # После обработки данных и генерации PDF файла делаем редирект на страницу с PDF
            return jsonify({"pdf_filename": pdf_filename}), 200

    # Если что-то пошло не так, возвращаем ошибку
    return jsonify({"error": "Ошибка обработки файла"}), 400


@main.route('/styles')
def styles():
    return send_from_directory(directory="../html/styles", path='stylev2.css')


@main.route('/fonts/<filename>')
def fonts(filename):
    styles_directory = "../html/fonts"
    allowed_files = {
        "rubik-v28-cyrillic_latin-300.woff2",
        "rubik-v28-cyrillic_latin-500.woff2"
    }

    if filename not in allowed_files:
        return abort(404)  # Возвращаем 404, если файл не разрешен

    return send_from_directory(directory=styles_directory, path=filename)


@main.route('/pdfs/<filename>')
def download_pdf(filename):
    return send_from_directory(directory="../pdfs", path=filename)


@main.route('/student/<unique_token>')
def student_info(unique_token):
    student = Student.query.filter_by(unique_token=unique_token).first_or_404()
    current_grades = [
        {
            'subj_name': subj.name,
            'marks': subj.marks.split(", "),  # Преобразуйте строку в список оценок
            'average': subj.average
        } for subj in student.subjects
    ]
    return render_template('student_info.html', student=student, current_grades=current_grades)
