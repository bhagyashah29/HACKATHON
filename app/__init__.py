import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv
from .models import db

login_manager = LoginManager()
migrate = Migrate()


def create_app():
    load_dotenv()

    app = Flask(__name__, template_folder=os.path.join(os.getcwd(), 'templates'), static_folder=os.path.join(os.getcwd(), 'static'))
    app.config.from_object('config.Config')

    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from .routes.auth import auth_bp
    from .routes.expenses import expenses_bp
    from .routes.admin import admin_bp
    from .routes.approvals import approvals_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(approvals_bp)

    @app.route('/')
    def index():
        from flask_login import current_user
        from flask import redirect, url_for, render_template
        if current_user.is_authenticated:
            return render_template('dashboard.html')
        return redirect(url_for('auth.login'))

    return app
