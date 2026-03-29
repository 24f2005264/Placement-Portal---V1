from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from ..models import db, Student, PlacementDrive, Application
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import date
import os

student_bp = Blueprint('student', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.get_id().startswith('student_'):
            flash('Student access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    search = request.args.get('search', '').strip()
    today = date.today()
    query = PlacementDrive.query.filter_by(status='approved').filter(
        PlacementDrive.application_deadline >= today
    )
    if search:
        query = query.filter(
            (PlacementDrive.job_title.ilike(f'%{search}%')) |
            (PlacementDrive.required_skills.ilike(f'%{search}%'))
        )
    drives = query.order_by(PlacementDrive.application_deadline).all()
    applied_ids = {a.drive_id for a in Application.query.filter_by(student_id=current_user.id).all()}
    my_applications = Application.query.filter_by(student_id=current_user.id)\
        .order_by(Application.application_date.desc()).all()
    return render_template('student/dashboard.html',
        drives=drives, applied_ids=applied_ids,
        my_applications=my_applications, search=search
    )


@student_bp.route('/apply/<int:did>', methods=['POST'])
@login_required
@student_required
def apply(did):
    drive = PlacementDrive.query.get_or_404(did)
    if drive.status != 'approved':
        flash('This drive is not available.', 'danger')
        return redirect(url_for('student.dashboard'))
    if drive.application_deadline < date.today():
        flash('Application deadline has passed.', 'danger')
        return redirect(url_for('student.dashboard'))
    existing = Application.query.filter_by(student_id=current_user.id, drive_id=did).first()
    if existing:
        flash('You have already applied for this drive.', 'warning')
        return redirect(url_for('student.dashboard'))
    app = Application(
        student_id=current_user.id,
        drive_id=did,
        cover_letter=request.form.get('cover_letter', '').strip()
    )
    db.session.add(app)
    db.session.commit()
    flash('Application submitted successfully.', 'success')
    return redirect(url_for('student.dashboard'))


@student_bp.route('/applications')
@login_required
@student_required
def my_applications():
    apps = Application.query.filter_by(student_id=current_user.id)\
        .order_by(Application.application_date.desc()).all()
    return render_template('student/applications.html', applications=apps)


@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@student_required
def profile():
    if request.method == 'POST':
        current_user.name = request.form.get('name', '').strip()
        current_user.phone = request.form.get('phone', '').strip()
        current_user.department = request.form.get('department', '').strip()
        cgpa = request.form.get('cgpa', '')
        current_user.cgpa = float(cgpa) if cgpa else None
        current_user.skills = request.form.get('skills', '').strip()

        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{current_user.roll_number}_{file.filename}")
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                current_user.resume_filename = filename

        new_password = request.form.get('new_password', '')
        if new_password:
            current_user.password = generate_password_hash(new_password)

        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('student.profile'))
    return render_template('student/profile.html')
