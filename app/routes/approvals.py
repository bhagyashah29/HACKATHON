from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ..models import db, Expense, ExpenseApproval, ApprovalDecision, ExpenseStatus, ApprovalStep, ApprovalRule, ApprovalRuleType, Role
from ..utils import require_roles

approvals_bp = Blueprint('approvals', __name__, url_prefix='/approvals')


@approvals_bp.route('/')
@login_required
def list_pending():
    # Expenses awaiting current user's approval
    approvals = ExpenseApproval.query.filter_by(approver_user_id=current_user.id, decision=None).all()
    # Team expenses view for managers
    team_expenses = []
    if current_user.role in (Role.MANAGER, Role.ADMIN):
        team_member_ids = [m.id for m in current_user.team_members]
        if team_member_ids:
            team_expenses = (Expense.query
                             .filter(Expense.user_id.in_(team_member_ids))
                             .order_by(Expense.created_at.desc())
                             .all())
    return render_template('approvals/list.html', approvals=approvals, team_expenses=team_expenses)


def _get_next_approver(expense: Expense):
    # If employee has manager approver, first step is manager
    submitter = expense.user
    if submitter.is_manager_approver and submitter.manager_id:
        # If no manager approval record yet
        existing = ExpenseApproval.query.filter_by(expense_id=expense.id, approver_user_id=submitter.manager_id).first()
        if not existing:
            return None, submitter.manager_id

    # Otherwise follow company approval steps by sequence
    steps = ApprovalStep.query.filter_by(company_id=submitter.company_id).order_by(ApprovalStep.sequence).all()
    for step in steps:
        # If specific approver set
        approver_id = step.approver_user_id
        if approver_id is None:
            # Fallback to role-based approver: any admin/manager can approve? For simplicity, require specific approver.
            continue
        exists = ExpenseApproval.query.filter_by(expense_id=expense.id, approver_user_id=approver_id).first()
        if not exists:
            return step, approver_id
    return None, None


def _evaluate_conditional_rules(expense: Expense) -> bool | None:
    # Returns True for auto-approved, False for auto-rejected (not used), None for no decision
    rules = ApprovalRule.query.filter_by(company_id=expense.user.company_id).all()
    if not rules:
        return None

    approvals = expense.approvals
    total = len([a for a in approvals if a.decision is not None])
    approved = len([a for a in approvals if a.decision == ApprovalDecision.APPROVED])

    for rule in rules:
        if rule.rule_type == ApprovalRuleType.SPECIFIC_APPROVER and rule.specific_approver_user_id:
            for a in approvals:
                if a.approver_user_id == rule.specific_approver_user_id and a.decision == ApprovalDecision.APPROVED:
                    return True
        elif rule.rule_type == ApprovalRuleType.PERCENTAGE and rule.percentage_threshold:
            if total > 0 and (approved * 100 / total) >= rule.percentage_threshold:
                return True
        elif rule.rule_type == ApprovalRuleType.HYBRID:
            ok = False
            if rule.percentage_threshold and total > 0 and (approved * 100 / total) >= rule.percentage_threshold:
                ok = True
            if rule.specific_approver_user_id:
                for a in approvals:
                    if a.approver_user_id == rule.specific_approver_user_id and a.decision == ApprovalDecision.APPROVED:
                        ok = True
            if ok:
                return True
    return None


@approvals_bp.route('/request/<int:expense_id>')
@login_required
def create_requests(expense_id: int):
    expense = Expense.query.get_or_404(expense_id)
    # Create next approval request
    step, next_approver_id = _get_next_approver(expense)
    if next_approver_id:
        exists = ExpenseApproval.query.filter_by(expense_id=expense.id, approver_user_id=next_approver_id).first()
        if not exists:
            approval = ExpenseApproval(expense_id=expense.id, step_id=step.id if step else None, approver_user_id=next_approver_id)
            db.session.add(approval)
            db.session.commit()
            flash('Approval request sent to next approver')
    else:
        # No more approvers; evaluate conditional or finalize
        decision = _evaluate_conditional_rules(expense)
        if decision is True:
            expense.status = ExpenseStatus.APPROVED
        else:
            # default if no rules: approved when no pending approvers
            expense.status = ExpenseStatus.APPROVED
        db.session.commit()
        flash('Expense finalized')
    return redirect(url_for('expenses.list_expenses'))


@approvals_bp.route('/decide/<int:approval_id>', methods=['POST'])
@login_required
@require_roles([Role.MANAGER, Role.ADMIN])
def decide(approval_id: int):
    approval = ExpenseApproval.query.get_or_404(approval_id)
    if approval.approver_user_id != current_user.id:
        flash('Not authorized for this approval')
        return redirect(url_for('approvals.list_pending'))

    decision = request.form['decision']
    comment = request.form.get('comment')
    approval.decision = ApprovalDecision.APPROVED if decision == 'approve' else ApprovalDecision.REJECTED
    approval.comment = comment
    approval.decided_at = datetime.utcnow()
    db.session.commit()

    expense = approval.expense
    if approval.decision == ApprovalDecision.REJECTED:
        expense.status = ExpenseStatus.REJECTED
        db.session.commit()
        flash('Expense rejected')
        return redirect(url_for('approvals.list_pending'))

    # Approved: move to next approver
    step, next_approver_id = _get_next_approver(expense)
    if next_approver_id:
        exists = ExpenseApproval.query.filter_by(expense_id=expense.id, approver_user_id=next_approver_id).first()
        if not exists:
            next_approval = ExpenseApproval(expense_id=expense.id, step_id=step.id if step else None, approver_user_id=next_approver_id)
            db.session.add(next_approval)
    else:
        # No more approvers; conditional rules may auto-approve
        decision = _evaluate_conditional_rules(expense)
        if decision is True:
            expense.status = ExpenseStatus.APPROVED
        else:
            expense.status = ExpenseStatus.APPROVED
    db.session.commit()
    flash('Decision recorded')
    return redirect(url_for('approvals.list_pending'))
