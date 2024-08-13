from flask import Flask, request, jsonify
from flask_migrate import Migrate
from flask_login import LoginManager
from dotenv import load_dotenv
from database import db
import os

load_dotenv()

migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///incidents.db')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    from models import User
    from routes import main_bp

    app.register_blueprint(main_bp)


    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, use_reloader=True)
