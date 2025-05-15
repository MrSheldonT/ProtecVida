from flask import Blueprint, jsonify, request
from .utils import token_required
from .extensions import db
from .models import Cuenta, TipoSignoVital, SignoVital
from sqlalchemy import desc
from datetime import datetime, timedelta
analisis_datos = Blueprint('analisis_datos', __name__)


def analyze_hypertension(pas_vals, pad_vals):
    anomalies = [v for v in pas_vals if v >= 130] + [v for v in pad_vals if v >= 80]
    count = len(anomalies)
    total = len(pas_vals) + len(pad_vals)
    porcentaje = (count / total) * 100 if total else 0
    promedio = (sum(anomalies) / count) if count else 0

    nivel = "normal"
    severity_num = 0
    if count > 0:
        if any(v > 180 for v in pas_vals) and any(v > 120 for v in pad_vals):
            nivel = "grave"
            severity_num = 3
        elif any(v >= 140 for v in pas_vals) or any(v >= 90 for v in pad_vals):
            nivel = "grave"
            severity_num = 3
        elif any(v >= 130 for v in pas_vals) or any(v >= 80 for v in pad_vals):
            nivel = "moderada"
            severity_num = 2
        elif any(120 <= v < 130 for v in pas_vals):
            nivel = "leve"
            severity_num = 1

    puntaje = severity_num * 20 + porcentaje
    puntaje = round(puntaje)
    return nivel, promedio, porcentaje, min(max(puntaje, 1), 100)

def analyze_hypotension(pas_vals, pad_vals):
    anomalies = [v for v in pas_vals if v < 90] + [v for v in pad_vals if v < 60]
    count = len(anomalies)
    total = len(pas_vals) + len(pad_vals)
    porcentaje = (count / total) * 100 if total else 0
    promedio = (sum(anomalies) / count) if count else 0

    nivel = "normal"
    severity_num = 0
    if count > 0:
        if any(v < 80 for v in pas_vals) or any(v < 50 for v in pad_vals):
            nivel = "grave"
            severity_num = 3
        else:
            nivel = "moderada"
            severity_num = 2

    puntaje = severity_num * 20 + porcentaje
    puntaje = round(puntaje)
    return nivel, promedio, porcentaje, min(max(puntaje, 1), 100)

def analyze_tachycardia(fc_vals):
    anomalies = [v for v in fc_vals if v > 100]
    count = len(anomalies)
    total = len(fc_vals)
    porcentaje = (count / total) * 100 if total else 0
    promedio = (sum(anomalies) / count) if count else 0

    nivel = "normal"
    severity_num = 0
    if count > 0:
        if any(v > 140 for v in anomalies):
            nivel = "grave"
            severity_num = 3
        elif any(v >= 121 for v in anomalies):
            nivel = "moderada"
            severity_num = 2
        else:
            nivel = "leve"
            severity_num = 1

    puntaje = severity_num * 20 + porcentaje
    puntaje = round(puntaje)
    return nivel, promedio, porcentaje, min(max(puntaje, 1), 100)

def analyze_bradycardia(fc_vals):
    anomalies = [v for v in fc_vals if v < 60]
    count = len(anomalies)
    total = len(fc_vals)
    porcentaje = (count / total) * 100 if total else 0
    promedio = (sum(anomalies) / count) if count else 0

    nivel = "normal"
    severity_num = 0
    if count > 0:
        if any(v < 40 for v in anomalies):
            nivel = "grave"
            severity_num = 3
        elif any(v <= 49 for v in anomalies):
            nivel = "moderada"
            severity_num = 2
        else:
            nivel = "leve"
            severity_num = 1

    puntaje = severity_num * 20 + porcentaje
    puntaje = round(puntaje)
    return nivel, promedio, porcentaje, min(max(puntaje, 1), 100)

def analyze_hypoxemia(spo2_vals):
    anomalies = [v for v in spo2_vals if v < 90]
    count = len(anomalies)
    total = len(spo2_vals)
    porcentaje = (count / total) * 100 if total else 0
    promedio = (sum(anomalies) / count) if count else 0

    nivel = "normal"
    severity_num = 0
    if count > 0:
        if any(v < 80 for v in anomalies):
            nivel = "grave"
            severity_num = 3
        elif any(v <= 84 for v in anomalies):
            nivel = "moderada"
            severity_num = 2
        else:
            nivel = "leve"
            severity_num = 1

    puntaje = severity_num * 20 + porcentaje
    puntaje = round(puntaje)
    return nivel, promedio, porcentaje, min(max(puntaje, 1), 100)

