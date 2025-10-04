# Expense Manager (Flask)

Quick start:

1. Create and activate a virtualenv (if available):
   - python3 -m venv .venv && source .venv/bin/activate
   - If venv fails on Debian/Ubuntu, install: `sudo apt install python3-venv`
2. Install dependencies:
   - pip install -r requirements.txt
3. Configure environment:
   - cp .env.example .env
   - Edit .env with SECRET_KEY and OCR key (optional)
4. Initialize DB:
   - python init_db.py
5. Run:
   - python run.py

Features:
- Signup auto-creates company and admin with country currency
- Admin manages users, roles, manager relationships, approval steps/rules
- Employees submit expenses with receipts and currency selection
- Multi-level and conditional approvals (percentage, specific approver, hybrid)
- OCR integration via OCR.Space (optional)
- Currency conversion via exchangerate-api (free endpoint)
