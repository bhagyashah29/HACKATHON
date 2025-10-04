from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from ..models import db, User, Company, Role
from ..utils import get_currency_for_country, load_countries
from .. import login_manager

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email'].lower()
        password = request.form['password']
        company_name = request.form['company_name']
        country = request.form['country']

        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('auth.signup'))

        currency = get_currency_for_country(country) or 'USD'

        company = Company(name=company_name, default_currency=currency)
        db.session.add(company)
        db.session.flush()

        user = User(email=email, full_name=full_name,
                    password_hash=generate_password_hash(password),
                    role=Role.ADMIN, company_id=company.id)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        return redirect(url_for('index'))

    countries = load_countries()
    return render_template('signup.html', countries=countries)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid credentials')
            return redirect(url_for('auth.login'))
        login_user(user, remember=True)
        return redirect(url_for('index'))
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
