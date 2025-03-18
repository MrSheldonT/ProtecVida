DROP DATABASE ProtectVida ;
CREATE DATABASE IF NOT EXISTS ProtectVida;
USE ProtectVida;

CREATE TABLE cuenta (
    id INT AUTO_INCREMENT PRIMARY KEY
    , nombre VARCHAR(100) NOT NULL
    , correoElectronico VARCHAR(255) UNIQUE NOT NULL
    , hashContraseña VARCHAR(255) NOT NULL
    , peso INT
    , altura INT
    , sexo ENUM('M', 'F', 'Otro') NOT NULL
    , fechaNacimiento DATE NOT NULL
);

CREATE TABLE condicion (
    id INT AUTO_INCREMENT PRIMARY KEY
    , nombre VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE cuenta_condicion (
    cuenta_id INT
    , condicion_id INT
    , PRIMARY KEY (cuenta_id, condicion_id)
    , FOREIGN KEY (cuenta_id) REFERENCES cuenta(id) ON DELETE CASCADE
    , FOREIGN KEY (condicion_id) REFERENCES condicion(id) ON DELETE CASCADE
);

CREATE TABLE grupo (
    id INT AUTO_INCREMENT PRIMARY KEY
    , nombre VARCHAR(100) NOT NULL
);

CREATE TABLE miembro_grupo (
    id INT AUTO_INCREMENT PRIMARY KEY
    , cuenta_id INT
    , grupo_id INT
    , esAdministrador BOOLEAN DEFAULT FALSE
    , FOREIGN KEY (cuenta_id) REFERENCES cuenta(id) ON DELETE CASCADE
    , FOREIGN KEY (grupo_id) REFERENCES grupo(id) ON DELETE CASCADE
);

CREATE TABLE zona_segura (
    id INT AUTO_INCREMENT PRIMARY KEY
    , cuenta_id INT
    , nombre VARCHAR(100) NOT NULL
    , latitud DOUBLE NOT NULL
    , longitud DOUBLE NOT NULL
    , radio DOUBLE NOT NULL
    , FOREIGN KEY (cuenta_id) REFERENCES cuenta(id) ON DELETE CASCADE
);
-- Esta probablemente se guarde cada cierto tiempo.
CREATE TABLE historial_ubicacion (
    id INT AUTO_INCREMENT PRIMARY KEY
    , cuenta_id INT
    , fecha DATETIME DEFAULT CURRENT_TIMESTAMP
    , latitud DOUBLE NOT NULL
    , longitud DOUBLE NOT NULL
    , FOREIGN KEY (cuenta_id) REFERENCES cuenta(id) ON DELETE CASCADE
);

CREATE TABLE signo_vital (
    id INT AUTO_INCREMENT PRIMARY KEY
    , cuenta_id INT
    , fecha DATETIME DEFAULT CURRENT_TIMESTAMP
    , tipo ENUM('Frecuencia cardiaca', 'Presion arterial', 'Oxigeno en sangre', 'Otro') NOT NULL
    , valor DOUBLE NOT NULL
    , FOREIGN KEY (cuenta_id) REFERENCES cuenta(id) ON DELETE CASCADE
);

CREATE TABLE alerta (
    id INT AUTO_INCREMENT PRIMARY KEY
    , cuenta_id INT
    , tipo ENUM('Caída', 'Apnea', 'Hipertensión', 'Ritmo cardíaco Anormal', 'Otro') NOT NULL
    , fecha DATETIME DEFAULT CURRENT_TIMESTAMP
    , atendida BOOLEAN DEFAULT FALSE
    , FOREIGN KEY (cuenta_id) REFERENCES cuenta(id) ON DELETE CASCADE
);