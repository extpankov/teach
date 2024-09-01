import openpyxl
from xls2xlsx import XLS2XLSX
from app import db
from app.models import StudentRecord
import uuid
import json


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

        # Extracting student information
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

        student_dict['subjects'] = []

        # Extracting subject information
        for item in student_data[7:]:
            subject_dict = {}
            subject_dict['subj_name'] = item[0]
            try:
                subject_dict['marks'] = [mark for mark in item[1].split(',') if mark]
                subject_dict['average'] = float(item[2])
            except Exception as e:
                print(f"Ошибка при обработке предмета {item[0]}: {e}")
            student_dict['subjects'].append(subject_dict)

        dataset.append(student_dict)

    wb.close()

    print(f"Данные загружены для {len(dataset)} студентов.")
    return dataset


def calculate_overall_average(student_data):
    total_average = sum(subject['average'] for subject in student_data['subjects'])
    overall_average = total_average / len(student_data['subjects'])
    return overall_average


def calculate_needed_grades(student_data):
    needed_grades = []

    for subject in student_data['subjects']:
        current_average = subject['average']
        grades_needed = {"subject": subject['subj_name'], "fours_needed": 0, "fives_needed": 0}
        total_marks = len(subject['marks'])

        # Если средний балл уже 4.51 и выше, оценки не нужны
        if current_average >= 4.51:
            needed_grades.append(grades_needed)
            continue

        # Ограничение количества циклов
        max_iterations = 100

        # Если средний балл между 4.0 и 4.51, считаем, сколько нужно пятерок
        if current_average >= 4.0:
            grades_needed["fives_needed"] = calculate_needed_grades_to_reach_target(current_average, total_marks, 4.51, 5, max_iterations)

        # Если средний балл ниже 4.0, считаем, сколько нужно четверок и пятерок
        elif current_average < 4.0:
            grades_needed["fours_needed"] = calculate_needed_grades_to_reach_target(current_average, total_marks, 4.0, 4, max_iterations)
            current_average = (current_average * total_marks + grades_needed["fours_needed"] * 4) / (total_marks + grades_needed["fours_needed"])
            total_marks += grades_needed["fours_needed"]
            grades_needed["fives_needed"] = calculate_needed_grades_to_reach_target(current_average, total_marks, 4.51, 5, max_iterations)

        needed_grades.append(grades_needed)

    return needed_grades

def calculate_needed_grades_to_reach_target(current_average, total_marks, target_average, grade_value, max_iterations):
    needed_grades = 0
    while current_average < target_average and max_iterations > 0:
        needed_grades += 1
        current_average = (current_average * total_marks + grade_value) / (total_marks + 1)
        total_marks += 1
        max_iterations -= 1

    if max_iterations == 0:
        print(f"Внимание: Расчет необходимых оценок был остановлен из-за превышения лимита итераций.")

    return needed_grades



def assign_title(average_score):
    if 4.9 <= average_score <= 5.0:
        return "Великий Магистр Высшего Ранга (5+)", "Абсолютный повелитель знаний, достигший вершины академического Олимпа. Этот ранг присваивается только истинным мастерам, которые превосходят все ожидания."
    elif 4.5 <= average_score < 4.9:
        return "Магистр Всеведущего Разума (5)", "Звание, достойное мудрецов, чьи знания охватывают все аспекты учебных дисциплин. Эти ученики демонстрируют непревзойденное понимание предмета."
    elif 4.0 <= average_score < 4.5:
        return "Архимаг Мудрости (4+)", "Ученик, овладевший магией науки и знания. Сильный и целеустремленный, этот ранг говорит о высоком уровне подготовки и стремлении к совершенству."
    elif 3.7 <= average_score < 4.0:
        return "Великий Хранитель Знаний (4)", "Титул, присваиваемый тем, кто с честью и упорством преодолевает все вызовы учебного пути. Ученик уверен в своих знаниях и готов покорять новые вершины."
    elif 3.5 <= average_score < 3.7:
        return "Мастер Откровений (3)", "Тот, кто видит свет знаний и идет по пути просветления, но ещё нуждается в усиленной практике, чтобы достичь высших сфер."
    elif 3.3 <= average_score < 3.5:
        return "Рыцарь Учебного Пути (3)", "Доблестный воин на пути к знаниям. Хотя испытания продолжаются, этот ученик твёрдо идёт вперед, стремясь к большему."
    elif 3.0 <= average_score < 3.3:
        return "Посвящённый Искатель Истины (3)", "Смелый начинающий ученик, только вступивший на великий путь поиска знаний. Этот ранг отмечает тех, кто начинает своё восхождение к вершинам академии."
    else:
        return "Неофит Знаний", "Начало великого пути! Неофит только вступил в мир знаний, и ему предстоит пройти через многие испытания, чтобы достичь успеха. Этот ранг – знак готовности к борьбе и совершенствованию."


def save_student_to_db(student_data):
    title, title_description = assign_title(student_data['average_score'])
    needed_grades = calculate_needed_grades(student_data)

    # Подготовка данных для сохранения
    student_record = StudentRecord(
        student_name=student_data['name'],
        class_name=student_data['class'],
        grades=json.dumps(student_data['subjects'], ensure_ascii=False),
        average_score=student_data['average_score'],
        title=title,
        period=student_data['period'],
        title_description=title_description,
        needed_grades=json.dumps(needed_grades, ensure_ascii=False)
    )

    db.session.add(student_record)
    print("session added")
    db.session.commit()
    print("session committed")


def process_data(filename):
    print("process data started")
    dataset = get_dataset(filename)
    print("database got")
    processed_students = []

    for student in dataset:
        student_info = {}
        student_info['name'] = student['name']
        print(student_info['name'])
        student_info['class'] = student['class']
        student_info['subjects'] = student.get('subjects', [])  # Обработка, если 'subjects' отсутствует
        student_info['overall_average'] = calculate_overall_average(student)
        student_info['average_score'] = student_info['overall_average']

        if 'period' in student:
            student_info['period'] = student['period']
        else:
            print(f"Ошибка: Период отсутствует для студента {student['name']}")

        student_info['needed_grades'] = calculate_needed_grades(student)

        print(student_info)
        print("приступаем к сохранению в БД")
        save_student_to_db(student_info)
        processed_students.append(student_info)


if __name__ == "__main__":
    process_data("your_data_file.xlsx")
