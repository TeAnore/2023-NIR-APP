# 2023-NIR-APP
NIRM 

### Required packages on venv:

```
python.exe -m pip install --upgrade pip
pip install -r requirements.txt
```
```
pip freeze > requirements.txt
```

### Initializing the application

Windows Platform:

```
set FLASK_APP=app.py
flask run
```

Linux Platform:

```
export FLASK_APP=app.py
flask run
```

### Data Base
Initializing:
```
flask db init
```

Updating:
```
flask db migrate -m "Comment"
flask db upgrade
```