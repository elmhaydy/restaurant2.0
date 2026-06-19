# L'Heritage Gourmand

Application web Django de gestion de restaurant. Le projet regroupe un espace public pour les clients, un espace d'administration, et des interfaces metier selon les roles du personnel.

## Fonctionnalites

- Consultation du menu public avec categories et fiches plats
- Reservation de tables
- Creation et suivi des commandes
- Gestion des tables du restaurant
- Gestion du stock et des ingredients
- Gestion du personnel et historique de paiement
- Tableau de bord d'administration
- Authentification avec redirection selon le role utilisateur

## Stack technique

- Python 3.12+ recommande
- Django 5.2
- PostgreSQL
- Django REST Framework
- Django Jazzmin
- Pillow, ReportLab

Des dependances liees a `channels`, `redis` et `celery` sont presentes dans `requirements.txt`, mais la configuration visible du projet est surtout centree sur l'application web Django classique.

## Applications Django

- `accounts` : utilisateurs, roles, authentification
- `menu` : categories, plats, composition par ingredient
- `orders` : commandes et lignes de commande
- `reservations` : reservations clients
- `tables` : tables, capacites, statuts
- `stock` : ingredients et mouvements de stock
- `staffops` : interfaces metier pour chef, caissier, serveur, livreur, menage, manager
- `admin_panel` : back-office fonctionnel du restaurant
- `audit` : journalisation et suivi d'activite
- `core` : pages publiques et commande de demo

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Le projet attend une base PostgreSQL. Creez un fichier `.env` a la racine avec au minimum :

```env
DB_NAME=restaurant_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=127.0.0.1

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=contact@example.com
CONTACT_RECIPIENT_EMAIL=contact@example.com
```

Notes :

- Il n'y a pas de fichier `.env.example` dans le depot.
- `DEBUG` est active dans les settings actuels.
- La `SECRET_KEY` est definie en dur dans [restaurant_config/settings.py](/abs/path/C:/Users/elmeh/OneDrive/Bureau/restauration-main/restaurant_config/settings.py:1), ce qui convient pour du developpement mais pas pour la production.

## Initialisation

```bash
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Application disponible par defaut sur `http://127.0.0.1:8000/`.

## Comptes de demonstration

La commande `seed_demo` cree les comptes suivants avec le mot de passe `Pass12345!` :

- `admin`
- `chef`
- `caissier`
- `menage`
- `client`

## Routes utiles

- `/` : accueil
- `/contact/` : contact
- `/menu/` : carte du restaurant
- `/reservations/` : reservations
- `/orders/` : commandes
- `/accounts/login/` : connexion
- `/accounts/signup/client/` : inscription client
- `/staff/chef/` : espace chef
- `/staff/caissier/` : espace caissier
- `/staff/serveur/` : espace serveur
- `/staff/livreur/` : espace livreur
- `/staff/manager/` : espace manager
- `/admin-panel/` : panneau d'administration metier
- `/django-admin/` : administration Django

## Arborescence rapide

```text
accounts/           gestion des utilisateurs et roles
admin_panel/        back-office restaurant
audit/              journalisation
core/               pages publiques et commandes utilitaires
menu/               catalogue des plats
orders/             commandes
payments/           paiements
reservations/       reservations
restaurant_config/  configuration Django
staffops/           espaces personnel
stock/              ingredients et stock
tables/             gestion des tables
templates/          templates HTML
static/             assets statiques
media/              images uploadees
```

## Commandes utiles

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo
```

## Points d'attention

- Le projet est actuellement configure pour PostgreSQL uniquement.
- Le depot contient des fichiers `media/` et `debug.log`, ce qui indique un usage principalement local/developpement.
- Si vous preparez un deploiement, il faudra externaliser la `SECRET_KEY`, desactiver `DEBUG`, renseigner `ALLOWED_HOSTS` et durcir la configuration email/base de donnees.
