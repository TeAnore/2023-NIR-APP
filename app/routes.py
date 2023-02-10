from app import app
from app.service import *

@app.route('/')
@app.route('/index')
def index():

    Service.create_db()

    return "Hello, World!"