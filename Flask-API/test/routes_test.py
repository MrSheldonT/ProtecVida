# tests/test_cuenta.py
import pytest

@pytest.fixture
def jwt_token(client):
    data = {
    "nombre": "Jonh doe",
    "correo_electronico": "test@example.com",
    "contrasenia": "Morales12#",
    }

    client.post("/cuenta/registrarse", json=data)

    response = client.post("/cuenta/acceder", json=data)

    data = response.get_json()
    return data.get("jwt_token")

def test_crear_cuenta(client):
    data = {
        "nombre": "Jonh doe",
        "correo_electronico": "test@example.com",
        "contrasenia": "Morales12#",
    }
    response = client.post("/cuenta/registrarse", json=data)
    assert response.status_code in (200, 201)

def test_iniciar_sesion(client):
    data = {
        "nombre": "Jonh doe",
        "correo_electronico": "test@example.com",
        "contrasenia": "Morales12#",
    }
    response_crear = client.post("/cuenta/registrarse", json=data)
    response = client.post("/cuenta/acceder", json=data)

    print("STATUS:", response.status_code)
    print("JSON:", response.get_data(as_text=True)) 

    data = response.get_json()
    print("Respuesta JSON:", data) 

    assert data["mensaje"] == "Logueado correctamente"

def test_iniciar_sesion_usuario_no_registrado(client):
    data = {
        "nombre": "Jonh doe",
        "correo_electronico": "test@example.com",
        "contrasenia": "Morales12#",
    }
    response = client.post("/cuenta/acceder", json=data)

    data = response.get_json()
    print("Respuesta JSON:", data)  

    assert data["error"] == "No se ha encontrado la cuenta"


def test_verificar_informacion_cuenta(client):
    data = {
        "nombre": "Jonh doe",
        "correo_electronico": "test@example.com",
        "contrasenia": "Morales12#",
    }
    response_crear = client.post("/cuenta/registrarse", json=data)
    response = client.post("/cuenta/acceder", json=data)

    print("STATUS:", response.status_code)
    print("JSON:", response.get_data(as_text=True))  

    data = response.get_json()
    print("Respuesta JSON:", data)
    
    token = data.get("jwt_token")
    print("Token JWT:", token)

    headers = {
        "Authorization": token 
    }
    
    response_info = client.get("/cuenta/conseguir_cuenta", headers=headers)

    print("STATUS de obtener cuenta:", response_info.status_code)
    print("JSON de obtener cuenta:", response_info.get_data(as_text=True))
    
    data_info = response_info.get_json()
    assert response_info.status_code == 200
    assert data_info["mensaje"] == "Información de la cuenta recuperada"
    assert "data" in data_info 

def test_actualizar_datos_usuario(client,jwt_token):
    headers = {
        "Authorization": jwt_token 
    }

    body ={
        "altura": 178.0,
        "peso": 72.0
    }
    
    response_info = client.put("/cuenta/editar_perfil", headers=headers,json=body)
    data = response_info.get_json()
    assert data["data"]["altura"] == 178.0
    assert data["data"]["peso"] == 72.0
    assert data["mensaje"] == "Cuenta Jonh doe(test@example.com) editada exitosamente"
    
def test_configurar_zona_segura(client,jwt_token):
    headers = {
        "Authorization": jwt_token 
    }
    body ={
        "latitud":10.0,
        "longitud":10.0,
        "radio":100.0,
        "nombre":"zona prueba"
    }
    response = client.post("/zona_segura/crear_zona_segura", headers=headers,json=body)
    data = response.get_json()
    assert data["mensaje"] == "Zona segura creada con éxito"
    assert data["data"]["latitud"] ==10.0
    assert data["data"]["longitud"] == 10.0
    assert data["data"]["radio"] == 100.0
    assert data["data"]["nombre"] == "zona prueba"

def test_crear_nuevo_grupo(client,jwt_token):
    headers = {
        "Authorization": jwt_token 
    }
    body ={
        "nombre_grupo":"grupo 1"
    }
    response = client.post("/grupo/crear_grupo", headers=headers,json=body)
    data = response.get_json()
    assert data["mensaje"] == "Grupo grupo 1 creado exitosamente"


