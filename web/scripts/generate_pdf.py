import re
from scripts.get_dataset import get_dataset
import pandas as pd
import os
import qrcode
from io import BytesIO
import base64
import json
from app.models import StudentRecord  # Import the StudentRecord model

class PDFGenerator:
    def __init__(self, path, output_path):
        print("PDFGenerator started")
        self.dataset = pd.DataFrame(get_dataset(path))
        self.output_path = output_path

    def replace_subjname(self, subjname):
        replace_list = [
            {
                "original": "Иностранный язык (английский)",
                "to": "Иностранный язык"
            },
            {
                "original": "Литературное чтение на родном языке (русский)",
                "to": "Литературное чтение на родном языке"
            },
            {
                "original": "Основы религиозных культур и светской этики",
                "to": "ОРКСЭ"
            },
            {
                "original": "Изобразительное искусство",
                "to": "ИЗО"
            },
        ]

        for r in replace_list:
            if subjname == r["original"]:
                return r["to"]
        return subjname

    def get_arrow(self):
        with open("html/icons/svg/arrow-right-solid.svg", "r") as f:
            svg = f.read()
        return svg

    def reformat_date(self, date):
        pattern = r"(\d{2}\.\d{2}\.)(\d{4})"
        replacement = lambda x: x.group(1) + x.group(2)[-2:]
        result = re.sub(pattern, replacement, date)
        return result

    def get_subject_object(self, data):
        return f"""
        <li>
            <strong class="name">{self.replace_subjname(data["subj_name"])}</strong>
            <span>
                {"".join(str(i) for i in data["marks"])}
                {self.get_arrow()}
                <strong>{data["average"]}</strong>
            </span>
        </li>
        """

    @staticmethod
    def generate_qr_code(unique_token):
        url = f"https://teach.extpankov.ru/student/{unique_token}"  # Replace with the actual domain
        print(f"link: {url}")
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')

        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

        return f'<img src="data:image/png;base64,{img_str}" alt="QR Code" />'

    def get_qr_code_block(self, data, student_record):
        subjects = ", ".join([f"<b>{self.replace_subjname(d['subj_name'])}</b>" for d in data])
        qr_code_image = self.generate_qr_code(student_record.unique_token)  # Use the unique token from StudentRecord

        if subjects == "":
            return f"""
            <div class="qr-code-block">
                <p>Отсканируйте QR код, чтобы посмотреть полную статистику:</p>
                {qr_code_image}
            </div>
            """
        else:
            return f"""
            <div class="qr-code-block">
                <p>Предметы {subjects} не уместились на этом листе. Отсканируйте QR код, чтобы посмотреть полную статистику:</p>
                {qr_code_image}
            </div>
            """

    def create_html_card(self, row, top):
        # Найти запись студента по имени
        student_record = StudentRecord.query.filter_by(student_name=row["name"], class_name=row["class"]).order_by(
            StudentRecord.id.desc()).first()

        if not student_record:
            return "<p>Запись студента не найдена</p>"

        # Преобразовать JSON-строку с оценками обратно в список
        grades = json.loads(student_record.grades)

        # Устанавливаем фон в зависимости от места в топе
        background_image = ""
        if not top.empty:  # Проверяем, что DataFrame не пустой
            # Сравнение по индексам
            if row["name"] == top.iloc[0]["name"]:
                background_image = 'background-image: url(https://teach.extpankov.ru/prize/1);'
            elif len(top) > 1 and row["name"] == top.iloc[1]["name"]:
                background_image = 'background-image: url(https://teach.extpankov.ru/prize/2);'
            elif len(top) > 2 and row["name"] == top.iloc[2]["name"]:
                background_image = 'background-image: url(https://teach.extpankov.ru/prize/3);'

        return f"""
        <div class="card" style="{background_image}">
            <div class="container">
                <h2 class="card_name">Промежуточная успеваемость учащегося</h2>
                <div class="header">
                    <div class="header__el name">
                        Имя
                        <span>{" ".join(row["name"].split()[:2][::-1])}</span>
                    </div>
                    <div class="header__el class">
                        Класс
                        <span>{row["class"]}</span>
                    </div>
                    <div class="header__el period">
                        Период
                        <span>{self.reformat_date(row["period"])}</span>
                    </div>
                </div>
                <div class="line"></div>
                <div class="marks__container">
                    <div class="marks__header">
                        <h5>Предмет</h5>
                        <h5>оценки{self.get_arrow()}средний балл</h5>
                    </div>
                    <div class="marks__body">
                        <ul>
                            {"".join([self.get_subject_object(data) for data in grades[:7]])}
                        </ul>
                    </div>
                </div>
            </div>
            {self.get_qr_code_block(grades[7:], student_record)}
        </div>
        """

    def generate_html(self):
        # Сортируем учеников по среднему баллу в порядке убывания
        sorted_dataset = self.dataset.sort_values(by="average", ascending=False)

        # Извлекаем топ-3 учеников
        top_3_students = sorted_dataset.head(3)

        # Генерируем HTML-карточки для всех учеников, передавая информацию о топ-3
        cards_html = ''.join([self.create_html_card(row, top_3_students) for index, row in self.dataset.iterrows()])

        html_content = f"""
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Документ</title>
            <link rel="stylesheet" type="text/css" href="#CSS#">
        </head>
        <body>
            {cards_html}
        </body>
        </html>
        """

        return html_content

    def generate_pdf(self):
        with open(self.output_path, 'w') as f:
            f.write(self.generate_html().replace("#CSS#", '../styles'))
