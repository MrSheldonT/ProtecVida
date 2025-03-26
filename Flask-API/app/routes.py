from flask import Blueprint, jsonify, request
from .models import Cuenta, Condicion, CuentaCondicion, Grupo, MiembroGrupo, ZonaSegura, Alerta, TipoAlerta, SignoVital
from .extensions import db
from .utils import check_password, hash_password, create_token_jwt, valid_password, valid_email, token_required

cuenta = Blueprint('cuenta', __name__)
grupo = Blueprint('grupo', __name__)
zona_segura = Blueprint('zona_segura', __name__)
@cuenta.route('/registrarse', methods=['POST'])
def crear_cuenta():

    user_data = request.get_json()
    nombre = str(user_data.get('nombre', '')).strip()
    correo = str(user_data.get('correo_electronico', '')).strip()
    contrasenia = str(user_data.get('contrasenia', '')).strip()

    if not nombre or not correo or not contrasenia:
        return jsonify({'error': 'Faltan parámetros requeridos: nombre, correo_electronico, contrasenia'}), 400

    if Cuenta.query.filter_by(correo_electronico=correo).first():
        return jsonify({'error': 'El correo ya está registrado'}), 409

    is_valid_password, message = valid_password(contrasenia)

    if not valid_email(correo) or not is_valid_password:
        return jsonify({'error': 'Correo o contraseña inválidos ({message})'}), 409

    try:
        nueva_cuenta = Cuenta(
            nombre=user_data['nombre'],
            correo_electronico=correo,
            hash_contraseña=hash_password(contrasenia),
        )

        db.session.add(nueva_cuenta)
        db.session.commit()
        return jsonify({'mensaje': 'Cuenta creada exitosamente', 'data': nueva_cuenta.to_json()}), 201
    except Exception as e:
        return jsonify({'error': f'Error: {e}'}), 500

@cuenta.route('/acceder', methods=['POST'])
def login_cuenta():

    user_data = request.get_json()
    correo = str(user_data.get('correo_electronico', '')).strip()
    contrasenia = str(user_data.get('contrasenia', '')).strip()

    if not correo or not contrasenia:
        return jsonify({'error': 'El correo y la contraseña son obligatorios'}), 400

    try:
        user = Cuenta.query.filter_by(correo_electronico=correo).first()

        if user is None:
            return jsonify({'error': 'No se ha encontrado la cuenta'}), 404

        if check_password(contrasenia, user.hash_contraseña):
            return jsonify({'mensaje': 'Logueado correctamente', 'jwt_token': create_token_jwt(user.id)}), 200
        else:
            return jsonify({'error': 'Contraseña incorrecta'}), 401

    except Exception as e:
        return jsonify({'error': f'Error: {e}'}), 500

@cuenta.route('/conseguir_cuenta', methods=['GET'])
@token_required
def conseguir_cuenta():

    try:
        current_account = Cuenta.query.filter_by(id=request.user_id).first(), 200
        if current_account is None:
            return jsonify({'error': 'No se ha encontrado cuenta'}), 404
        return jsonify({'mensaje': 'Información de la cuenta recuperada', 'data': current_account.to_json()}), 200
    except Exception as e:
        return jsonify({'error': f'Error: {e}'}), 500


