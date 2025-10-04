from __future__ import annotations
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from enum import Enum


db = SQLAlchemy()


class Role(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    default_currency = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship('User', backref='company', lazy=True)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    role = db.Column(db.Enum(Role), nullable=False, default=Role.EMPLOYEE)

    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)

    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    manager = db.relationship('User', remote_side=[id], backref='team_members')

    is_manager_approver = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ExpenseStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Expense(db.Model):
    __tablename__ = 'expenses'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    amount_in_company_currency = db.Column(db.Float, nullable=True)

    category = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    expense_date = db.Column(db.Date, nullable=False)

    receipt_filename = db.Column(db.String(255), nullable=True)

    status = db.Column(db.Enum(ExpenseStatus), default=ExpenseStatus.PENDING, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='expenses')


class ApprovalDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalStep(db.Model):
    __tablename__ = 'approval_steps'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)

    name = db.Column(db.String(120), nullable=False)  # e.g., Manager, Finance, Director
    sequence = db.Column(db.Integer, nullable=False)

    approver_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # optional specific approver

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    company = db.relationship('Company', backref='approval_steps')
    approver_user = db.relationship('User')


class ApprovalRuleType(str, Enum):
    PERCENTAGE = "percentage"
    SPECIFIC_APPROVER = "specific_approver"
    HYBRID = "hybrid"


class ApprovalRule(db.Model):
    __tablename__ = 'approval_rules'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)

    rule_type = db.Column(db.Enum(ApprovalRuleType), nullable=False)
    percentage_threshold = db.Column(db.Integer, nullable=True)
    specific_approver_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    company = db.relationship('Company', backref='approval_rules')
    specific_approver_user = db.relationship('User')


class ExpenseApproval(db.Model):
    __tablename__ = 'expense_approvals'
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'), nullable=False)

    step_id = db.Column(db.Integer, db.ForeignKey('approval_steps.id'), nullable=True)
    approver_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    decision = db.Column(db.Enum(ApprovalDecision), nullable=True)
    comment = db.Column(db.Text, nullable=True)
    decided_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    expense = db.relationship('Expense', backref='approvals')
    step = db.relationship('ApprovalStep')
    approver_user = db.relationship('User')
