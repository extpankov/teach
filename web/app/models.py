import uuid
from . import db


class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    marks = db.Column(db.String(100))
    average = db.Column(db.Float)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    needed_grades_comment = db.Column(db.String(255))  # Добавлено поле

    student = db.relationship('Student', backref=db.backref('student_subjects', lazy=True))



class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    class_name = db.Column(db.String(50))
    average_score = db.Column(db.Float)
    title = db.Column(db.String(100))
    title_description = db.Column(db.String(255))
    unique_token = db.Column(db.String(36), unique=True, nullable=False)

    # Связь с моделью Subject
    subjects = db.relationship('Subject', backref='student_subject', lazy=True)

    # Определение метода save_history
    def save_history(self, period, average_score):
        history = StudentHistory(
            student_id=self.id,
            period=period,
            average_score=average_score,
            improved=self.has_improved(average_score)
        )
        db.session.add(history)
        db.session.commit()

    def has_improved(self, new_score):
        last_record = StudentHistory.query.filter_by(student_id=self.id).order_by(StudentHistory.period.desc()).first()
        if last_record:
            return new_score > last_record.average_score
        return None

    def __repr__(self):
        return f'<Student {self.first_name} {self.last_name}>'


class StudentHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    period = db.Column(db.String(50), nullable=False)
    average_score = db.Column(db.Float, nullable=False)
    improved = db.Column(db.Boolean, nullable=True)

    student = db.relationship('Student', backref=db.backref('history', lazy=True))
