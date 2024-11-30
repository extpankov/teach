import os
from datetime import datetime

from flask import Flask, render_template, request, Response, url_for, jsonify, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.utils import secure_filename

from scripts.generate_pdf import PDFGenerator

app = Flask(__name__, template_folder='templates', static_folder='static')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


def create_pdf(path, pdf_path):
    try:
        generator = PDFGenerator(path, pdf_path)
        generator.generate_pdf()
        return True
    except Exception as e:
        print(e)
        return False


@app.route('/')
def index():
    return render_template('index/index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    uploaded_files = request.files.getlist("file")
    for file in uploaded_files:
        if file:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            _, file_extension = os.path.splitext(file.filename)
            filename = secure_filename(f"{timestamp}{file_extension}")
            upload_dir = "web/userfiles"
            uploaded_file_path = f"{upload_dir}/{filename}"
            file.save(uploaded_file_path)


            pdf_filename = f"{timestamp}.html"
            pdf_dir = "web/userfiles/ready"
            pdf_path = f"{pdf_dir}/{pdf_filename}"
            res = create_pdf(uploaded_file_path, pdf_path)
            if res:
                return jsonify({"pdf_filename": pdf_filename}), 200
    return jsonify({"error": "Ошибка обработки файла"}), 400


@app.route('/styles')
def styles():
    styles_directory = "html/styles"
    filename = 'stylev2.css'
    return send_from_directory(directory=styles_directory, path=filename)


@app.route('/fonts/<filename>')
def fonts(filename):
    styles_directory = "html/fonts"
    allowed_files = {
        "rubik-v28-cyrillic_latin-300.woff2",
        "rubik-v28-cyrillic_latin-500.woff2"
    }

    if filename not in allowed_files:
        return abort(404)

    return send_from_directory(directory=styles_directory, path=filename)


@app.route('/pdfs/<filename>')
def download_pdf(filename):
    return send_from_directory(directory='pdfs', path=filename)


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001)
