from app import app
from models import Message_app

@app.route('/')
def index():
    test = Message_app()
    return str(test)
