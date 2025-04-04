from .extensions import db

class Cuenta(db.Model):
    __tablename__ = 'cuenta'
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(255), nullable=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo_electronico = db.Column(db.String(255), unique=True, nullable=False)
    hash_contraseña = db.Column(db.String(60), nullable=False)
    peso = db.Column(db.Numeric(5, 2), nullable=True)
    altura = db.Column(db.Numeric(5, 2), nullable=True)
    sexo = db.Column(db.Enum('M', 'F', 'Otro'), nullable=True)
    fecha_nacimiento = db.Column(db.Date, nullable=True)

    def to_json(self):
        return {
            'cuenta_id': self.id,
            'google_id': self.google_id,
            'nombre': self.nombre,
            'correo_electronico': self.correo_electronico,
            'peso': float(self.peso) if self.peso else None,
            'altura': float(self.altura) if self.altura else None,
            'sexo': self.sexo,
            'fecha_nacimiento': self.fecha_nacimiento.isoformat() if self.fecha_nacimiento else None,
        }

    condiciones = db.relationship('Condicion', secondary='cuenta_condicion', backref='cuentas', lazy='dynamic')
    zonas_seguras = db.relationship('ZonaSegura', backref='cuenta', lazy=True)
    signos_vitales = db.relationship('SignoVital', backref='cuenta', lazy=True)
    alertas = db.relationship('Alerta', backref='cuenta', lazy=True)

class Condicion(db.Model):
    __tablename__ = 'condicion'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)

    def to_json(self):
        return {
            'condicion_id': self.id,
            'nombre': self.nombre,
        }

class CuentaCondicion(db.Model):
    __tablename__ = 'cuenta_condicion'
    cuenta_id = db.Column(db.Integer, db.ForeignKey('cuenta.id'), primary_key=True)
    condicion_id = db.Column(db.Integer, db.ForeignKey('condicion.id'), primary_key=True)

    def to_json(self):
        return {
            'cuenta_id': self.cuenta_id,
            'condicion_id': self.condicion_id,
        }

class Grupo(db.Model):
    __tablename__ = 'grupo'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)

    def to_json(self):
        return {
            'grupo_id': self.id,
            'nombre': self.nombre,
        }

class MiembroGrupo(db.Model):
    __tablename__ = 'miembro_grupo'
    cuenta_id = db.Column(db.Integer, db.ForeignKey('cuenta.id'), primary_key=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), primary_key=True)
    es_administrador = db.Column(db.Boolean, default=False)

    def to_json(self):
        return {
            'cuenta_id': self.cuenta_id,
            'grupo_id': self.grupo_id,
            'es_administrador': self.es_administrador,
        }

class ZonaSegura(db.Model):
    __tablename__ = 'zona_segura'
    id = db.Column(db.Integer, primary_key=True)
    cuenta_id = db.Column(db.Integer, db.ForeignKey('cuenta.id'), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    latitud = db.Column(db.Float, nullable=False)
    longitud = db.Column(db.Float, nullable=False)
    radio = db.Column(db.Float, nullable=False)

    def to_json(self):
        return {
            'zona_segura_id': self.id,
            'cuenta_id': self.cuenta_id,
            'nombre': self.nombre,
            'latitud': self.latitud,
            'longitud': self.longitud,
            'radio': self.radio
        }

class TipoSignoVital(db.Model):
    __tablename__ = 'tipo_signo_vital'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
    unidad = db.Column(db.String(50))

    def to_json(self):
        return {
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'unidad': self.unidad,
        }

class SignoVital(db.Model):
    __tablename__ = 'signo_vital'
    id = db.Column(db.Integer, primary_key=True)
    cuenta_id = db.Column(db.Integer, db.ForeignKey('cuenta.id'), nullable=False)
    tipo_id = db.Column(db.Integer, db.ForeignKey('tipo_signo_vital.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=db.func.current_timestamp())
    valor_numerico_1 = db.Column(db.Float)  # Primer valor (frecuencia cardíaca o sistólica)
    valor_numerico_2 = db.Column(db.Float)  # Segundo valor (diastólica)

    def to_json(self):
        return {
            'signo_vital_id': self.id,
            'cuenta_id': self.cuenta_id,
            'tipo_id': self.tipo_id,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'valor_numerico_1': self.valor_numerico_1,
            'valor_numerico_2': self.valor_numerico_2 if self.valor_numerico_2 else None
        }

class TipoAlerta(db.Model):
    __tablename__ = 'tipo_alerta'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)

    def to_json(self):
        return {
            'tipo_alerta_id': self.id,
            'nombre': self.nombre,
        }

class Alerta(db.Model):
    __tablename__ = 'alerta'
    id = db.Column(db.Integer, primary_key=True)
    cuenta_id = db.Column(db.Integer, db.ForeignKey('cuenta.id'))
    tipo_id = db.Column(db.Integer, db.ForeignKey('tipo_alerta.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=db.func.current_timestamp())
    atendida = db.Column(db.Boolean, default=False)

    def to_json(self):
        return {
            'alerta_id': self.id,
            'cuenta_id': self.cuenta_id,
            'tipo_id': self.tipo_id,
            'fecha': self.fecha,
            'atendida': self.atendida,
        }
class ubicacion(db.Model):
    __tablename__ = 'ubicacion'
    id = db.Column(db.Integer, primary_key=True)
    cuenta_id = db.Column(db.Integer, db.ForeignKey('cuenta.id'))
    latitud = db.Column(db.Float, nullable=True)
    longitud = db.Column(db.Float, nullable=True)

    def to_json(self):
        return {
            'ubicacion_id': self.id,
            'cuenta_id': self.cuenta_id,
            'latitud': self.latitud,
            'longitud': self.longitud,
        }