# HABOT LSA Booking API

A Django REST Framework backend for managing LSA (Learning Support Assistant) profiles, parent booking requests, bookings, and payments.

## Features

- Parent management
- LSA profile management
- Search available LSAs by skill
- Booking request management
- Automatic LSA matching based on skill and availability
- Booking conflict checking
- Booking cancellation
- Payment creation
- Payment webhook for updating payment and booking status
- RESTful API endpoints
- Automated Django tests
- GitHub Actions CI workflow

## Tech Stack

- Python
- Django 6.1
- Django REST Framework
- SQLite / PostgreSQL support
- Git & GitHub
- GitHub Actions

## Project Structure

```text
habot-lsa-booking-api/
├── .github/
│   └── workflows/
│       └── tests.yml
├── bookings/
│   ├── migrations/
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── manage.py
├── requirements.txt
└── .gitignore
Installation

Clone the repository:

git clone https://github.com/rakshu112003/habot-lsa-booking-api.git
cd habot-lsa-booking-api

Create and activate a virtual environment:

python -m venv venv

Windows:

venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt
Database Setup

Run migrations:

python manage.py migrate
Run the Server
python manage.py runserver

The API will be available at:

http://127.0.0.1:8000/
API Endpoints
/api/parents/
/api/lsa-profiles/
/api/booking-requests/
/api/bookings/
/api/payments/
/api/payments/webhook/
LSA Search

Search available LSAs by skill:

GET /api/lsa-profiles/search/?skill=skill_name
Payment Webhook

Payment status can be updated through:

POST /api/payments/webhook/

Example request:

{
  "transaction_id": "TXN-TEST-001",
  "status": "SUCCESS"
}
Testing

Run the booking application tests:

python manage.py test bookings

The project currently passes all 7 tests.

Continuous Integration

GitHub Actions automatically runs:

Django system checks
Django booking tests

Workflow:

.github/workflows/tests.yml
Author

Rakshitha HN

GitHub: https://github.com/rakshu112003
