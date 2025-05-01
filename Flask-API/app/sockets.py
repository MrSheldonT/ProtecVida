from .extensions import socketio, db
from .models import Ubicacion, MiembroGrupo, ZonaSegura, TipoAlerta, Alerta, Cuenta
from .utils import detectar_cambio_estado
from flask_socketio import emit
from firebase_admin import messaging


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

        zonas_usuario = db.session.query(ZonaSegura).filter_by(cuenta_id=cuenta_id)

        grupos_usuario = db.session.query(MiembroGrupo.grupo_id).filter(
            MiembroGrupo.cuenta_id == cuenta_id
        ).distinct().all()  

        grupos_usuario_ids = [grupo.grupo_id for grupo in grupos_usuario]  
        miembros_grupo = db.session.query(MiembroGrupo.cuenta_id).filter(
            MiembroGrupo.grupo_id.in_(grupos_usuario_ids),
            MiembroGrupo.cuenta_id != cuenta_id
        ).distinct().all() 

        miembros_grupo_ids = [miembro.cuenta_id for miembro in miembros_grupo]
        zonas_grupo = db.session.query(ZonaSegura).filter(
            ZonaSegura.cuenta_id.in_(miembros_grupo_ids)
        )

        todas_zonas = zonas_usuario.union(zonas_grupo).all()

        if lat_anterior and lon_anterior:
            cuenta = db.session.query(Cuenta).filter_by(id=cuenta_id).first()
            nombre_usuario = cuenta.nombre if cuenta else "Desconocido"
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
                        emit("NOTIFICACION", {
                        "cuenta_id": cuenta_id,
                        "lat": lat,
                        "lon": lon,
                        "mensaje": f"{nombre_usuario} salió de la zona segura"
                          }, broadcast=True)
                    
                        alertas = ultimas_alertas()
                        emit('ULTIMAS_ALERTAS', alertas, broadcast=True)

                    try:
                        token_fcm = cuenta.fcm_token 

                        if token_fcm:
                            # Crear el mensaje FCM
                            message = messaging.Message(
                                notification=messaging.Notification(
                                    title=f"{nombre_usuario} salió de la zona segura",
                                    body=f"Ubicación: Lat {lat}, Lon {lon}",
                                ),
                                token=token_fcm,
                            )
                            # Enviar la notificación
                            response = messaging.send(message)
                            print(f"Notificación enviada: {response}")
                        else:
                            print(f"Token FCM no disponible para el usuario {cuenta_id}")

                    except Exception as e:
                        print(f"Error al enviar notificación FCM: {e}")
                  
                 

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
                        emit("NOTIFICACION", {
                        "cuenta_id": cuenta_id,
                        "lat": lat,
                        "lon": lon,
                        "mensaje": f"{nombre_usuario} volvió a la zona segura"
                    }, broadcast=True)

                    alertas = ultimas_alertas()
                    emit('ULTIMAS_ALERTAS', alertas, broadcast=True)
                    try:
                        token_fcm = cuenta.fcm_token 

                        if token_fcm:
                            # Crear el mensaje FCM
                            message = messaging.Message(
                                notification=messaging.Notification(
                                    title=f"{nombre_usuario} volvió a la zona segura",
                                    body=f"Ubicación: Lat {lat}, Lon {lon}",
                                ),
                                token=token_fcm,
                            )
                            # Enviar la notificación
                            response = messaging.send(message)
                            print(f"Notificación enviada: {response}")
                        else:
                            print(f"Token FCM no disponible para el usuario {cuenta_id}")

                    except Exception as e:
                        print(f"Error al enviar notificación FCM: {e}")

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


@socketio.on('pedir_alertas')
def handle_pedir_alertas():
    alertas = ultimas_alertas()
    emit('ULTIMAS_ALERTAS', alertas, broadcast=True)

def ultimas_alertas():
    alertas = Alerta.query.order_by(Alerta.fecha.desc()).limit(10).all()
    resultado = []

    for alerta in alertas:
        tipo_alerta = TipoAlerta.query.get(alerta.tipo_id)
        cuenta = Cuenta.query.get(alerta.cuenta_id)

        resultado.append({
            'alerta_id': alerta.id,
            'cuenta_id': alerta.cuenta_id,
            'tipo_id': alerta.tipo_id,
            'tipo_alerta': tipo_alerta.nombre if tipo_alerta else "Desconocido",
            'fecha': alerta.fecha.strftime("%Y-%m-%d %H:%M:%S"),
            'atendida': alerta.atendida,
            'magnitud': alerta.magnitud,
            'usuario': {
                'nombre': cuenta.nombre if cuenta else "Desconocido",
                'correo_electronico': cuenta.correo_electronico if cuenta else "N/A"
            }
        })

    return resultado