def test_Agregar_usuario_al_grupo(client, jwt_token):
    headers = {
        "Authorization": jwt_token
    }

    body = {
        "nombre_grupo": "grupo 1"
    }

    new_user = {
        "nombre": "Jonh doe 2",
        "correo_electronico": "test@example2.com",
        "contrasenia": "Morales12#",
    }

    response_crear_grupo = client.post("/grupo/crear_grupo", headers=headers, json=body)
    response_registrar = client.post("/cuenta/registrarse", json=new_user)

    data_crear_grupo = response_crear_grupo.get_json()
    grupo_id = data_crear_grupo["data"]["grupo_id"]

    add_member_body = {
        "correo_electronico": "test@example2.com",
        "grupo_id": grupo_id
    }

    response_agregar = client.post("/grupo/agregar_miembro", headers=headers, json=add_member_body)
    assert response_agregar.get_json()["mensaje"] == "Usuario Jonh doe 2 agregado al grupo 1"

    response_listado = client.get(f"/grupo/conseguir_miembros_grupo/{grupo_id}", headers=headers)
    miembros = response_listado.get_json()["data"]
    nombres = [miembro["cuenta"]["nombre"] for miembro in miembros]

    assert "Jonh doe 2" in nombres

    


def test_eliminar_miembro_al_grupo(client, jwt_token):
    headers = {
        "Authorization": jwt_token
    }

    body = {
        "nombre_grupo": "grupo 1"
    }

    new_user = {
        "nombre": "Jonh doe 2",
        "correo_electronico": "test@example2.com",
        "contrasenia": "Morales12#",
    }

    response_crear_grupo = client.post("/grupo/crear_grupo", headers=headers, json=body)
    response_registrar = client.post("/cuenta/registrarse", json=new_user)

    data_crear_grupo = response_crear_grupo.get_json()
    data_registro = response_registrar.get_json()
    grupo_id = data_crear_grupo["data"]["grupo_id"]
    user_id = data_registro["data"]["cuenta_id"]

    add_member_body = {
        "correo_electronico": "test@example2.com",
        "grupo_id": grupo_id
    }

    admin_body = {
        "grupo_id": grupo_id,
        "user_id": user_id
    }

    client.post("/grupo/agregar_miembro", headers=headers, json=add_member_body)
    response_eliminar = client.delete("/grupo/eliminar_miembro", headers=headers, json=admin_body)
    assert response_eliminar.get_json()["mensaje"] == f"Se ha eliminado al usuario {user_id} exitosamente"

    response_listado = client.get(f"/grupo/conseguir_miembros_grupo/{grupo_id}", headers=headers)
    miembros = response_listado.get_json()["data"]
    ids = [miembro["cuenta"]["cuenta_id"] for miembro in miembros]

    assert user_id not in ids


def test_Agregar_administrador_al_grupo(client,jwt_token):
    headers = {
        "Authorization": jwt_token 
    }
    
    body ={
        "nombre_grupo":"grupo 1"
    }

    new_user = {
        "nombre": "Jonh doe 2",
        "correo_electronico": "test@example2.com",
        "contrasenia": "Morales12#",
    }

    response_crear_grupo = client.post("/grupo/crear_grupo", headers=headers,json=body)
    response_registrar = client.post("/cuenta/registrarse", json=new_user)
    
    data_registro = response_registrar.get_json()
    data_crear_grupo = response_crear_grupo.get_json()
    nuevo_usuario_id = data_registro["data"]["cuenta_id"]
    nuevo_grupo_id = data_crear_grupo["data"]["grupo_id"]

    add_member_body={
        "correo_electronico":"test@example2.com",
        "grupo_id":nuevo_grupo_id
    }

    admin_body={
        "grupo_id":nuevo_grupo_id,
        "user_id":nuevo_usuario_id
    }

    response_crear_grupo = client.post("/grupo/agregar_miembro", headers=headers,json=add_member_body)
    response_admin = client.post("/grupo/agregar_administrador", headers=headers,json=admin_body)
    response_data_admin = response_admin.get_json()
    assert response_data_admin["mensaje"] == f"Se ha actualizado los permisos al usuario {nuevo_usuario_id} exitosamente"

    

def test_listar_miembros_grupo(client, jwt_token):
    headers = {
        "Authorization": jwt_token
    }

    body = {
        "nombre_grupo": "grupo 1"
    }

    response_crear_grupo = client.post("/grupo/crear_grupo", headers=headers, json=body)
    data_crear_grupo = response_crear_grupo.get_json()
    grupo_id = data_crear_grupo["data"]["grupo_id"]

    response_listado = client.get(f"/grupo/conseguir_miembros_grupo/{grupo_id}", headers=headers)
    data_listado = response_listado.get_json()

    assert response_listado.status_code == 200
    assert data_listado["mensaje"] == "Miembros del grupo listados con éxito"
    assert isinstance(data_listado["data"], list)
    assert len(data_listado["data"]) == 1