@analisis_datos.route('/riesgo', methods=['GET'])
def riesgo():
    cuenta_id = request.args.get('cuenta_id', type=int)
    if cuenta_id is None:
        return jsonify({'error': 'Falta el parámetro cuenta_id'}), 400

    # Obtener los datos de la cuenta
    cuenta = Cuenta.query.get(cuenta_id)
    if not cuenta:
        return jsonify({'error': 'Cuenta no encontrada'}), 404

    edad = None
    if cuenta.fecha_nacimiento:
        hoy = datetime.now()
        edad = hoy.year - cuenta.fecha_nacimiento.year - \
               ((hoy.month, hoy.day) < (cuenta.fecha_nacimiento.month, cuenta.fecha_nacimiento.day))

    peso = cuenta.peso
    altura = cuenta.altura
    sexo = cuenta.sexo

    ahora = datetime.now()
    hace_24h = ahora - timedelta(days=1)

    # Obtener datos de signos vitales
    datos_pas = SignoVital.query.filter(
        SignoVital.cuenta_id == cuenta_id,
        SignoVital.tipo_id == 1,
        SignoVital.fecha >= hace_24h
    ).all()
    datos_pad = SignoVital.query.filter(
        SignoVital.cuenta_id == cuenta_id,
        SignoVital.tipo_id == 2,
        SignoVital.fecha >= hace_24h
    ).all()
    datos_fc = SignoVital.query.filter(
        SignoVital.cuenta_id == cuenta_id,
        SignoVital.tipo_id == 3,
        SignoVital.fecha >= hace_24h
    ).all()
    datos_spo2 = SignoVital.query.filter(
        SignoVital.cuenta_id == cuenta_id,
        SignoVital.tipo_id == 4,
        SignoVital.fecha >= hace_24h
    ).all()

    pas_vals = [sv.valor_numerico_1 for sv in datos_pas]
    pad_vals = [sv.valor_numerico_1 for sv in datos_pad]
    fc_vals = [sv.valor_numerico_1 for sv in datos_fc]
    spo2_vals = [sv.valor_numerico_1 for sv in datos_spo2]

    nivel_ht, prom_ht, pct_ht, score_ht = analyze_hypertension(pas_vals, pad_vals)
    nivel_hipo, prom_hipo, pct_hipo, score_hipo = analyze_hypotension(pas_vals, pad_vals)
    nivel_taq, prom_taq, pct_taq, score_taq = analyze_tachycardia(fc_vals)
    nivel_bra, prom_bra, pct_bra, score_bra = analyze_bradycardia(fc_vals)
    nivel_hypox, prom_hypox, pct_hypox, score_hypox = analyze_hypoxemia(spo2_vals)

    if edad is not None:
        if edad > 60:
            # Incrementar severidad para adultos mayores
            score_ht += 5
            score_hipo += 5
            score_taq += 5
            score_bra += 5
            score_hypox += 5

    if peso and altura:
        imc = peso / ((altura / 100) ** 2)
        if imc >= 30:
            score_ht += 10
            score_taq += 5
        elif imc < 18.5:
            score_hipo += 10
            score_bra += 5

    resultado = [
        {
            "condicion": "Hipertensión",
            "descripcion": "La hipertensión arterial es la elevación sostenida de la presión arterial (PAS ≥130 mmHg o PAD ≥80 mmHg).",
            "puntaje": score_ht,
            "nivel_severidad": nivel_ht,
            "promedio_anomalo": f"{prom_ht:.1f} mmHg",
            "porcentaje_afectado": f"{pct_ht:.1f}%",
            "comentario_clinico": f"Se detectaron lecturas con promedio de {prom_ht:.1f} mmHg, severidad {nivel_ht}."
        },
        {
            "condicion": "Hipotensión",
            "descripcion": "La hipotensión arterial es la disminución de la presión arterial (PAS <90 mmHg o PAD <60 mmHg).",
            "puntaje": score_hipo,
            "nivel_severidad": nivel_hipo,
            "promedio_anomalo": f"{prom_hipo:.1f} mmHg",
            "porcentaje_afectado": f"{pct_hipo:.1f}%",
            "comentario_clinico": f"Se detectaron lecturas con promedio de {prom_hipo:.1f} mmHg, severidad {nivel_hipo}."
        },
        {
            "condicion": "Taquicardia",
            "descripcion": "La taquicardia es la elevación del ritmo cardíaco (>100 latidos por minuto).",
            "puntaje": score_taq,
            "nivel_severidad": nivel_taq,
            "promedio_anomalo": f"{prom_taq:.1f} lpm",
            "porcentaje_afectado": f"{pct_taq:.1f}%",
            "comentario_clinico": f"Se detectaron lecturas con promedio de {prom_taq:.1f} lpm, severidad {nivel_taq}."
        },
        {
            "condicion": "Bradicardia",
            "descripcion": "La bradicardia es la disminución del ritmo cardíaco (<60 latidos por minuto).",
            "puntaje": score_bra,
            "nivel_severidad": nivel_bra,
            "promedio_anomalo": f"{prom_bra:.1f} lpm",
            "porcentaje_afectado": f"{pct_bra:.1f}%",
            "comentario_clinico": f"Se detectaron lecturas con promedio de {prom_bra:.1f} lpm, severidad {nivel_bra}."
        },
        {
            "condicion": "Hipoxemia",
            "descripcion": "La hipoxemia es la disminución de la saturación de oxígeno (<90%).",
            "puntaje": score_hypox,
            "nivel_severidad": nivel_hypox,
            "promedio_anomalo": f"{prom_hypox:.1f}%",
            "porcentaje_afectado": f"{pct_hypox:.1f}%",
            "comentario_clinico": f"Se detectaron lecturas con promedio de {prom_hypox:.1f}%, severidad {nivel_hypox}."
        },
    ]

    return jsonify(resultado)