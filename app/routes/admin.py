from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ..models import db, User, Role, Company, ApprovalStep, ApprovalRule, ApprovalRuleType
from ..utils import require_roles

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.before_request
def ensure_admin():
    # Redirect non-admins
    if not (getattr(current_user, 'is_authenticated', False) and current_user.role == Role.ADMIN):
        return redirect(url_for('index'))


@admin_bp.route('/')
@login_required
def dashboard():
    users = User.query.filter_by(company_id=current_user.company_id).all()
    steps = (ApprovalStep.query
             .filter_by(company_id=current_user.company_id)
             .order_by(ApprovalStep.sequence)
             .all())
    rules = ApprovalRule.query.filter_by(company_id=current_user.company_id).all()
    # Company-wide expenses for oversight
    from ..models import Expense
    expenses = Expense.query.join(User, Expense.user_id == User.id) \
        .filter(User.company_id == current_user.company_id) \
        .order_by(Expense.created_at.desc()).all()
    return render_template('admin/dashboard.html', users=users, steps=steps, rules=rules, expenses=expenses)


@admin_bp.route('/users/create', methods=['POST'])
@login_required
def create_user():
    email = request.form['email'].lower()
    full_name = request.form['full_name']
    role = request.form['role']
    manager_id = request.form.get('manager_id') or None
    password = request.form['password']

    if User.query.filter_by(email=email).first():
        flash('Email already exists')
        return redirect(url_for('admin.dashboard'))

    user = User(email=email, full_name=full_name, role=Role(role),
                password_hash=password,  # will be hashed by trigger below
                company_id=current_user.company_id,
                manager_id=int(manager_id) if manager_id else None)

    from werkzeug.security import generate_password_hash
    user.password_hash = generate_password_hash(password)

    db.session.add(user)
    db.session.commit()
    flash('User created')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/users/update_role', methods=['POST'])
@login_required
def update_role():
    user_id = int(request.form['user_id'])
    role = request.form['role']
    user = User.query.get_or_404(user_id)
    user.role = Role(role)
    db.session.commit()
    flash('Role updated')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/users/update_manager', methods=['POST'])
@login_required
def update_manager():
    user_id = int(request.form['user_id'])
    manager_id = request.form.get('manager_id')
    user = User.query.get_or_404(user_id)
    user.manager_id = int(manager_id) if manager_id else None
    db.session.commit()
    flash('Manager updated')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/users/toggle_manager_approver', methods=['POST'])
@login_required
def toggle_manager_approver():
    user_id = int(request.form['user_id'])
    user = User.query.get_or_404(user_id)
    user.is_manager_approver = request.form.get('is_manager_approver') == 'on'
    db.session.commit()
    flash('Manager approver setting updated')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/approval_steps/create', methods=['POST'])
@login_required
def create_step():
    name = request.form['name']
    sequence = int(request.form['sequence'])
    approver_id = request.form.get('approver_user_id')

    step = ApprovalStep(company_id=current_user.company_id,
                        name=name,
                        sequence=sequence,
                        approver_user_id=int(approver_id) if approver_id else None)
    db.session.add(step)
    db.session.commit()
    flash('Approval step added')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/approval_rules/create', methods=['POST'])
@login_required
def create_rule():
    rule_type = request.form['rule_type']
    percentage_threshold = request.form.get('percentage_threshold')
    specific_approver_user_id = request.form.get('specific_approver_user_id')

    rule = ApprovalRule(company_id=current_user.company_id,
                        rule_type=rule_type,
                        percentage_threshold=int(percentage_threshold) if percentage_threshold else None,
                        specific_approver_user_id=int(specific_approver_user_id) if specific_approver_user_id else None)
    db.session.add(rule)
    db.session.commit()
    flash('Approval rule added')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/expenses/override', methods=['POST'])
@login_required
def override_expense():
    if current_user.role != Role.ADMIN:
        return redirect(url_for('index'))
    from ..models import Expense, ExpenseStatus
    expense_id = int(request.form['expense_id'])
    action = request.form['action']
    expense = Expense.query.get_or_404(expense_id)
    if action == 'approve':
        expense.status = ExpenseStatus.APPROVED
    elif action == 'reject':
        expense.status = ExpenseStatus.REJECTED
    db.session.commit()
    flash('Expense overridden')
    return redirect(url_for('admin.dashboard'))
