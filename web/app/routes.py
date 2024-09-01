import os
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, send_from_directory, redirect, url_for, Response
from werkzeug.utils import secure_filename
from scripts.process_data import process_data
from functools import wraps
import traceback
from flask import current_app
import json

from scripts.generate_pdf import PDFGenerator
from app.models import StudentRecord

main = Blueprint('main', __name__)

# Настройте имя пользователя и пароль
USERNAME = 'admin'
PASSWORD = '9X9BVr10'


# Декоратор для базовой аутентификации
def check_auth(username, password):
    """Функция проверки имени пользователя и пароля"""
    return username == USERNAME and password == PASSWORD


def authenticate():
    """Запросить аутентификацию"""
    return Response(
        'Необходимо ввести правильные учетные данные.', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )


def requires_auth(f):
    """Декоратор для защиты маршрутов"""

    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated


@main.route('/')
@requires_auth
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
            pdf_path = f"userfiles/ready/{pdf_filename}"
            process_data(file_path)

            # try:
            generator = PDFGenerator(file_path, pdf_path)
            generator.generate_pdf()
            # except Exception as e:
            #     print("error: ", e)

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
    return send_from_directory(directory="../userfiles/ready", path=filename)


def get_correct_grade_word(number, grade_type):
    if grade_type == "четверка":
        if number == 1:
            return f"одну четверку"
        elif 2 <= number <= 4:
            return f"{number} четверки"
        else:
            return f"{number} четверок"
    elif grade_type == "пятерка":
        if number == 1:
            return f"одну пятерку"
        elif 2 <= number <= 4:
            return f"{number} пятерки"
        else:
            return f"{number} пятерок"


@main.route('/prize/<step>')
def get_prize(step):
    return send_from_directory(directory="./static/imgs", path=f"{step}_new.png")


@main.route('/student/<unique_token>')
def student_info(unique_token):
    # Получаем текущую запись по уникальному токену или возвращаем 404, если не найдено
    record = StudentRecord.query.filter_by(unique_token=unique_token).first_or_404()

    # Получаем все записи ученика, исключая текущую запись
    history = StudentRecord.query.filter(
        StudentRecord.student_name == record.student_name,
        StudentRecord.class_name == record.class_name,
        StudentRecord.id != record.id  # Исключаем текущую запись
    ).all()

    # Преобразуем формат имени: Фамилия Имя Отчество -> Имя Фамилия
    name = record.student_name.split()
    record.student_name = f"{name[1]} {name[0]}"

    # Обрезаем средний балл до 4 знаков после запятой
    record.average_score = float(str(record.average_score)[:4])

    # Преобразуем строку с оценками (в формате JSON) обратно в список Python
    grades = json.loads(record.grades)



    # Подготовка нового списка с оценками, добавление комментариев
    new_grades = []
    for subj in grades:
        comments = []
        needed = json.loads(record.needed_grades)
        for n in needed:
            if n["subject"] == subj["subj_name"]:
                needed = n
                break

        if needed.get("fours_needed", 0) < 50 and needed.get("fives_needed", 0) < 50:
            if needed.get("fours_needed", 0) > 0:
                comments.append(get_correct_grade_word(needed['fours_needed'], "четверка"))

            if needed.get("fives_needed", 0) > 0:
                comments.append(get_correct_grade_word(needed['fives_needed'], "пятерка"))

            if comments:
                subj["comment"] = f"Нужно получить {' и '.join(comments)} для повышения оценки в четверти"
            else:
                subj["comment"] = "Вы прекрасны :)"
        else:
            subj["comment"] = f"{name[1]}, старайся, у тебя всё получится!"

        new_grades.append(subj)

    # Передаем данные и историю успеваемости в шаблон для рендеринга страницы
    return render_template('student_info.html', record=record, grades=new_grades, history=history)
