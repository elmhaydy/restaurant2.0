# L’Héritage Gourmand — Django

## Installation
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py makemigrations
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Accès: `/`, `/menu/`, `/reservations/new/`, `/accounts/login/`, `/admin-panel/`, `/django-admin/`.
Comptes demo: `admin`, `chef`, `caissier`, `menage`, `client` avec `Pass12345!`.
Signups: `/accounts/signup/client/`, `/accounts/signup/staff/CHEF/`, `/accounts/signup/staff/CAISSIER/`, `/accounts/signup/staff/MENAGE/`, `/accounts/signup/staff/SERVEUR/`. Token staff: `dev-token`.
