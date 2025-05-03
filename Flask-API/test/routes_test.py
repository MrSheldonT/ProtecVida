# tests/test_cuenta.py
import pytest

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