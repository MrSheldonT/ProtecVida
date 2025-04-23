from .extensions import socketio, db
from .models import Ubicacion, MiembroGrupo, ZonaSegura, TipoAlerta, Alerta
from .utils import detectar_cambio_estado
from flask_socketio import emit

@socketio.on('ubicacion')
def handle_ubicacion(data):
    cuenta_id = data.get("cuenta_id")
    lat = data.get("lat")
    lon = data.get("lon")

    if cuenta_id is None or lat is None or lon is None:
        return

    try:
        lat_anterior = None
        lon_anterior = None

        # Buscar la ubicación anterior del usuario
        ubicacion = db.session.query(Ubicacion).filter_by(cuenta_id=cuenta_id).first()
        if ubicacion:
            lat_anterior = ubicacion.latitud
            lon_anterior = ubicacion.longitud
            ubicacion.latitud = lat
            ubicacion.longitud = lon
        else:
            # Si no existe, crear la nueva ubicación
            ubicacion = Ubicacion(cuenta_id=cuenta_id, latitud=lat, longitud=lon)
            db.session.add(ubicacion)

        db.session.commit()

        # Cargar las zonas propias del usuario
        zonas_usuario = db.session.query(ZonaSegura).filter_by(cuenta_id=cuenta_id)

        # Obtener los grupos a los que pertenece el usuario
        grupos_usuario = db.session.query(MiembroGrupo.grupo_id).filter(
            MiembroGrupo.cuenta_id == cuenta_id
        ).distinct().all()  # Obtener los IDs de los grupos del usuario

        grupos_usuario_ids = [grupo.grupo_id for grupo in grupos_usuario]  # Extraemos solo los IDs

        # Obtener los miembros de los grupos a los que pertenece el usuario
        miembros_grupo = db.session.query(MiembroGrupo.cuenta_id).filter(
            MiembroGrupo.grupo_id.in_(grupos_usuario_ids),
            MiembroGrupo.cuenta_id != cuenta_id
        ).distinct().all()  # Obtener los IDs de los miembros

        miembros_grupo_ids = [miembro.cuenta_id for miembro in miembros_grupo]  # Extraemos solo los IDs de los miembros

        # Obtener zonas de los grupos a los que pertenece el usuario
        zonas_grupo = db.session.query(ZonaSegura).filter(
            ZonaSegura.cuenta_id.in_(miembros_grupo_ids)
        )

        # Unir todas las zonas (propias del usuario y de los grupos)
        todas_zonas = zonas_usuario.union(zonas_grupo).all()

        # Comprobar si la ubicación anterior existe y si el usuario está fuera de la zona segura
        if lat_anterior and lon_anterior:
            cambio = detectar_cambio_estado(lat, lon, lat_anterior, lon_anterior, todas_zonas)
            if cambio == "salida":
                try:
                    alerta_zona_segura = TipoAlerta.query.filter_by(nombre="Salida de zona segura").first()
                    if alerta_zona_segura:
                        new_alerta = Alerta(
                            cuenta_id=cuenta_id,
                            tipo_id=alerta_zona_segura.id,
                            atendida=False,
                            magnitud="Baja"
                        )
                        db.session.add(new_alerta)
                        db.session.commit()

                    emit("ALERTA_SALIDA_ZONA", {
                        "cuenta_id": cuenta_id,
                        "lat": lat,
                        "lon": lon,
                        "mensaje": "Salió de zona segura"
                    }, broadcast=True)

                except Exception as e:
                    print(f"Error al guardar alerta: {e}")
                    emit("ERROR", "No se pudo guardar la alerta", broadcast=True)

            elif cambio == "entrada":
                try:
                    alerta_zona_segura = TipoAlerta.query.filter_by(nombre="Entrada zona segura").first()
                    if alerta_zona_segura:
                        new_alerta = Alerta(
                            cuenta_id=cuenta_id,
                            tipo_id=alerta_zona_segura.id,
                            atendida=False,
                            magnitud="Baja"
                        )
                        db.session.add(new_alerta)
                        db.session.commit()

                    emit("ALERTA_ENTRADA_ZONA", {
                        "cuenta_id": cuenta_id,
                        "lat": lat,
                        "lon": lon,
                        "mensaje": "Volvió a la zona segura"
                    }, broadcast=True)

                except Exception as e:
                    print(f"Error al guardar alerta: {e}")
                    emit("ERROR", "No se pudo guardar la alerta", broadcast=True)

            
        # Emitir la nueva ubicación
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