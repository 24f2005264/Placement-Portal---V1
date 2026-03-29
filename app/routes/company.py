from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import db, Company, PlacementDrive, Application, Student
from functools import wraps
from datetime import date

company_bp = Blueprint('company', __name__)

def company_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.get_id().startswith('company_'):
            flash('Company access required.', 'danger')
            return redirect(url_for('auth.login'))
        if current_user.approval_status != 'approved':
            flash('Your account is not approved yet.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@company_bp.route('/dashboard')
@login_required
@company_required
def dashboard():
    drives = PlacementDrive.query.filter_by(company_id=current_user.id).all()
    drive_data = []
    for d in drives:
        count = Application.query.filter_by(drive_id=d.id).count()
        drive_data.append({'drive': d, 'applicant_count': count})
    return render_template('company/dashboard.html', drive_data=drive_data)


@company_bp.route('/drive/new', methods=['GET', 'POST'])
@login_required
@company_required
def new_drive():
    if request.method == 'POST':
        drive = PlacementDrive(
            company_id=current_user.id,
            job_title=request.form.get('job_title', '').strip(),
            job_description=request.form.get('job_description', '').strip(),
            eligibility_criteria=request.form.get('eligibility_criteria', '').strip(),
            required_skills=request.form.get('required_skills', '').strip(),
            salary_range=request.form.get('salary_range', '').strip(),
            location=request.form.get('location', '').strip(),
            application_deadline=date.fromisoformat(request.form.get('application_deadline'))
        )
        db.session.add(drive)
        db.session.commit()
        flash('Drive submitted for admin approval.', 'success')
        return redirect(url_for('company.dashboard'))
    return render_template('company/drive_form.html', drive=None)


@company_bp.route('/drive/<int:did>/edit', methods=['GET', 'POST'])
@login_required
@company_required
def edit_drive(did):
    drive = PlacementDrive.query.get_or_404(did)
    if drive.company_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('company.dashboard'))
    if request.method == 'POST':
        drive.job_title = request.form.get('job_title', '').strip()
        drive.job_description = request.form.get('job_description', '').strip()
        drive.eligibility_criteria = request.form.get('eligibility_criteria', '').strip()
        drive.required_skills = request.form.get('required_skills', '').strip()
        drive.salary_range = request.form.get('salary_range', '').strip()
        drive.location = request.form.get('location', '').strip()
        drive.application_deadline = date.fromisoformat(request.form.get('application_deadline'))
        drive.status = 'pending'  # re-submit for approval
        db.session.commit()
        flash('Drive updated and re-submitted for approval.', 'success')
        return redirect(url_for('company.dashboard'))
    return render_template('company/drive_form.html', drive=drive)


@company_bp.route('/drive/<int:did>/close')
@login_required
@company_required
def close_drive(did):
    drive = PlacementDrive.query.get_or_404(did)
    if drive.company_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('company.dashboard'))
    drive.status = 'closed'
    db.session.commit()
    flash('Drive closed.', 'info')
    return redirect(url_for('company.dashboard'))


@company_bp.route('/drive/<int:did>/delete')
@login_required
@company_required
def delete_drive(did):
    drive = PlacementDrive.query.get_or_404(did)
    if drive.company_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('company.dashboard'))
    db.session.delete(drive)
    db.session.commit()
    flash('Drive deleted.', 'info')
    return redirect(url_for('company.dashboard'))


@company_bp.route('/drive/<int:did>/applications')
@login_required
@company_required
def drive_applications(did):
    drive = PlacementDrive.query.get_or_404(did)
    if drive.company_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('company.dashboard'))
    apps = Application.query.filter_by(drive_id=did).all()
    return render_template('company/applications.html', drive=drive, applications=apps)


@company_bp.route('/application/<int:aid>/status', methods=['POST'])
@login_required
@company_required
def update_status(aid):
    app = Application.query.get_or_404(aid)
    drive = PlacementDrive.query.get_or_404(app.drive_id)
    if drive.company_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('company.dashboard'))
    new_status = request.form.get('status')
    if new_status in ('shortlisted', 'selected', 'rejected'):
        app.status = new_status
        db.session.commit()
        flash('Application status updated.', 'success')
    return redirect(url_for('company.drive_applications', did=app.drive_id))


@company_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@company_required
def profile():
    if request.method == 'POST':
        current_user.hr_contact = request.form.get('hr_contact', '').strip()
        current_user.website = request.form.get('website', '').strip()
        current_user.industry = request.form.get('industry', '').strip()
        current_user.description = request.form.get('description', '').strip()
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('company.profile'))
    return render_template('company/profile.html')
