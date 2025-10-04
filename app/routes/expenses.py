import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from ..models import db, Expense, ExpenseStatus
from ..services.currency import convert_amount
from ..services.ocr import parse_receipt_image

expenses_bp = Blueprint('expenses', __name__, url_prefix='/expenses')


@expenses_bp.route('/')
@login_required
def list_expenses():
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.created_at.desc()).all()
    return render_template('expenses/list.html', expenses=expenses)


@expenses_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_expense():
    if request.method == 'POST':
        amount = float(request.form['amount'])
        currency = request.form['currency']
        category = request.form['category']
        description = request.form.get('description')
        expense_date = datetime.strptime(request.form['expense_date'], '%Y-%m-%d').date()

        filename = None
        if 'receipt' in request.files and request.files['receipt'].filename:
            file = request.files['receipt']
            filename = datetime.utcnow().strftime('%Y%m%d%H%M%S_') + secure_filename(file.filename)
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            file.save(save_path)
            # OCR parse optionally
            _ = parse_receipt_image(save_path)

        expense = Expense(user_id=current_user.id,
                          amount=amount,
                          currency=currency,
                          category=category,
                          description=description,
                          expense_date=expense_date,
                          receipt_filename=filename)

        # Convert to company currency for visibility
        try:
            from_currency = currency
            to_currency = current_user.company.default_currency
            expense.amount_in_company_currency = convert_amount(amount, from_currency, to_currency)
        except Exception:
            expense.amount_in_company_currency = None

        db.session.add(expense)
        db.session.commit()
        flash('Expense submitted')
        return redirect(url_for('expenses.list_expenses'))

    # Let user choose common currencies
    currencies = ['USD', 'EUR', 'GBP', 'INR', 'JPY', 'AUD', 'CAD']
    return render_template('expenses/submit.html', currencies=currencies)
