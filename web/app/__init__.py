from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')

    # Конфигурация базы данных
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Инициализация базы данных и миграций
    db.init_app(app)
    migrate.init_app(app, db)

    # Регистрация маршрутов
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