@cuenta.route('/editar_perfil', methods=['PUT'])
@token_required
def editar_cuenta():

    user_data = request.get_json()
    nombre = str(user_data.get('nombre', '')).strip()
    correo = str(user_data.get('correo_electronico', '')).strip()
    contrasenia = str(user_data.get('contrasenia', '')).strip()
    sexo = str(user_data.get('sexo', '')).strip()
    fechaNacimiento = user_data.get('fechaNacimiento', '')

    try:
        peso = float(user_data.get('peso', 0))
    except ValueError:
        return jsonify({'error': 'El peso debe ser un número válido'}), 400

    try:
        altura = float(user_data.get('altura', 0))
    except ValueError:
        return jsonify({'error': 'La altura debe ser un número válido'}), 400

    try:
        from datetime import datetime
        if fechaNacimiento:
            fechaNacimiento = datetime.strptime(fechaNacimiento, '%Y-%m-%d')
        else:
            fechaNacimiento = None
    except ValueError:
        return jsonify({'error': 'La fecha de nacimiento debe estar en formato YYYY-MM-DD'}), 400

    try:
        user = Cuenta.query.filter_by(id=request.user_id).first()

        if not user:
            return  jsonify({'error': 'No se ha encontrado la cuenta'}), 404
        if nombre:
            user.nombre = nombre
        if correo:
            user.correo_electronico = correo
        if contrasenia:
            user.hash_contraseña = hash_password(contrasenia)
        if peso:
            user.peso = peso
        if altura:
            user.altura = altura
        if sexo and (sexo == 'F' or sexo == 'M'):
            user.sexo = sexo
        if fechaNacimiento:
            user.fecha_nacimiento = fechaNacimiento

        db.session.commit()

        return jsonify({'mensaje': f'Cuenta {user.nombre}({user.correo_electronico}) editada exitosamente', 'data': user.to_json()}), 200
    except Exception as e:
        return jsonify({'error': f'Error: {e}'}), 500

@grupo.route('/crear_grupo', methods=['POST'])
@token_required
def crear_grupo():

    group_data = request.get_json()
    nombre_grupo = str(group_data.get('nombre_grupo', '')).strip()

    if not nombre_grupo:
        return jsonify({'error': 'Error, no se ha ingresado el nombre del grupo'}), 400
    try:
        new_group = Grupo(
            nombre=nombre_grupo
        )
        db.session.add(new_group)
        db.session.commit()

        add_miembro_grupo = MiembroGrupo(
            cuenta_id = request.user_id,
            grupo_id = new_group.id,
            es_administrador = True
        )

        db.session.add(add_miembro_grupo)
        db.session.commit()

        return  jsonify({'mensaje': f'Grupo {new_group.nombre} creado exitosamente'}), 201

    except Exception as e:
        return jsonify({'error': f'Error: {e}'}), 500


@grupo.route('/agregar_miembro', methods=['POST'])
@token_required
def agregar_miembro():

    user_data = request.get_json()
    correo = str(user_data.get('correo_electronico', '')).strip()
    grupo_id = user_data.get('grupo_id', '')

    if not correo:
        return  jsonify({'error': 'Error, no se ha ingresado el correo del miembro a ingresar'}), 400

    if not grupo_id:
        return jsonify({'error': 'Error, no se ha ingresado el grupo'}), 400
    try:
        new_member = Cuenta.query.filter_by(correo_electronico=correo).first()
        relacion_miembro = MiembroGrupo.query.filter_by(grupo_id=grupo_id, cuenta_id=new_member.id).first()

        if new_member is None:
            return jsonify({'error': 'El usuario no se ha encontrado'}), 404
        if relacion_miembro:
            return jsonify({'error': 'El usuario ya se encuentra en este grupo'}), 409

        grupo_miembro = MiembroGrupo(
            cuenta_id = new_member.id,
            grupo_id = grupo_id,
        )

        db.session.add(grupo_miembro)
        db.session.commit()

        return jsonify({'mensaje': f'Usuario {new_member.nombre} agregado al grupo {grupo_miembro.grupo_id}'}), 200
    except Exception as e:
        return jsonify({'error': f'Error: {e}'}), 500

@grupo.route('/eliminar_miembro', methods=['DELETE'])
@token_required
def eliminar_miembro():

    group_data = request.get_json()
    user_id = int(group_data.get('user_id', 0))
    grupo_id = int(group_data.get('grupo_id', 0))

    if not user_id:
        return jsonify({'error': 'No se ha ingresado el usuario del miembro ha eliminar'}), 400

    if not grupo_id:
        return jsonify({'error': 'No se ha ingresado el grupo'}), 400

    try:
        user_admin = MiembroGrupo.query.filter_by(cuenta_id = request.user_id, grupo_id = grupo_id).first()
        user_delete = MiembroGrupo.query.filter_by(cuenta_id = user_id, grupo_id = grupo_id).first()

        if not user_delete:
            return jsonify({'error': 'Error, este usuario no se encuentra en el grupo'}), 404

        if not user_admin:
            return jsonify({'error': 'Error, no estás en este grupo'}), 404

        if user_admin.cuenta_id == user_delete.cuenta_id:
            return jsonify({'error': 'No puedes eliminar tu propia cuenta desde esta operación'})

        if not user_admin.es_administrador:
            return jsonify({'error': 'Error, usted no es administrador de este grupo'}), 403

        if user_delete.es_administrador:
            return jsonify({'error': 'Error, no se puede eliminar a otro administrador'}), 403

        db.session.delete(user_delete)
        db.session.commit()
        return  jsonify({'mensaje': f'Se ha eliminado al usuario {user_delete.cuenta_id} exitosamente'}), 200
    except Exception as e:
        return jsonify({'error': f'Error: {e}'}), 500

