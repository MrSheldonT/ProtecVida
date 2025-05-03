# tests/conftest.py
import pytest
from app import create_app
from app.extensions import db

@pytest.fixture
def app():
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "MAIL_SUPPRESS_SEND": True,
        "WTF_CSRF_ENABLED": False,
        "JWT_EXPIRATION_TIME": 3600,
        "SECRET_KEY": "TestSecretKey"
    }
    app = create_app(test_config)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()
