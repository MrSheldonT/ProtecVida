# ProtectVida

ProtectVida es una aplicación que aprovecha el protocolo de comunicación BLE para conectarse con reojes inteligentes y otros dispositivos con el fin de ofrecer un monitoreo continuo sobre la salud. Los datos como la oxigenación en sangre, ritmo cardíaco y presión arterial se analizan para detectar posibles anomalías y generar alertas automáticas a familiares cercanos en caso de emergencia.

- Monitoreo de signos vitales: Realiza un ánalisis de los signos vitales con el fin de generar un analisis y alertas.
- Areas seguras: Configuración de áreas seguras para tener un monitoreo de los usuarios y generando notificaciones.
- Grupos: Creación de grupos familiares para un monitoreo compartido, permitiendo el acceso a información en tiempo real sobre el estado de salud de los integrantes.
- Notificaciones personalizadas: Configuración personalizada de alertas según el tipo, miembro, étc.

## Diagrama ER
```mermaid
erDiagram
    cuenta {
        int id PK
        varchar google_id
        varchar nombre
        varchar correo_electronico
        char hash_contraseña
        decimal peso
        decimal altura
        enum sexo
        date fechaNacimiento
    }

    condicion {
        int id PK
        varchar nombre 
    }

    cuenta_condicion {
        int cuenta_id FK
        int condicion_id FK
    }

    grupo {
        int id PK
        varchar nombre
    }

    miembro_grupo {
        int cuenta_id FK
        int grupo_id FK
        boolean es_administrador
    }

    zona_segura {
        int id PK
        int cuenta_id FK
        varchar nombre
        double latitud
        double longitud
        double radio
    }

    tipo_signo_vital {
        int id PK
        varchar nombre
        text descripcion
        varchar unidad
    }

    signo_vital {
        int id PK
        int cuenta_id FK
        int tipo_id FK
        datetime fecha
        double valor_numerico_1
        double valor_numerico_2
    }

    tipo_alerta {
        int id PK
        varchar nombre
    }

    alerta {
        int id PK
        int cuenta_id FK
        int tipo_id FK
        datetime fecha
        boolean atendida
    }

    cuenta ||--o{ cuenta_condicion : "tiene"
    condicion ||--o{ cuenta_condicion : "asociada"

    cuenta ||--o{ miembro_grupo : "pertenece"
    grupo ||--o{ miembro_grupo : "contiene"

    cuenta ||--o{ zona_segura : "crea"

    cuenta ||--o{ signo_vital : "registra"
    tipo_signo_vital ||--o{ signo_vital : "clasifica"

    cuenta ||--o{ alerta : "genera"
    tipo_alerta ||--o{ alerta : "clasifica"

```