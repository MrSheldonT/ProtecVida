import math
import string
import re
from functools import wraps
from datetime import datetime, timezone, timedelta
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
    expiration_time = datetime.now(timezone.utc) + timedelta(seconds=current_app.config['JWT_EXPIRATION_TIME'])
    iat = datetime.now(timezone.utc) 
    payload = {
        'user_id':user_id,
        'exp': expiration_time,
        'iat': iat,
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

def distancia_aproximada_metros(lat1, lon1, lat2, lon2):
    """
    Calcula una distancia aproximada en metros usando una fórmula simplificada.
    """
    # 1 grado de latitud = ~111,000 metros
    # 1 grado de longitud varía con la latitud (~111,000 * cos(lat))
    lat_dist = (lat2 - lat1) * 111000
    lon_dist = (lon2 - lon1) * 111000 * math.cos(math.radians((lat1 + lat2) / 2))
    return math.sqrt(lat_dist ** 2 + lon_dist ** 2)


def detectar_cambio_estado(lat_actual, lon_actual, lat_anterior, lon_anterior, zonas):
    def esta_en_alguna_zona(lat, lon):
        for zona in zonas:
            distancia = distancia_aproximada_metros(lat, lon, zona.latitud, zona.longitud)
            if distancia <= zona.radio:
                return True
        return False

    en_zona_antes = esta_en_alguna_zona(lat_anterior, lon_anterior)
    en_zona_ahora = esta_en_alguna_zona(lat_actual, lon_actual)

    if not en_zona_antes and en_zona_ahora:
        return "entrada"
    elif en_zona_antes and not en_zona_ahora:
        return "salida"
    else:
        return None
