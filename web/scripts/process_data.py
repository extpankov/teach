import openpyxl
from xls2xlsx import XLS2XLSX
from app import db
from app.models import Student, StudentHistory, Subject
import uuid


def get_dataset(filename: str):
    try:
        wb = openpyxl.load_workbook(filename)
    except Exception as e:
        print(f"Ошибка при загрузке файла: {e}")
        XLS2XLSX(filename).to_xlsx(filename + "x")
        wb = openpyxl.load_workbook(filename + "x")
    sheet = wb.active
    data = []

    for row in sheet.iter_rows(values_only=True):
        data.append(row)

    students_data = []
    current_student_data = []
    for item in data:
        if item[0] == 'Текущая успеваемость учащегося':
            if current_student_data:
                students_data.append(current_student_data[:-2])
            current_student_data = [item]
        else:
            current_student_data.append(item)

    if current_student_data:
        students_data.append(current_student_data[:-2])

    dataset = []

    for student_data in students_data:
        student_dict = {}

        # Извлечение данных о ФИО, классе, учителе, периоде и дате
        for item in student_data:
            if item[0] == 'ФИО учащегося:':
                student_dict['name'] = item[1]
            elif item[0] == 'Класс:':
                student_dict['class'] = item[1]
            elif item[0] == 'Кл. руководитель:':
                student_dict['teacher'] = item[1]
            elif item[0] == 'Период формирования успеваемости:':
                student_dict['period'] = item[1]
            elif item[0] == 'Дата формирования:':
                student_dict['date'] = item[1]

        student_dict['data'] = []

        # Извлечение данных о предметах, оценках и среднем балле
        for item in student_data[7:]:
            subject_dict = {}
            subject_dict['subj_name'] = item[0]
            try:
                subject_dict['marks'] = [mark for mark in item[1].split(',') if mark]
                subject_dict['average'] = float(item[2])
            except Exception as e:
                print(f"Ошибка при обработке предмета {item[0]}: {e}")
            student_dict['data'].append(subject_dict)

        dataset.append(student_dict)

    wb.close()

    print(f"Данные загружены для {len(dataset)} студентов.")
    return dataset


def calculate_overall_average(student_data):
    print(student_data)
    total_average = sum(subject['average'] for subject in student_data['data' if 'data' in student_data else 'subjects'])
    overall_average = total_average / len(student_data['data' if 'data' in student_data else 'subjects'])
    return overall_average


def calculate_needed_grades(student_data):
    if 'subjects' in student_data:
        student_data['data'] = student_data['subjects']
    current_average = calculate_overall_average(student_data)
    needed_grades = {"fours_needed": 0, "fives_needed": 0}

    if current_average >= 4.51:
        return needed_grades

    if current_average >= 4.0:
        while current_average <= 4.51:
            needed_grades["fives_needed"] += 1
            current_average = (current_average * len(student_data['data']) + 5) / (len(student_data['data']) + 1)
    elif current_average >= 3.0:
        while current_average <= 4.0:
            needed_grades["fours_needed"] += 1
            current_average = (current_average * len(student_data['data']) + 4) / (len(student_data['data']) + 1)
        while current_average <= 4.51:
            needed_grades["fives_needed"] += 1
            current_average = (current_average * len(student_data['data']) + 5) / (len(student_data['data']) + 1)

    return needed_grades