def test_editar_grupo(client, jwt_token):
    headers = {
        "Authorization": jwt_token
    }

    body_creacion = {
        "nombre_grupo": "grupo original"
    }
    response_crear = client.post("/grupo/crear_grupo", headers=headers, json=body_creacion)
    data_crear = response_crear.get_json()
    grupo_id = data_crear["data"]["grupo_id"]

    body_editar = {
        "grupo_id": grupo_id,
        "nombre_grupo": "grupo editado"
    }
    response_editar = client.put("/grupo/editar_grupo", headers=headers, json=body_editar)
    data_editar = response_editar.get_json()

    assert response_editar.status_code == 200
    assert data_editar["mensaje"] == "Grupo editado con éxito"

    response_verificar = client.get(f"/grupo/conseguir_miembros_grupo/{grupo_id}", headers=headers)
    data_verificar = response_verificar.get_json()
    assert data_verificar["data"][0]["nombre"] == "grupo editado"

def test_eliminar_grupo_exitoso(client, jwt_token):
    headers = {"Authorization": jwt_token}
    crear_grupo_data = {"nombre_grupo": "Grupo a eliminar"}
    response_crear = client.post("/grupo/crear_grupo", headers=headers, json=crear_grupo_data)
    grupo_id = response_crear.get_json()["data"]["grupo_id"]

    eliminar_data = {"grupo_id": grupo_id}
    response = client.delete("/grupo/eliminar_grupo", headers=headers, json=eliminar_data)
    
    data = response.get_json()
    print("Respuesta JSON:", data)
    
    assert response.status_code == 200
    assert data["mensaje"] == "El grupo ha sido eliminado con éxito"
    assert data["data"]["nombre"] == "Grupo a eliminar"

def test_salir_grupo_exitoso(client, jwt_token):
    headers = {"Authorization": jwt_token}
    crear_grupo_data = {"nombre_grupo": "Grupo para salir"}
    response_crear = client.post("/grupo/crear_grupo", headers=headers, json=crear_grupo_data)
    grupo_id = response_crear.get_json()["data"]["grupo_id"]

    salir_data = {"grupo_id": grupo_id}
    response = client.delete("/grupo/salir_grupo", headers=headers, json=salir_data)
    
    data = response.get_json()
    assert response.status_code == 200
    assert data["mensaje"] == "Se ha salido del grupo exitosamente"

def test_salir_grupo_sin_id(client, jwt_token):
    headers = {"Authorization": jwt_token}
    salir_data = {}  # Sin grupo_id
    
    response = client.delete("/grupo/salir_grupo", headers=headers, json=salir_data)
    data = response.get_json()
    
    assert response.status_code == 400
    assert data["error"] == "Error, no has ingresado el ID del grupo"

def test_salir_grupo_no_miembro(client, jwt_token):
    otro_usuario = {
        "nombre": "Usuario 2",
        "correo_electronico": "usuario2@test.com",
        "contrasenia": "Password123#"
    }
    client.post("/cuenta/registrarse", json=otro_usuario)
    login_resp = client.post("/cuenta/acceder", json=otro_usuario)
    otro_token = login_resp.get_json()["jwt_token"]
    
    headers_otro = {"Authorization": otro_token}
    crear_grupo_data = {"nombre_grupo": "Grupo de otro"}
    response_crear = client.post("/grupo/crear_grupo", headers=headers_otro, json=crear_grupo_data)
    grupo_id = response_crear.get_json()["data"]["grupo_id"]

    headers = {"Authorization": jwt_token}
    salir_data = {"grupo_id": grupo_id}
    response = client.delete("/grupo/salir_grupo", headers=headers, json=salir_data)
    
    data = response.get_json()
    assert response.status_code == 404
    assert data["error"] == "Error, no te encuentras en el grupo"

