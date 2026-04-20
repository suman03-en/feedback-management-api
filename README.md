# Feedback Management System

A Django-based feedback workflow platform for organizations that need role-based access, department routing, responder assignment, and tracked responses.

This repository currently provides:
- Web UI using Django templates
- Authentication with a custom email-based user model
- Role and object-level permissions using Django Groups + django-guardian
- Feedback submission, assignment, response, and status flow

Note: DRF endpoints are not implemented yet in this repository.

## Current Feature Set

### 1) Authentication and User Model
- Custom user model in `account` app
- Email as login identity (no username)
- Name and optional department linkage per user
- Register, login, and logout flows

### 2) Role and Permission Model
- Global role setup via management command:
	- Employee
	- Responder
	- Department Manager
	- Feedback Admin
	- Auditor
- Object-level visibility/ownership rules via django-guardian
- Department managers and auditors can receive routed feedback visibility

### 3) Feedback Workflow
- Feedback creation with:
	- Creator tracking
	- Email capture from logged-in user
	- Department routing
- Status lifecycle:
	- pending
	- reviewed
	- resolved
- Feedback delete flow with object permission checks

### 4) Response Workflow
- Add, edit, delete feedback responses
- Mark feedback as reviewed or resolved from response form
- Assign feedback to responder users
- Prevent duplicate responder assignment records

### 5) Department Management
- Department model with manager/auditor relationships
- Department create view (permission-protected)
- Department creation management command

### 6) Admin and Management Utilities
- Django admin registrations for feedback, responses, departments, assignments, users
- Seed role-permission matrix command
- Department creation command

## Project Structure

- `account/`: custom user model, auth views/forms, role-seeding command
- `feedback/`: feedback domain models, permission helpers, views/forms/templates, management commands
- `config/`: Django project settings and URL configuration
- `templates/` and `static/`: UI templates and styles

## Tech Stack

- Python
- Django 6
- django-guardian
- python-decouple
- WhiteNoise
- SQLite (default development database)

## Setup and Run

### 1) Create and activate virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Configure environment

Create a `.env` file in project root (optional but recommended):

```env
DJANGO_SECRET_KEY=replace-with-a-secure-key
DJANGO_DEBUG=True
```

### 4) Run migrations

```bash
python manage.py migrate
```

### 5) Create superuser

```bash
python manage.py createsuperuser
```

### 6) Seed roles and permissions

```bash
python manage.py seed_roles_permissions
```

### 7) (Optional) Add departments

```bash
python manage.py adddepartment "HR" --description "Human Resources"
python manage.py adddepartment "IT" --description "Technology and Systems"
```

### 8) Start development server

```bash
python manage.py runserver
```

Open in browser:
- `http://127.0.0.1:8000/account/login/`
- `http://127.0.0.1:8000/feedback/`
- `http://127.0.0.1:8000/admin/`

## Main Routes

### Account
- `/account/register/`
- `/account/login/`
- `/account/logout/`

### Feedback
- `/feedback/`
- `/feedback/create/`
- `/feedback/<uuid>/`
- `/feedback/<uuid>/delete/`
- `/feedback/<uuid>/response/create/`
- `/feedback/<uuid>/responses/`
- `/feedback/response/<uuid>/edit/`
- `/feedback/response/<uuid>/delete/`
- `/feedback/<uuid>/assign/`
- `/feedback/department/create/`

## Management Commands

- `python manage.py seed_roles_permissions`
	- Creates/updates role groups and permission mappings

- `python manage.py adddepartment <name> --description <text>`
	- Creates a department record


## Known Limitations (Current State)

- API endpoints are not implemented yet (despite earlier README claim)
- Automated tests are not yet implemented in `account/tests.py` and `feedback/tests.py`
- In response creation flow, department permission assignment call currently passes a boolean instead of `response=` keyword argument
- Security and compliance hardening for production is not complete yet

## Suggested Next Milestones

1. Fix current correctness issues (template field references, permission sync helper, response permission assignment call)
2. Add feedback title/priority/category and list pagination/filtering
3. Implement audit logging and compliance controls (retention, traceability)
4. Add workflow enhancements (reassign, escalation, SLA tracking, bulk actions)
5. Add reporting dashboard and exports
6. Implement DRF API after workflow model stabilizes

## Production Readiness Notes

Before production use, complete these minimum checks:
- Move from SQLite to PostgreSQL
- Enforce environment-managed secret key and host settings
- Add security headers and rate limiting
- Add automated tests for permission matrix and lifecycle transitions
- Add backup/restore and monitoring strategy

## License

Add your preferred license here (for example, MIT).