@grupo.route('/salir_grupo', methods=['DELETE'])
@token_required
def salir_grupo():

    group_data = request.get_json()
    grupo_id = group_data.get('grupo_id')

    if not grupo_id:
        return jsonify({'error': 'Error, no has ingresado el ID del grupo'}), 400

    try:
        miembro = MiembroGrupo.query.filter_by(cuenta_id = request.user_id, grupo_id=grupo_id).first()

        if not miembro:
            return jsonify({'error': 'Error, no te encuentras en el grupo'}), 404

        if miembro.es_administrador:
            administradores = MiembroGrupo.query.filter_by(grupo_id=grupo_id, es_administrador=True).all()

            if len(administradores) == 1:
                otro_miembro = MiembroGrupo.query.filter_by(grupo_id=grupo_id, es_administrador=False).first()
                if otro_miembro:
                    otro_miembro.es_administrador = True
                else:
                    Grupo.query.filter_by(id=grupo_id).delete()

        db.session.delete(miembro)
        db.session.commit()
        return jsonify({'mensaje':'Se ha salido del grupo exitosamente'}), 200
    except Exception as e:
        return jsonify({'error': f'Error: {e}'}), 500

@grupo.route('/conseguir_grupo', methods=['GET'])
@token_required
def listar_grupos():
    try:
        grupos_miembro = db.session.query(Grupo, MiembroGrupo).join(MiembroGrupo).filter(
            MiembroGrupo.cuenta_id == request.user_id
        ).all()

        if not grupos_miembro:
            return jsonify({'mensaje': 'No cuenta con grupos', 'data': []}), 200

        group_data = []
        for grupo, miembro_grupo in grupos_miembro:
            grupo_data = grupo.to_json()
            miembro_grupo_data = miembro_grupo.to_json()
            grupo_data['es_administrador'] = miembro_grupo_data.get('es_administrador',False)
            group_data.append(grupo_data)

        return jsonify({'mensaje': 'Grupos listados con éxito', 'data': group_data}), 200

    except Exception as e:
        return jsonify({'error': f'Error: {e}'}), 500


@grupo.route('/conseguir_miembros_grupo/<int:grupo_id>', methods=['GET'])
@token_required
def listar_miembros_grupo(grupo_id):

    if not grupo_id:
        return  jsonify({'error': 'Error, no se ingresó un grupo'}), 400

    try:
        grupo = MiembroGrupo.query.filter_by(grupo_id=grupo_id).first()
        if not grupo:
            return jsonify({'error': 'Error, no pertenece a este grupo'}), 403

        grupos_miembro = db.session.query(Grupo, MiembroGrupo, Cuenta).select_from(Grupo).join(MiembroGrupo).join(
            Cuenta).filter(
            Grupo.id == grupo_id
        ).all()

        group_data = []
        for grupo, miembro_grupo, cuenta in grupos_miembro:
            grupo_data = grupo.to_json()
            miembro_grupo_data = miembro_grupo.to_json()

            grupo_data['es_administrador'] = miembro_grupo_data.get('es_administrador', False)
            grupo_data['cuenta'] = cuenta.to_json()

            group_data.append(grupo_data)

        return jsonify({'mensaje':'Miembros del grupo listados con éxito', 'data': group_data}), 200

    except Exception as e:
        return jsonify({'error': f'Error: {e}'}), 500

