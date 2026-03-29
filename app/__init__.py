import os
from flask import Flask
from flask_login import LoginManager
from .models import db, Admin

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'ppa-secret-key-2024'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement_portal.db'
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    from .routes.auth import auth_bp
    from .routes.admin import admin_bp
    from .routes.company import company_bp
    from .routes.student import student_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(company_bp, url_prefix='/company')
    app.register_blueprint(student_bp, url_prefix='/student')

    with app.app_context():
        db.create_all()
        _seed_admin()

    return app

def _seed_admin():
    from werkzeug.security import generate_password_hash
    if not Admin.query.first():
        admin = Admin(
            username='admin',
            email='admin@placement.com',
            password=generate_password_hash('admin123')
        )
        db.session.add(admin)
        db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    from .models import Admin, Company, Student
    # user_id format: "role_id"
    parts = user_id.split('_', 1)
    if len(parts) != 2:
        return None
    role, uid = parts
    if role == 'admin':
        return Admin.query.get(int(uid))
    elif role == 'company':
        return Company.query.get(int(uid))
    elif role == 'student':
        return Student.query.get(int(uid))
    return None
