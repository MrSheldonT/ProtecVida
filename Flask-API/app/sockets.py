from .extensions import socketio, db
from .models import Ubicacion, MiembroGrupo, ZonaSegura, TipoAlerta, Alerta, Cuenta
from .utils import detectar_cambio_estado
from flask_socketio import emit,join_room
from firebase_admin import messaging
from datetime import datetime, timedelta


@socketio.on('connect_user')
def handle_connect_user(data):
    cuenta_id = data.get("cuenta_id")
    if not cuenta_id:
        emit('error', {'message': 'cuenta_id es requerido'})
        return

    grupos = db.session.query(MiembroGrupo.grupo_id).filter_by(cuenta_id=cuenta_id).all()
    grupo_ids = [g.grupo_id for g in grupos]

    for grupo_id in grupo_ids:
        join_room(str(grupo_id))
    
    emit('user_connected', {'cuenta_id': cuenta_id, 'grupos': grupo_ids})


@socketio.on('ubicacion')
def handle_ubicacion(data):
    cuenta_id = data.get("cuenta_id")
    lat = data.get("lat")
    lon = data.get("lon")
    telefono_porcentaje = data.get("telefono_porcentaje")
    gatget_porcentaje = data.get("gatget_porcentaje")

    if not all([cuenta_id, lat, lon]):
        emit('error', {'message': 'cuenta_id, lat y lon son requeridos'})
        return

    try:
        ubicacion = db.session.query(Ubicacion).filter_by(cuenta_id=cuenta_id).first()
        lat_anterior = ubicacion.latitud if ubicacion else None
        lon_anterior = ubicacion.longitud if ubicacion else None

        now = datetime.utcnow()
        
        if ubicacion:
            ubicacion.latitud = lat
            ubicacion.longitud = lon
            ubicacion.ubicacion_ultima_actualizacion = now
            
            if telefono_porcentaje is not None:
                ubicacion.telefono_porcentaje = telefono_porcentaje
                ubicacion.telefono_ultima_actualizacion = now
                
            if gatget_porcentaje is not None:
                ubicacion.gatget_porcentaje = gatget_porcentaje
                ubicacion.gatget_ultima_actualizacion = now
        else:
            ubicacion = Ubicacion(
                cuenta_id=cuenta_id,
                latitud=lat,
                longitud=lon,
                ubicacion_ultima_actualizacion=now,
                telefono_porcentaje=telefono_porcentaje,
                telefono_ultima_actualizacion=now if telefono_porcentaje is not None else None,
                gatget_porcentaje=gatget_porcentaje,
                gatget_ultima_actualizacion=now if gatget_porcentaje is not None else None
            )
            db.session.add(ubicacion)

        db.session.commit()
        grupos_usuario = db.session.query(MiembroGrupo.grupo_id).filter_by(cuenta_id=cuenta_id).all()
        grupo_ids = [g.grupo_id for g in grupos_usuario]
        PRIORIDAD_ALERTA = {'Alta': 3, 'Media': 2, 'Baja': 1}

        for grupo_id in grupo_ids:
            tres_dias_atras = datetime.utcnow() - timedelta(hours=72)
            alertas = Alerta.query.filter(
                Alerta.cuenta_id == cuenta_id,
                Alerta.fecha >= tres_dias_atras
            ).all()

            alerta_data = None
            if alertas:
                # Encontrar la alerta con mayor prioridad
                alerta_principal = max(alertas, key=lambda a: PRIORIDAD_ALERTA.get(a.magnitud, 0))
                
                alerta_data = {
                    "tipo_alerta": alerta_principal.tipo_id,
                    "magnitud": alerta_principal.magnitud,
                    "fecha": alerta_principal.fecha.isoformat(),
                    "total_alertas": len(alertas)
                }

            emit('UBICACION_ACTUALIZADA', {
                'cuenta_id': cuenta_id,
                'lat': lat,
                'lon': lon,
                'telefono_porcentaje': telefono_porcentaje,
                'gatget_porcentaje': gatget_porcentaje,
                'telefono_ultima_actualizacion':ubicacion.telefono_ultima_actualizacion.strftime("%Y-%m-%d %H:%M:%S"),
                'gatget_ultima_actualizacion':ubicacion.gatget_ultima_actualizacion.strftime("%Y-%m-%d %H:%M:%S"),
                'ubicacion_ultima_actualizacion':ubicacion.ubicacion_ultima_actualizacion.strftime("%Y-%m-%d %H:%M:%S"),
                "alerta": alerta_data
            }, room=str(grupo_id))

        # Procesamiento de zonas seguras (mantenido igual)
        zonas_usuario = db.session.query(ZonaSegura).filter_by(cuenta_id=cuenta_id)
        grupos_usuario = db.session.query(MiembroGrupo.grupo_id).filter_by(cuenta_id=cuenta_id).distinct().all()
        grupo_ids = [g.grupo_id for g in grupos_usuario]

        miembros_grupo = db.session.query(MiembroGrupo.cuenta_id).filter(
            MiembroGrupo.grupo_id.in_(grupo_ids),
            MiembroGrupo.cuenta_id != cuenta_id
        ).distinct().all()
        miembros_ids = [m.cuenta_id for m in miembros_grupo]
        zonas_grupo = db.session.query(ZonaSegura).filter(ZonaSegura.cuenta_id.in_(miembros_ids))

        todas_zonas = zonas_usuario.union(zonas_grupo).all()

        if lat_anterior and lon_anterior:
            cuenta = db.session.query(Cuenta).filter_by(id=cuenta_id).first()
            nombre_usuario = cuenta.nombre if cuenta else "Desconocido"
            cambio = detectar_cambio_estado(lat, lon, lat_anterior, lon_anterior, todas_zonas)

            if cambio in ["salida", "entrada"]:
                mensaje = f"{nombre_usuario} {'salió de' if cambio == 'salida' else 'volvió a'} la zona segura"
                tipo_alerta_nombre = "Salida de zona segura" if cambio == "salida" else "Entrada zona segura"
                try:
                    tipo_alerta = TipoAlerta.query.filter_by(nombre=tipo_alerta_nombre).first()
                    if tipo_alerta:
                        nueva_alerta = Alerta(
                            cuenta_id=cuenta_id,
                            tipo_id=tipo_alerta.id,
                            atendida=False,
                            magnitud="Baja"
                        )
                        db.session.add(nueva_alerta)
                        db.session.commit()

                        emit("NOTIFICACION", {
                            "cuenta_id": cuenta_id,
                            "lat": lat,
                            "lon": lon,
                            "mensaje": mensaje,
                            "telefono_bateria": ubicacion.telefono_porcentaje,
                            "gatget_bateria": ubicacion.gatget_porcentaje
                        }, broadcast=True)

                        emit('ULTIMAS_ALERTAS', ultimas_alertas(), broadcast=True)

                        if cuenta and cuenta.fcm_token:
                            try:
                                message = messaging.Message(
                                    notification=messaging.Notification(
                                        title=mensaje,
                                        body=f"Ubicación: Lat {lat}, Lon {lon}",
                                    ),
                                    token=cuenta.fcm_token,
                                )
                                response = messaging.send(message)
                                print(f"Notificación enviada: {response}")
                            except Exception as fcm_error:
                                print(f"Error al enviar notificación FCM: {fcm_error}")
                        else:
                            print(f"Token FCM no disponible para cuenta_id={cuenta_id}")
                except Exception as alerta_error:
                    print(f"Error al guardar alerta: {alerta_error}")
                    emit("ERROR", "No se pudo guardar la alerta", broadcast=True)


        db.session.commit()

    except Exception as general_error:
        db.session.rollback()
        print(f"Error al procesar ubicación: {general_error}")
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
    emit('ULTIMAS_ALERTAS', alertas)

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

