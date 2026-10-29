from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text,
    Enum, Numeric, JSON, ForeignKey
)
from sqlalchemy.orm import relationship
from app.extensions import db


# ─────────────────────────────────────────────
# Modelos compartidos con auth-service (solo lectura)
# ─────────────────────────────────────────────

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    usuario_id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    telefono = Column(String(20))
    direccion = Column(Text)
    codigo_postal = Column(String(10))
    genero = Column(Enum('M', 'F', 'O'))
    estado = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ultimo_login = Column(DateTime)
    intentos_login = Column(Integer, default=0)
    cuenta_bloqueada = Column(Boolean, default=False)

    roles = relationship('UsuarioRol', foreign_keys='UsuarioRol.usuario_id',
                         back_populates='usuario', lazy='selectin')

    signos_vitales = relationship('SignoVital', foreign_keys='SignoVital.paciente_id',
                                  back_populates='paciente')
    historial_creado = relationship('HistorialClinico',
                                    foreign_keys='HistorialClinico.profesional_id',
                                    back_populates='profesional')
    historial_paciente = relationship('HistorialClinico',
                                      foreign_keys='HistorialClinico.paciente_id',
                                      back_populates='paciente')
    alertas = relationship('Alerta', foreign_keys='Alerta.paciente_id',
                           back_populates='paciente')
    alertas_resueltas = relationship('Alerta', foreign_keys='Alerta.resuelta_por',
                                     back_populates='resolutor')

    def _get_rol_principal(self):
        for ur in self.roles:
            if ur.es_rol_principal and ur.rol is not None:
                return ur.rol.nombre_rol
        return None


class RolDetalle(db.Model):
    __tablename__ = 'roles_detalle'
    rol_id = Column(Integer, primary_key=True)
    nombre_rol = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)
    nivel_permisos = Column(Integer, nullable=False)
    puede_crear_usuarios = Column(Boolean, default=False)
    puede_eliminar_datos = Column(Boolean, default=False)
    puede_configurar_sistema = Column(Boolean, default=False)
    acceso_total = Column(Boolean, default=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    creado_por = Column(Integer, ForeignKey('usuarios.usuario_id'))

    usuarios = relationship('UsuarioRol', back_populates='rol')


class UsuarioRol(db.Model):
    __tablename__ = 'usuario_roles'
    usuario_rol_id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.usuario_id'), nullable=False)
    rol_id = Column(Integer, ForeignKey('roles_detalle.rol_id'), nullable=False)
    asignado_por = Column(Integer, ForeignKey('usuarios.usuario_id'), nullable=False)
    fecha_asignacion = Column(DateTime, default=datetime.utcnow)
    fecha_expiracion = Column(DateTime)
    es_rol_principal = Column(Boolean, default=False)

    usuario = relationship('Usuario', foreign_keys=[usuario_id], back_populates='roles')
    rol = relationship('RolDetalle', back_populates='usuarios', lazy='joined')


# ─────────────────────────────────────────────
# Modelos clínicos (los del monolito)
# ─────────────────────────────────────────────

class SignoVital(db.Model):
    __tablename__ = 'signos_vitales'
    signo_vital_id = Column(Integer, primary_key=True)
    paciente_id = Column(Integer, ForeignKey('usuarios.usuario_id'), nullable=False)
    glucosa = Column(Numeric(5, 2))
    presion_sistolica = Column(Integer)
    presion_diastolica = Column(Integer)
    peso = Column(Numeric(5, 2))
    frecuencia_cardiaca = Column(Integer)
    oxigenacion = Column(Numeric(5, 2))
    tipo_registro = Column(Enum('automatico', 'manual'), nullable=False)
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    validado_por = Column(Integer, ForeignKey('usuarios.usuario_id'))
    fecha_validacion = Column(DateTime)
    observaciones = Column(Text)

    paciente = relationship('Usuario', foreign_keys=[paciente_id],
                            back_populates='signos_vitales')
    validador = relationship('Usuario', foreign_keys=[validado_por])

    @classmethod
    def consulta_por_paciente(cls, paciente_id):
        return (cls.query.filter_by(paciente_id=paciente_id)
                .order_by(cls.fecha_registro.desc()).all())


class Alerta(db.Model):
    __tablename__ = 'alertas'
    alerta_id = Column(Integer, primary_key=True)
    paciente_id = Column(Integer, ForeignKey('usuarios.usuario_id'), nullable=False)
    tipo_signo_vital = Column(
        Enum('glucosa', 'presion_arterial', 'peso',
             'frecuencia_cardiaca', 'oxigenacion'),
        nullable=False
    )
    valor_registrado = Column(Numeric(8, 2), nullable=False)
    nivel_urgencia = Column(Enum('normal', 'alerta', 'critico'), nullable=False)
    mensaje = Column(Text, nullable=False)
    fecha_generacion = Column(DateTime, default=datetime.utcnow)
    fecha_resolucion = Column(DateTime)
    resuelta_por = Column(Integer, ForeignKey('usuarios.usuario_id'))
    estado = Column(Enum('activa', 'en_proceso', 'resuelta', 'falsa_alarma'),
                    default='activa')
    accion_tomada = Column(Text)

    paciente = relationship('Usuario', foreign_keys=[paciente_id],
                            back_populates='alertas')
    resolutor = relationship('Usuario', foreign_keys=[resuelta_por],
                             back_populates='alertas_resueltas')


class HistorialClinico(db.Model):
    __tablename__ = 'historial_clinico'
    historial_id = Column(Integer, primary_key=True)
    paciente_id = Column(Integer, ForeignKey('usuarios.usuario_id'), nullable=False)
    tipo_entrada = Column(
        Enum('diagnostico', 'medicamento', 'antecedente', 'laboratorio', 'evolucion'),
        nullable=False
    )
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text)
    archivo_url = Column(String(500))
    profesional_id = Column(Integer, ForeignKey('usuarios.usuario_id'), nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    es_urgente = Column(Boolean, default=False)
    categoria = Column(String(100))
    nivel_confidencialidad = Column(Enum('bajo', 'medio', 'alto', 'critico'),
                                    default='medio')

    paciente = relationship('Usuario', foreign_keys=[paciente_id],
                            back_populates='historial_paciente')
    profesional = relationship('Usuario', foreign_keys=[profesional_id],
                               back_populates='historial_creado')

    @classmethod
    def consulta_por_paciente(cls, paciente_id):
        return (cls.query.filter_by(paciente_id=paciente_id)
                .order_by(cls.fecha_creacion.desc()).all())


class Notificacion(db.Model):
    __tablename__ = 'notificaciones'
    notificacion_id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.usuario_id'), nullable=False)
    titulo = Column(String(200), nullable=False)
    mensaje = Column(Text, nullable=False)
    tipo = Column(Enum('alerta', 'recordatorio', 'sistema', 'general'), nullable=False)
    leida = Column(Boolean, default=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_leida = Column(DateTime)
    url_destino = Column(String(500))
    prioridad = Column(Enum('baja', 'media', 'alta', 'urgente'), default='media')