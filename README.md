# AccountX-Backend

## Install required Python packages using pip and requirements.txt
```shell
pip install -r requirements.txt
```

## Create database
```shell
python manage.py migrate
```

## Load initial data to database using Django fixtures 
```shell
python manage.py loaddata initial_companies
python manage.py loaddata initial_bookingTypes
python manage.py loaddata initial_sales
python manage.py loaddata initial_purchases
```
