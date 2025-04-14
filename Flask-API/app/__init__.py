from flask import Flask, jsonify
from .config import Config
from .extensions import db, bcrypt, socketio, mail
from flask_mail import Message
from .utils import token_required, hash_password, create_token_jwt, valid_password, decode_jwt_token
from .models import Cuenta
from flask_cors import CORS
import os

def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
    app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_USERNAME")

    CORS(app, resources={r"/*": {"origins": "*"}})
    db.init_app(app)
    bcrypt.init_app(app)
    socketio.init_app(app)
    mail.init_app(app)

    from .routes import cuenta, grupo, zona_segura, condicion, signo_vital
    app.register_blueprint(cuenta, url_prefix="/cuenta")
    app.register_blueprint(grupo, url_prefix="/grupo")
    app.register_blueprint(zona_segura, url_prefix="/zona_segura")
    app.register_blueprint(condicion, url_prefix="/condicion")
    app.register_blueprint(signo_vital, url_prefix="/signo_vital")


    @app.route("/")
    def index():
        return "ProtecVida"

    import datetime
    @app.route('/enviar_token/<email>')
    def enviar_token(email):
        print(config.MAIL_PASSWORD)
        current_year = datetime.datetime.now().year
        user = Cuenta.query.filter_by(correo_electronico=email).first()
        if not user:
            return jsonify({'error': 'Cuenta no encontrada'}), 404

        token = create_token_jwt(user.id)
        msg = Message(
            'Tu enlace de recuperación de contraseña - ProtecVida',
            sender=os.getenv("MAIL_USERNAME"),
            recipients=[email]
        )

        html_content = render_template(
            'email.html',
            verification_url='localhost:5000/recuperar_contrasenia?token=' + token,
            year=current_year
        )

        msg.html = html_content

        try:
            mail.send(msg)
            print(f"Token enviado a {email}: {token}")
            return 'Correo enviado exitosamente.'
        except Exception as e:
            print(f"Error al enviar el correo: {e}")
            return 'Error al enviar el correo.', 500

    from flask import request, render_template
    @app.route("/recuperar_contrasenia", methods=["GET", "POST"])
    def recuperar_contrasenia():
        token = request.args.get("token")
        if not token:
            return render_template("reset_password.html", mensaje="No se cargó el token correctamente", token=token)

        if request.method == "POST":
            password = request.form.get("password")
            confirm_password = request.form.get("confirm_password")

            if not password or not confirm_password:
                return render_template("reset_password.html", mensaje="Completa todos los campos.", token=token)

            if password != confirm_password:
                return render_template("reset_password.html", mensaje="Las contraseñas no coinciden.", token=token)

            is_valid_password, message = valid_password(password)
            if not is_valid_password:
                return render_template("reset_password.html", mensaje="La contraseña debe tener al menos 8 caracteres.",
                                       token=token)

            try:
                decode_token = decode_jwt_token(token)
                update_user =  Cuenta.query.filter_by(id=decode_token['user_id']).first()
                if not update_user:
                    return render_template("reset_password.html", mensaje="Usuario no encontrado.",token=token)

                update_user.hash_contraseña = hash_password(password)
                db.session.commit()
                return render_template("success.html")
            except Exception as e:
                print(f"Error al enviar el correo: {e}")
                return render_template("error.html",
                                       mensaje="Ocurrió un error al actualizar la contraseña. Por favor intenta nuevamente.")

        return render_template("reset_password.html", token=token)


    @app.errorhandler(404)
    def page_404(e):
            return """
    <pre>
    404
    </pre>
            """, 404
    @app.errorhandler(500)
    def internal_server_error(e):
        return jsonify({'error': f'Error interno del servidor {str(e)}'}), 500


    return app