def assign_title(average_score):
    average_score *= 20
    if 90 <= average_score <= 100:
        return "Великий Магистр Высшего Ранга (A+)", "Абсолютный повелитель знаний, достигший вершины академического Олимпа. Этот ранг присваивается только истинным мастерам, которые превосходят все ожидания."
    elif 80 <= average_score < 90:
        return "Магистр Всеведущего Разума (A)", "Звание, достойное мудрецов, чьи знания охватывают все аспекты учебных дисциплин. Эти ученики демонстрируют непревзойденное понимание предмета."
    elif 70 <= average_score < 80:
        return "Архимаг Мудрости (B+)", "Ученик, овладевший магией науки и знания. Сильный и целеустремленный, этот ранг говорит о высоком уровне подготовки и стремлении к совершенству."
    elif 60 <= average_score < 70:
        return "Великий Хранитель Знаний (B)", "Титул, присваиваемый тем, кто с честью и упорством преодолевает все вызовы учебного пути. Ученик уверен в своих знаниях и готов покорять новые вершины."
    elif 50 <= average_score < 60:
        return "Мастер Откровений (C+)", "Тот, кто видит свет знаний и идет по пути просветления, но ещё нуждается в усиленной практике, чтобы достичь высших сфер."
    elif 40 <= average_score < 50:
        return "Рыцарь Учебного Пути (C)", "Доблестный воин на пути к знаниям. Хотя испытания продолжаются, этот ученик твёрдо идёт вперед, стремясь к большему."
    elif 30 <= average_score < 40:
        return "Посвящённый Искатель Истины (D)", "Смелый начинающий ученик, только вступивший на великий путь поиска знаний. Этот ранг отмечает тех, кто начинает своё восхождение к вершинам академии."
    else:
        return "Неофит Знаний (F)", "Начало великого пути! Неофит только вступил в мир знаний, и ему предстоит пройти через многие испытания, чтобы достичь успеха. Этот ранг – знак готовности к борьбе и совершенствованию."


def rank_students(students):
    students_with_averages = [(student, calculate_overall_average(student)) for student in students]
    students_with_averages.sort(key=lambda x: x[1], reverse=True)

    for rank, (student, _) in enumerate(students_with_averages, start=1):
        if rank <= 5:
            student['top'] = rank
        else:
            student['top'] = None


def save_student_to_db(student_data):
    title, title_description = assign_title(student_data['average_score'])
    student = Student.query.filter_by(first_name=student_data['name'].split()[1],
                                      last_name=student_data['name'].split()[0]).first()

    if student:
        student.average_score = student_data['average_score']
        student.title = title
        student.title_description = title_description
    else:
        student = Student(
            first_name=student_data['name'].split()[1],
            last_name=student_data['name'].split()[0],
            class_name=student_data['class'],
            average_score=student_data['average_score'],
            title=title,
            title_description=title_description,
            unique_token=str(uuid.uuid4())  # Генерация уникального токена
        )
        db.session.add(student)

    db.session.commit()

    # Сохранение данных о предметах
    for subj in student_data['subjects']:
        needed_grades = calculate_needed_grades(student_data)
        needed_grades_comment = (
            f"Для повышения оценки до пятёрки нужно: "
            f"{needed_grades['fives_needed']} пятёрок и "
            f"{needed_grades['fours_needed']} четвёрок."
        )

        subject = Subject(
            name=subj['subj_name'],
            marks=", ".join(subj['marks']),
            average=subj['average'],
            student_id=student.id,
            needed_grades_comment=needed_grades_comment  # Добавлено сохранение комментария
        )
        db.session.add(subject)

    db.session.commit()


def process_data(filename):
    dataset = get_dataset(filename)
    processed_students = []

    for student in dataset:
        student_info = {}
        student_info['name'] = student['name']
        student_info['class'] = student['class']
        student_info['overall_average'] = calculate_overall_average(student)
        student_info['subjects'] = student['data']  # Добавляем ключ 'subjects'
        student_info['average_score'] = student_info['overall_average']

        if 'period' in student:
            student_info['period'] = student['period']
        else:
            print(f"Ошибка: Период отсутствует для студента {student['name']}")

        student_info['needed_grades'] = calculate_needed_grades(student)

        save_student_to_db(student_info)
        processed_students.append(student_info)

    rank_students(dataset)
    print("Обработка завершена.")


if __name__ == "__main__":
    process_data("your_data_file.xlsx")
