from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO
from flask_mail import Mail

db = SQLAlchemy()
bcrypt = Bcrypt()
socketio = SocketIO(cors_allowed_origins="*")
mail = Mail()
# pip install bcrypt flask-cors