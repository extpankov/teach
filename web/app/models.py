import uuid
from . import db


class Title(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<Title {self.name}>'


class StudentRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100))
    class_name = db.Column(db.String(50))
    grades = db.Column(db.Text)
    average_score = db.Column(db.Float)
    title_id = db.Column(db.Integer, db.ForeignKey('title.id'), nullable=False)
    needed_grades = db.Column(db.String(255), nullable=False)
    unique_token = db.Column(db.String(36), unique=True, nullable=False)
    period = db.Column(db.String(50), nullable=False)
    last_visited = db.Column(db.DateTime, nullable=True, default=None)

    title = db.relationship('Title', backref='student_records')

    def __init__(self, student_name, class_name, grades, average_score, title_id, needed_grades, period):
        self.student_name = student_name
        self.class_name = class_name
        self.grades = grades
        self.average_score = average_score
        self.title_id = title_id
        self.needed_grades = needed_grades
        self.unique_token = str(uuid.uuid4())
        self.period = period
        self.last_visited = None

    def __repr__(self):
        return f'<StudentRecord {self.student_name}>'
