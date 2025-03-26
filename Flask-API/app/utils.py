import string
import re
from functools import wraps
from datetime import datetime, timedelta
from flask import current_app, jsonify, request
from flask_bcrypt import Bcrypt
import jwt

EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
USER_PATTERN = r"^[a-zA-Z0-9_]{3,20}$"
bcrypt = Bcrypt()


def hash_password(password_original: str):
    return bcrypt.generate_password_hash(password_original).decode('utf-8')


def check_password(password:str, hashed_password:str):
    try:
        return bcrypt.check_password_hash(hashed_password, password)
    except:
        return False

def create_token_jwt(user_id):
    expiration_time = datetime.utcnow() + timedelta(seconds=current_app.config['JWT_EXPIRATION_TIME'])
    payload = {
        'user_id':user_id,
        'exp': expiration_time,
        'iat': datetime.utcnow(),
    }
    token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

    return token

# def token_require
def decode_jwt_token(token: str):
    try:
        payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return {"error": "Token has expired"}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token"}


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        token = request.headers.get("Authorization")
        if not token:
            return {"message": "Token is missing"}

        decoded_token = decode_jwt_token(token)

        if "error" in decoded_token:
            return {"message": decoded_token["error"]}

        request.user_id = decoded_token["user_id"]
        return f(*args, **kwargs)

    return decorated
def valid_email(email: str):
    return email and bool(re.fullmatch(EMAIL_PATTERN, email))

def valid_password(password: str):
    if len(password) <= 5:
        return False, "La contraseña debe de ser de al menos 6 caracteres."

    if not any(char.isdigit() for char in password):
        return False, "La contraseña debe de tener al menos un dígito númerico"

    if not any(char.isalpha() for char in password):
        return False, "La contraseña debe tener al menos una mayuscula"

    if not any(char in string.punctuation for char in password):
        return False, "La contraseña debe tener al menos un carácter especial"

    return True, "Password is valid."

def valid_date(date):
    try:
        return datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return None