@socketio.on('obtener_ubicaciones_grupo')
def handle_obtener_ubicaciones_grupo(data):
    cuenta_id = data.get("cuenta_id")
    
    if not cuenta_id:
        emit("ERROR", {"mensaje": "Se requiere cuenta_id"})
        return

    try:
        PRIORIDAD_ALERTA = {'Alta': 3, 'Media': 2, 'Baja': 1}
        grupos_usuario = db.session.query(MiembroGrupo.grupo_id).filter_by(cuenta_id=cuenta_id).distinct().all()
        grupo_ids = [g.grupo_id for g in grupos_usuario]

        miembros_grupo = db.session.query(MiembroGrupo.cuenta_id).filter(
            MiembroGrupo.grupo_id.in_(grupo_ids),
        ).distinct().all()
        miembros_ids = [m.cuenta_id for m in miembros_grupo]

        ubicaciones_miembros = Ubicacion.query.filter(
            Ubicacion.cuenta_id.in_(miembros_ids))
            
        cuentas_miembros = {c.id: c for c in Cuenta.query.filter(Cuenta.id.in_(miembros_ids)).all()}
        
        ubicaciones_data = []
        for ubicacion in ubicaciones_miembros:
            cuenta = cuentas_miembros.get(ubicacion.cuenta_id)
            tres_dias_atras = datetime.utcnow() - timedelta(hours=72)
            alertas = Alerta.query.filter(
                Alerta.cuenta_id == ubicacion.cuenta_id,
                Alerta.fecha >= tres_dias_atras
            ).all()

            alerta_data = None
            if alertas:
                # Encontrar la alerta con mayor prioridad
                alerta_principal = max(alertas, key=lambda a: PRIORIDAD_ALERTA.get(a.magnitud, 0))
                
                alerta_data = {
                    "tipo_alerta": alerta_principal.tipo_id,
                    "magnitud": alerta_principal.magnitud,
                    "fecha": alerta_principal.fecha.isoformat(),
                    "total_alertas": len(alertas)
                }
            
            ubicaciones_data.append({
                "cuenta_id": ubicacion.cuenta_id,
                "nombre": cuenta.nombre if cuenta else "Desconocido",
                "lat": ubicacion.latitud,
                "lon": ubicacion.longitud,
                "telefono_porcentaje": ubicacion.telefono_porcentaje,
                "telefono_ultima_actualizacion": ubicacion.telefono_ultima_actualizacion.isoformat() if ubicacion.telefono_ultima_actualizacion else None,
                "ultima_actualizacion": ubicacion.ubicacion_ultima_actualizacion.isoformat() if ubicacion.ubicacion_ultima_actualizacion else None,
                "alerta": alerta_data
            })

            emit("UBICACIONES_GRUPO", {
            "cuenta_id": cuenta_id,
            "ubicaciones": ubicaciones_data
            })

    except Exception as e:
        print(f"Error al obtener ubicaciones de grupo: {str(e)}")
        emit("ERROR", {"mensaje": "Error al obtener ubicaciones de grupo"})