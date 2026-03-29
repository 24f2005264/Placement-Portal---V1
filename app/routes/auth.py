from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from ..models import db, Admin, Company, Student
import os

auth_bp = Blueprint('auth', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        uid = current_user.get_id()
        if uid.startswith('admin_'):
            return redirect(url_for('admin.dashboard'))
        elif uid.startswith('company_'):
            return redirect(url_for('company.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))
    return render_template('auth/login.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', '')

        if role == 'admin':
            user = Admin.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('admin.dashboard'))
        elif role == 'company':
            user = Company.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                if user.approval_status == 'blacklisted':
                    flash('Your account has been blacklisted.', 'danger')
                    return redirect(url_for('auth.login'))
                if user.approval_status != 'approved':
                    flash('Your account is pending admin approval.', 'warning')
                    return redirect(url_for('auth.login'))
                login_user(user)
                return redirect(url_for('company.dashboard'))
        elif role == 'student':
            user = Student.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                if not user.is_active:
                    flash('Your account has been deactivated.', 'danger')
                    return redirect(url_for('auth.login'))
                login_user(user)
                return redirect(url_for('student.dashboard'))

        flash('Invalid credentials. Please try again.', 'danger')
    return render_template('auth/login.html')


@auth_bp.route('/register/company', methods=['GET', 'POST'])
def register_company():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        hr_contact = request.form.get('hr_contact', '').strip()
        website = request.form.get('website', '').strip()
        industry = request.form.get('industry', '').strip()
        description = request.form.get('description', '').strip()

        if Company.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register_company'))

        company = Company(
            name=name, email=email,
            password=generate_password_hash(password),
            hr_contact=hr_contact, website=website,
            industry=industry, description=description
        )
        db.session.add(company)
        db.session.commit()
        flash('Registration submitted. Await admin approval.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register_company.html')


@auth_bp.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        phone = request.form.get('phone', '').strip()
        roll_number = request.form.get('roll_number', '').strip()
        department = request.form.get('department', '').strip()
        cgpa = request.form.get('cgpa', '')
        skills = request.form.get('skills', '').strip()

        if Student.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register_student'))
        if roll_number and Student.query.filter_by(roll_number=roll_number).first():
            flash('Roll number already registered.', 'danger')
            return redirect(url_for('auth.register_student'))

        resume_filename = None
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename and allowed_file(file.filename):
                from flask import current_app
                filename = secure_filename(f"{roll_number}_{file.filename}")
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                resume_filename = filename

        student = Student(
            name=name, email=email,
            password=generate_password_hash(password),
            phone=phone, roll_number=roll_number,
            department=department,
            cgpa=float(cgpa) if cgpa else None,
            skills=skills, resume_filename=resume_filename
        )
        db.session.add(student)
        db.session.commit()
        flash('Registration successful. You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register_student.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
