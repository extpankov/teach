import uuid
from . import db


class StudentRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100))
    class_name = db.Column(db.String(50))
    grades = db.Column(db.Text)  # JSON строка с оценками
    average_score = db.Column(db.Float)
    title = db.Column(db.String(100))
    title_description = db.Column(db.String(255))
    needed_grades = db.Column(db.String(255), nullable=False)
    unique_token = db.Column(db.String(36), unique=True, nullable=False)
    period = db.Column(db.String(50), nullable=False)

    def __init__(self, student_name, class_name, grades, average_score, title, title_description, needed_grades, period):
        self.student_name = student_name
        self.class_name = class_name
        self.grades = grades
        self.average_score = average_score
        self.title = title
        self.title_description = title_description
        self.needed_grades = needed_grades
        self.unique_token = str(uuid.uuid4())
        self.period = period

    def __repr__(self):
        return f'<StudentRecord {self.student_name}>'
