from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import db, Admin, Company, Student, PlacementDrive, Application
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.get_id().startswith('admin_'):
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_students = Student.query.count()
    total_companies = Company.query.filter_by(approval_status='approved').count()
    total_drives = PlacementDrive.query.count()
    total_applications = Application.query.count()
    pending_companies = Company.query.filter_by(approval_status='pending').all()
    pending_drives = PlacementDrive.query.filter_by(status='pending').all()
    return render_template('admin/dashboard.html',
        total_students=total_students,
        total_companies=total_companies,
        total_drives=total_drives,
        total_applications=total_applications,
        pending_companies=pending_companies,
        pending_drives=pending_drives
    )


@admin_bp.route('/companies')
@login_required
@admin_required
def companies():
    search = request.args.get('search', '').strip()
    query = Company.query
    if search:
        query = query.filter(Company.name.ilike(f'%{search}%'))
    companies = query.order_by(Company.created_at.desc()).all()
    return render_template('admin/companies.html', companies=companies, search=search)


@admin_bp.route('/company/<int:cid>/approve')
@login_required
@admin_required
def approve_company(cid):
    company = Company.query.get_or_404(cid)
    company.approval_status = 'approved'
    db.session.commit()
    flash(f'{company.name} approved.', 'success')
    return redirect(url_for('admin.companies'))


@admin_bp.route('/company/<int:cid>/reject')
@login_required
@admin_required
def reject_company(cid):
    company = Company.query.get_or_404(cid)
    company.approval_status = 'rejected'
    db.session.commit()
    flash(f'{company.name} rejected.', 'warning')
    return redirect(url_for('admin.companies'))


@admin_bp.route('/company/<int:cid>/blacklist')
@login_required
@admin_required
def blacklist_company(cid):
    company = Company.query.get_or_404(cid)
    company.approval_status = 'blacklisted'
    db.session.commit()
    flash(f'{company.name} blacklisted.', 'danger')
    return redirect(url_for('admin.companies'))


@admin_bp.route('/company/<int:cid>/delete')
@login_required
@admin_required
def delete_company(cid):
    company = Company.query.get_or_404(cid)
    db.session.delete(company)
    db.session.commit()
    flash('Company deleted.', 'info')
    return redirect(url_for('admin.companies'))


@admin_bp.route('/students')
@login_required
@admin_required
def students():
    search = request.args.get('search', '').strip()
    query = Student.query
    if search:
        query = query.filter(
            (Student.name.ilike(f'%{search}%')) |
            (Student.roll_number.ilike(f'%{search}%')) |
            (Student.phone.ilike(f'%{search}%'))
        )
    students = query.order_by(Student.created_at.desc()).all()
    return render_template('admin/students.html', students=students, search=search)


@admin_bp.route('/student/<int:sid>/toggle')
@login_required
@admin_required
def toggle_student(sid):
    student = Student.query.get_or_404(sid)
    student.is_active = not student.is_active
    db.session.commit()
    status = 'activated' if student.is_active else 'deactivated'
    flash(f'Student {status}.', 'info')
    return redirect(url_for('admin.students'))


@admin_bp.route('/student/<int:sid>/delete')
@login_required
@admin_required
def delete_student(sid):
    student = Student.query.get_or_404(sid)
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted.', 'info')
    return redirect(url_for('admin.students'))


@admin_bp.route('/drives')
@login_required
@admin_required
def drives():
    drives = PlacementDrive.query.order_by(PlacementDrive.created_at.desc()).all()
    return render_template('admin/drives.html', drives=drives)


@admin_bp.route('/drive/<int:did>/approve')
@login_required
@admin_required
def approve_drive(did):
    drive = PlacementDrive.query.get_or_404(did)
    drive.status = 'approved'
    db.session.commit()
    flash('Drive approved.', 'success')
    return redirect(url_for('admin.drives'))


@admin_bp.route('/drive/<int:did>/reject')
@login_required
@admin_required
def reject_drive(did):
    drive = PlacementDrive.query.get_or_404(did)
    drive.status = 'rejected'
    db.session.commit()
    flash('Drive rejected.', 'warning')
    return redirect(url_for('admin.drives'))


@admin_bp.route('/applications')
@login_required
@admin_required
def applications():
    apps = Application.query.order_by(Application.application_date.desc()).all()
    return render_template('admin/applications.html', applications=apps)