@zona_segura.route('/crear_zona_segura', methods=['POST'])
@token_required
def crear_zona_segura():
    safe_area_data = request.get_json()
    nombre = str(safe_area_data.get('nombre', '')).strip()

    try:
        latitud = float(safe_area_data.get('latitud'))
        if not (-90 <= latitud <= 90):
            return jsonify({'error': 'Latitud fuera de rango (-90 a 90)'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Latitud inválida'}), 400

    try:
        longitud = float(safe_area_data.get('longitud'))
        if not (-180 <= longitud <= 180):
            return jsonify({'error': 'Longitud fuera de rango (-180 a 180)'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Longitud inválida'}), 400

    try:
        radio = float(safe_area_data.get('radio'))
        if radio <= 0:
            return jsonify({'error': 'El radio debe ser mayor a 0'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Radio inválido'}), 400

    try:
        new_zona_segura = ZonaSegura(
            nombre=nombre,
            latitud=latitud,
            longitud=longitud,
            radio=radio,
            cuenta_id=request.user_id
        )
        db.session.add(new_zona_segura)
        db.session.commit()
        return jsonify({'mensaje': 'Zona segura creada con éxito', 'data': new_zona_segura.to_json()}), 201
    except Exception as e:
        return jsonify({'error': f'Error al crear zona segura: {str(e)}'}), 500


@zona_segura.route('/editar_zona_segura', methods=['PUT'])
@token_required
def editar_zona_segura():
    safe_area_data = request.get_json()

    try:
        zona_segura_id = int(safe_area_data.get('zona_segura_id'))
    except (ValueError, TypeError):
        return jsonify({'error': 'ID de zona segura inválido'}), 400

    update_zona_segura = ZonaSegura.query.filter_by(id=zona_segura_id).first()
    if not update_zona_segura:
        return jsonify({'error': 'Zona segura no encontrada'}), 404

    nombre = str(safe_area_data.get('nombre', '')).strip()
    if nombre:
        update_zona_segura.nombre = nombre

    try:
        latitud = safe_area_data.get('latitud')
        if latitud is not None:
            latitud = float(latitud)
            if not (-90 <= latitud <= 90):
                return jsonify({'error': 'Latitud fuera de rango (-90 a 90)'}), 400
            update_zona_segura.latitud = latitud
    except (ValueError, TypeError):
        return jsonify({'error': 'Latitud inválida'}), 400

    try:
        longitud = safe_area_data.get('longitud')
        if longitud is not None:
            longitud = float(longitud)
            if not (-180 <= longitud <= 180):
                return jsonify({'error': 'Longitud fuera de rango (-180 a 180)'}), 400
            update_zona_segura.longitud = longitud
    except (ValueError, TypeError):
        return jsonify({'error': 'Longitud inválida'}), 400

    try:
        radio = safe_area_data.get('radio')
        if radio is not None:
            radio = float(radio)
            if radio <= 0:
                return jsonify({'error': 'El radio debe ser mayor a 0'}), 400
            update_zona_segura.radio = radio
    except (ValueError, TypeError):
        return jsonify({'error': 'Radio inválido'}), 400

    db.session.commit()
    return jsonify({'mensaje': 'Zona segura actualizada con éxitos', 'data': update_zona_segura.to_json()}), 200

@zona_segura.route('/eliminar_zona_segura', methods=['DELETE'])
@token_required
def eliminar_zona_segura():
    safe_area_data = request.get_json()

    try:
        zona_segura_id = int(safe_area_data.get('zona_segura_id'))
    except (ValueError, TypeError):
        return jsonify({'error': 'ID de zona segura inválido'}), 400

    try:
        delete_zona_segura = ZonaSegura.query.filter_by(id=zona_segura_id).first()
        if not delete_zona_segura:
            return jsonify({'error': 'Zona segura no encontrada'}), 404

        db.session.delete(delete_zona_segura)
        db.session.commit()
        return jsonify({'mensaje': 'La zona segura se eliminó con exito'}), 200
    except Exception as e:
        return jsonify({'error': f'Error: {e}'}), 500