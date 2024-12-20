from flask import Flask, Response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from functools import wraps
from dotenv import load_dotenv
import base64
import os

db = SQLAlchemy()
migrate = Migrate()

load_dotenv()


USERNAME = os.getenv('DB_USER')
PASSWORD = os.getenv('DB_PASS')


def check_auth(username, password):
    """Функция проверки имени пользователя и пароля"""
    return username == USERNAME and password == PASSWORD


def authenticate():
    """Запросить аутентификацию"""
    return Response(
        'Необходимо ввести правильные учетные данные.', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

class AuthMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        request_path = environ.get('PATH_INFO', '')


        if request_path.startswith('/admin'):
            auth = environ.get('HTTP_AUTHORIZATION')
            if auth:
                auth_type, credentials = auth.split(None, 1)
                if auth_type.lower() == 'basic':
                    credentials = base64.b64decode(credentials).decode('utf-8')
                    username, password = credentials.split(':', 1)
                    if check_auth(username, password):
                        return self.app(environ, start_response)

            res = authenticate()
            return res(environ, start_response)

        return self.app(environ, start_response)

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')


    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.secret_key = os.getenv('FLASK_SECRET_KEY')


    db.init_app(app)
    migrate.init_app(app, db)


    from .models import StudentRecord, Title


    admin = Admin(app, name='Admin Panel', template_mode='bootstrap3')
    admin.add_view(ModelView(StudentRecord, db.session))
    admin.add_view(ModelView(Title, db.session))


    app.wsgi_app = AuthMiddleware(app.wsgi_app)


    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
