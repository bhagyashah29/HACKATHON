import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    EXCHANGE_RATE_API_URL = os.environ.get("EXCHANGE_RATE_API_URL", "https://api.exchangerate-api.com/v4/latest")
    OCR_SPACE_API_KEY = os.environ.get("OCR_SPACE_API_KEY")

    MAX_CONTENT_LENGTH = int(float(os.environ.get("MAX_CONTENT_LENGTH_MB", "10")) * 1024 * 1024)
    UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads", "receipts")

    REMEMBER_COOKIE_DURATION = timedelta(days=30)
