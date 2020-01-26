# AccountX-Backend

## Setup Guide

### Virtual environment
Create a virtualenvironment for the submodule `backend` and activate it.
Supported and tested python version is 3.8.0

### Dependencies
Install required Python packages using pip and `requirements.txt`
```bash
pip install -r requirements.txt
```

### Create database
```bash
python manage.py migrate
```

### Server
Run development server
```bash
python manage.py runserver
```
