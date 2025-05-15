from flask import Blueprint, jsonify, request
from .utils import token_required
from .extensions import db
from .models import Cuenta, TipoSignoVital, SignoVital
from sqlalchemy import desc
from datetime import datetime, timedelta
analisis_datos = Blueprint('analisis_datos', __name__)


@analisis_datos.route('/riesgo')
def riesgo():
    cuenta_id = request.args.get('cuenta_id', type=int)
    if not cuenta_id:
        return jsonify({'error': 'Falta cuenta_id'}), 400

    ahora = datetime.utcnow()
    ayer = ahora - timedelta(days=1)
    signos = SignoVital.query \
        .filter(SignoVital.cuenta_id == cuenta_id) \
        .filter(SignoVital.tipo_id.in_([1, 2, 3, 4])) \
        .filter(SignoVital.fecha >= ayer) \
        .all()

    hipert_vals = [];
    hipot_vals = []
    taqui_vals = [];
    bradi_vals = []
    hipox_vals = []

    for sv in signos:
        if sv.tipo_id == 1:  # FC
            if sv.valor_numerico_1 > 100:
                taqui_vals.append(sv.valor_numerico_1)
            elif sv.valor_numerico_1 < 60:
                bradi_vals.append(sv.valor_numerico_1)
        elif sv.tipo_id == 2:  # PAS
            if sv.valor_numerico_1 >= 130:
                hipert_vals.append(sv.valor_numerico_1)
            elif sv.valor_numerico_1 < 90:
                hipot_vals.append(sv.valor_numerico_1)
        elif sv.tipo_id == 3:  # PAD
            if sv.valor_numerico_1 >= 80:
                hipert_vals.append(sv.valor_numerico_1)
            elif sv.valor_numerico_1 < 60:
                hipot_vals.append(sv.valor_numerico_1)
        elif sv.tipo_id == 4:  # SpO2
            if sv.valor_numerico_1 < 90:
                hipox_vals.append(sv.valor_numerico_1)

    def calc_puntaje(vals, umbral_normal, tipo):
        ocurrencias = len(vals)
        if ocurrencias == 0:
            return None
        promedio = sum(vals) / ocurrencias
        severidad = promedio / umbral_normal
        puntaje = min(100, int(severidad * ocurrencias * 10))
        if puntaje < 30:
            desc = "riesgo bajo"
        elif puntaje < 70:
            desc = "riesgo moderado"
        else:
            desc = "riesgo alto"
        return {'ocurrencias': ocurrencias, 'promedio': round(promedio, 1),
                'puntaje': puntaje, 'descripcion': desc}

    resultado = []

    # Hipertensión
    datos = calc_puntaje(hipert_vals, 130, 'Hipertensión')
    if datos:
        resultado.append({
            'condición': 'Hipertensión',
            'ocurrencias': datos['ocurrencias'],
            'promedio_valor': f"{datos['promedio']} mmHg",
            'puntaje': datos['puntaje'],
            'descripcion': datos['descripcion']
        })

    # Hipotensión
    datos = calc_puntaje(hipot_vals, 90, 'Hipotensión')
    if datos:
        resultado.append({
            'condición': 'Hipotensión',
            'ocurrencias': datos['ocurrencias'],
            'promedio_valor': f"{datos['promedio']} mmHg",
            'puntaje': datos['puntaje'],
            'descripcion': datos['descripcion']
        })

    # Taquicardia
    datos = calc_puntaje(taqui_vals, 100, 'Taquicardia')
    if datos:
        resultado.append({
            'condición': 'Taquicardia',
            'ocurrencias': datos['ocurrencias'],
            'promedio_valor': f"{datos['promedio']} lpm",
            'puntaje': datos['puntaje'],
            'descripcion': datos['descripcion']
        })

    # Bradicardia
    datos = calc_puntaje(bradi_vals, 60, 'Bradicardia')
    if datos:
        resultado.append({
            'condición': 'Bradicardia',
            'ocurrencias': datos['ocurrencias'],
            'promedio_valor': f"{datos['promedio']} lpm",
            'puntaje': datos['puntaje'],
            'descripcion': datos['descripcion']
        })

    # Hipoxemia
    datos = calc_puntaje(hipox_vals, 90, 'Hipoxemia')
    if datos:
        resultado.append({
            'condición': 'Hipoxemia',
            'ocurrencias': datos['ocurrencias'],
            'promedio_valor': f"{datos['promedio']} %",
            'puntaje': datos['puntaje'],
            'descripcion': datos['descripcion']
        })

    if hipot_vals and taqui_vals:
        ocurr = min(len(hipot_vals), len(taqui_vals))
        prom = (sum(hipot_vals) / len(hipot_vals) + sum(taqui_vals) / len(taqui_vals)) / 2
        punt = min(100, int(prom / 100 * ocurr * 10))
        desc = "riesgo alto" if punt > 70 else "riesgo moderado"
        resultado.append({
            'condición': 'Choque',
            'ocurrencias': ocurr,
            'promedio_valor': f"{round(prom, 1)} mix",
            'puntaje': punt,
            'descripcion': desc
        })

    return jsonify(resultado)