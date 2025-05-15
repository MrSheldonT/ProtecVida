from flask import Blueprint, jsonify, request
from .utils import token_required
from .extensions import db
from .models import Cuenta, TipoSignoVital, SignoVital
from sqlalchemy import desc
from datetime import datetime, timedelta
analisis_datos = Blueprint('analisis_datos', __name__)


@analisis_datos.route('/', methods=['GET'])
def analizar_signos():
    cuenta_id = request.args.get('cuenta_id', type=int)
    if not cuenta_id:
        return jsonify({'error': 'Parámetro cuenta_id es requerido'}), 400

    try:
        ahora = datetime.utcnow()
        hace_60 = ahora - timedelta(minutes=60)
        hace_15 = ahora - timedelta(minutes=15)

        signos = SignoVital.query.join(TipoSignoVital).filter(
            SignoVital.cuenta_id == cuenta_id,
        ).all()

        max_fc = None
        min_spo2 = None
        min_pas = None
        min_pad = None
        anomalos = []
        reglas = []
        condiciones = []
        puntaje = 1
        for signo in signos:
            print(signo.to_json())
        return jsonify({"xd": "xd"})

    except Exception as e:
        return jsonify({'error': f'Error {str(e)}'}), 500