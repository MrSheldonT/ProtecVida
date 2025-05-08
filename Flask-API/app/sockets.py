from .extensions import socketio, db
from .models import Ubicacion, MiembroGrupo, ZonaSegura, TipoAlerta, Alerta, Cuenta,Dispositivo
from .utils import detectar_cambio_estado
from flask_socketio import emit
from firebase_admin import messaging


@socketio.on('ubicacion')
def handle_ubicacion(data):
    cuenta_id = data.get("cuenta_id")
    lat = data.get("lat")
    lon = data.get("lon")
    dispositivos = data.get("dispositivos", [])

    if not all([cuenta_id, lat, lon]):
        return

    try:
        ubicacion = db.session.query(Ubicacion).filter_by(cuenta_id=cuenta_id).first()
        lat_anterior = ubicacion.latitud if ubicacion else None
        lon_anterior = ubicacion.longitud if ubicacion else None

        if ubicacion:
            ubicacion.latitud = lat
            ubicacion.longitud = lon
        else:
            ubicacion = Ubicacion(cuenta_id=cuenta_id, latitud=lat, longitud=lon)
            db.session.add(ubicacion)

        for dispositivo_data in dispositivos:
            direccion_mac = dispositivo_data.get("direccion_mac")
            if not direccion_mac:
                continue

            dispositivo = db.session.query(Dispositivo).filter_by(direccion_mac=direccion_mac).first()
            if dispositivo:
                dispositivo.porcentaje = dispositivo_data.get("porcentaje")
                dispositivo.nombre = dispositivo_data.get("nombre")
                dispositivo.tipo = dispositivo_data.get("tipo")
                dispositivo.ultima_act = db.func.current_timestamp()
            else:
                nuevo_disp = Dispositivo(
                    cuenta_id=cuenta_id,
                    direccion_mac=direccion_mac,
                    porcentaje=dispositivo_data.get("porcentaje"),
                    nombre=dispositivo_data.get("nombre"),
                    tipo=dispositivo_data.get("tipo")
                )
                db.session.add(nuevo_disp)

        db.session.commit()

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
                            "mensaje": mensaje
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

        emit("UBICACION", data, broadcast=True)

    except Exception as general_error:
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
