import re
from scripts.get_dataset import get_dataset
import pandas as pd
import os
import qrcode
from io import BytesIO
import base64
from app.models import Student  # Импорт модели Student для получения уникального токена


class PDFGenerator:
    def __init__(self, path, output_path):
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
        # Исходная строка с датами

        # Регулярное выражение для поиска дат
        pattern = r"(\d{2}\.\d{2}\.)(\d{4})"

        # Функция замены, сохраняющая день и месяц, но сокращающая год до двух цифр
        replacement = lambda x: x.group(1) + x.group(2)[-2:]

        # Производим замену в исходной строке
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
        # Генерация QR-кода с уникальной ссылкой
        url = f"http://example.com/student/{unique_token}"  # Используем уникальный токен студента
        print(f"link: {url}")
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')

        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

        return f'<img src="data:image/png;base64,{img_str}" alt="QR Code" />'

    def get_qr_code_block(self, data, student):
        subjects = ", ".join([self.replace_subjname(d["subj_name"]) for d in data])
        qr_code_image = self.generate_qr_code(student.unique_token)  # Передаем уникальный токен студента

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

    def create_html_card(self, row):
        # Найти студента по имени и фамилии
        student = Student.query.filter_by(first_name=row["name"].split()[1], last_name=row["name"].split()[0]).first()

        return f"""
        <div class="card">
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
                            {"".join([self.get_subject_object(data) for data in row["data"][:7]])}
                        </ul>
                    </div>
                </div>
            </div>
            {self.get_qr_code_block(row["data"][7:], student)}
        </div>
        """

    def generate_html(self):
        cards_html = ''.join([self.create_html_card(row) for index, row in self.dataset.iterrows()])

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
