from .extensions import socketio, db
from .models import Ubicacion, MiembroGrupo, ZonaSegura
from .utils import detectar_salida_zona
from flask_socketio import emit

@socketio.on('ubicacion')
def handle_ubicacion(data):
    cuenta_id = data.get("cuenta_id")
    lat = data.get("lat")
    lon = data.get("lon")
    print("yaaaaa")

    if cuenta_id is None or lat is None or lon is None:
        return

    try:
        lat_anterior = None
        lon_anterior = None

        ubicacion = db.session.query(Ubicacion).filter_by(cuenta_id=cuenta_id).first()
        if ubicacion:
            lat_anterior = ubicacion.latitud
            lon_anterior = ubicacion.longitud
            ubicacion.latitud = lat
            ubicacion.longitud = lon
        else:
            ubicacion = Ubicacion(cuenta_id=cuenta_id, latitud=lat, longitud=lon)
            db.session.add(ubicacion)

        db.session.commit()

        # Cargar zonas propias y de grupo
        zonas_usuario = db.session.query(ZonaSegura).filter_by(cuenta_id=cuenta_id)

        grupos_usuario = db.session.query(MiembroGrupo.grupo_id).filter(
            MiembroGrupo.cuenta_id == cuenta_id
        ).subquery()

        miembros_grupo = db.session.query(MiembroGrupo.cuenta_id).filter(
            MiembroGrupo.grupo_id.in_(grupos_usuario),
            MiembroGrupo.cuenta_id != cuenta_id
        ).distinct().subquery()

        zonas_grupo = db.session.query(ZonaSegura).filter(
            ZonaSegura.cuenta_id.in_(miembros_grupo)
        )

        todas_zonas = zonas_usuario.union(zonas_grupo).all()

        if lat_anterior and lon_anterior:
            if detectar_salida_zona(lat, lon, lat_anterior, lon_anterior, todas_zonas):
                print("jaja")
                emit("ALERTA_SALIDA_ZONA", {
                    "cuenta_id": cuenta_id,
                    "lat": lat,
                    "lon": lon,
                    "mensaje": "Salió de zona segura"
                }, broadcast=True)

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