def test_salir_grupo_ultimo_administrador(client, jwt_token):
    headers = {"Authorization": jwt_token}
    crear_grupo_data = {"nombre_grupo": "Grupo con admin"}
    response_crear = client.post("/grupo/crear_grupo", headers=headers, json=crear_grupo_data)
    grupo_id = response_crear.get_json()["data"]["grupo_id"]

    otro_usuario = {
        "nombre": "Usuario normal",
        "correo_electronico": "normal@test.com",
        "contrasenia": "Password123#"
    }
    client.post("/cuenta/registrarse", json=otro_usuario)
    
    add_member_data = {
        "correo_electronico": "normal@test.com",
        "grupo_id": grupo_id
    }
    client.post("/grupo/agregar_miembro", headers=headers, json=add_member_data)

    salir_data = {"grupo_id": grupo_id}
    response = client.delete("/grupo/salir_grupo", headers=headers, json=salir_data)
    
    data = response.get_json()
    assert response.status_code == 200
    assert data["mensaje"] == "Se ha salido del grupo exitosamente"


def test_quitar_administrador_exitoso(client, jwt_token):
    headers = {"Authorization": jwt_token}
    crear_grupo_data = {"nombre_grupo": "Grupo con admin"}
    response_crear = client.post("/grupo/crear_grupo", headers=headers, json=crear_grupo_data)
    grupo_id = response_crear.get_json()["data"]["grupo_id"]

    otro_usuario = {
        "nombre": "Usuario Admin",
        "correo_electronico": "admin@test.com",
        "contrasenia": "Password123#"
    }
    response_registro = client.post("/cuenta/registrarse", json=otro_usuario)
    otro_user_id = response_registro.get_json()["data"]["cuenta_id"]

    add_member_data = {
        "correo_electronico": "admin@test.com",
        "grupo_id": grupo_id
    }
    client.post("/grupo/agregar_miembro", headers=headers, json=add_member_data)
    
    make_admin_data = {
        "grupo_id": grupo_id,
        "user_id": otro_user_id
    }
    client.post("/grupo/agregar_administrador", headers=headers, json=make_admin_data)

    quitar_admin_data = {
        "grupo_id": grupo_id,
        "user_id": otro_user_id
    }
    response = client.post("/grupo/quitar_administrador", headers=headers, json=quitar_admin_data)
    
    data = response.get_json()
    assert response.status_code == 200
    assert data["mensaje"] == f"Se ha actualizado los permisos al usuario {otro_user_id} exitosamente"
    assert data["data"]["es_administrador"] == False



def test_quitar_administrador_a_si_mismo(client, jwt_token):
    headers = {"Authorization": jwt_token}
    crear_grupo_data = {"nombre_grupo": "Grupo self admin"}
    response_crear = client.post("/grupo/crear_grupo", headers=headers, json=crear_grupo_data)
    grupo_id = response_crear.get_json()["data"]["grupo_id"]

    user_info = client.get("/cuenta/conseguir_cuenta", headers=headers)
    user_id = user_info.get_json()["data"]["cuenta_id"]

    quitar_admin_data = {
        "grupo_id": grupo_id,
        "user_id": user_id
    }
    response = client.post("/grupo/quitar_administrador", headers=headers, json=quitar_admin_data)
    
    data = response.get_json()
    assert response.status_code == 409
    assert data["error"] == "No puedes hacer esta operación con tu propia cuenta"

def test_quitar_administrador_usuario_no_existe(client, jwt_token):
    headers = {"Authorization": jwt_token}
    crear_grupo_data = {"nombre_grupo": "Grupo test no existe"}
    response_crear = client.post("/grupo/crear_grupo", headers=headers, json=crear_grupo_data)
    grupo_id = response_crear.get_json()["data"]["grupo_id"]

    quitar_admin_data = {
        "grupo_id": grupo_id,
        "user_id": 99999  
    }
    response = client.post("/grupo/quitar_administrador", headers=headers, json=quitar_admin_data)
    
    data = response.get_json()
    assert response.status_code == 404
    assert data["error"] == "Error, este usuario no se encuentra en el grupo"

def test_quitar_administrador_faltan_datos(client, jwt_token):
    headers = {"Authorization": jwt_token}
    data_sin_user = {"grupo_id": 1}
    response = client.post("/grupo/quitar_administrador", headers=headers, json=data_sin_user)
    assert response.status_code == 400
    assert response.get_json()["error"] == "No se ha ingresado el usuario del miembro ha eliminar"

    data_sin_grupo = {"user_id": 1}
    response = client.post("/grupo/quitar_administrador", headers=headers, json=data_sin_grupo)
    assert response.status_code == 400
    assert response.get_json()["error"] == "No se ha ingresado el grupo"