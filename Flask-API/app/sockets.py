from .extensions import socketio, db
from .models import Ubicacion
from flask_socketio import emit


@socketio.on('ubicacion')
def handle_ubicacion(data):
    cuenta_id = data.get("cuenta_id")
    lat = data.get("lat")
    lon = data.get("lon")

    if cuenta_id is None or lat is None or lon is None:
        return

    try:
        ubicacion = db.session.query(Ubicacion).filter_by(cuenta_id=cuenta_id).first()
        print("xd")
        if ubicacion:
            print("entra")
            ubicacion.latitud = lat
            ubicacion.longitud = lon
        else:
            ubicacion = Ubicacion(cuenta_id=cuenta_id, lat=lat, lon=lon)
            db.session.add(ubicacion)

        db.session.commit()

        print(f"Ubicación recibida para cuenta {cuenta_id}: Lat: {lat}, Lon: {lon}")
        print(ubicacion.to_json())
        emit("UBICACION", data, broadcast=True)

    except Exception as e:
        print(f"Error al procesar ubicación: {str(e)}")
        emit("ERROR", "Data no transmitida", broadcast=True)


@socketio.on('solicitar_ubicacion')
def handle_solicitar_ubicacion(data):
    cuenta_id = data.get("cuenta_id")

    if cuenta_id is None:
        emit("ERROR", "ID de cuenta no proporcionado")
        return

    try:
        ubicacion = Ubicacion.query.filter_by(cuenta_id=cuenta_id).order_by(Ubicacion.id.desc()).first()

        if ubicacion:
            emit("UBICACION", {
                "cuenta_id": ubicacion.cuenta_id,
                "lat": ubicacion.latitud,
                "lon": ubicacion.longitud
            })
        else:
            emit("ERROR", f"No se encontró la ubicación para la cuenta {cuenta_id}")
    except Exception as e:
        emit("ERROR", f"Error al obtener la ubicación: {str(e)}")