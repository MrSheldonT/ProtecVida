from flask import Flask, jsonify
from .config import Config
from .extensions import db, bcrypt
from flask_cors import CORS

def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)
    CORS(app, resources={r"/*": {"origins": "*"}})
    db.init_app(app)
    bcrypt.init_app(app)

    from .routes import cuenta, grupo, zona_segura
    app.register_blueprint(cuenta, url_prefix="/cuenta")
    app.register_blueprint(grupo, url_prefix="/grupo")
    app.register_blueprint(zona_segura, url_prefix="/zona_segura")


    @app.route("/")
    def index():
        return "Hello :D"
    #from app.routes import register_routes
    #register_routes(app=app)
    @app.errorhandler(404)
    def page_404(e):
            return """
    <pre>
    404
    </pre>
            """, 404
    @app.errorhandler(500)
    def internal_server_error(e):
        return jsonify({'error': 'Error interno del servidor'}), 500


    return app

