# AccountX-Backend

## Setup Guide

### Virtual environment
Create a virtual environment and activate it.
Supported and tested python versions are 3.8.0 and 3.7.3.

If this app is used within a different project, it has to be ensured that the settings.py is set correctly.

### Dependencies
Install required Python packages using pip and `requirements.txt`
```bash
pip install -r requirements.txt
```

### Database
```bash
python manage.py migrate
```

### Superuser (optional)
Create an optional superuser
```bash
python manage.py createsuperuser
```

### Server
Run development server
```bash
python manage.py runserver
```
