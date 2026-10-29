# auth-service/app/models.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


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
                         back_populates='usuario', cascade='all, delete-orphan', lazy='selectin')

    @property
    def password(self):
        raise AttributeError('password is write-only')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def validar_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.usuario_id)

    def _get_rol_principal(self):
        try:
            for ur in self.roles:
                if ur.es_rol_principal and ur.rol is not None:
                    return ur.rol.nombre_rol
        except Exception:
            return None
        return None

    def is_admin(self):
        return self._get_rol_principal() == 'administrador_sistema'

    def is_medico(self):
        rol = self._get_rol_principal()
        return rol is not None and rol.startswith('medico')

    def is_enfermero(self):
        rol = self._get_rol_principal()
        return rol is not None and rol.startswith('enfermero')

    def is_paciente(self):
        rol = self._get_rol_principal()
        return rol is not None and rol.startswith('paciente')

    def tiene_permiso(self, nombre_permiso):
        for ur in self.roles:
            if ur.fecha_expiracion and ur.fecha_expiracion < datetime.utcnow():
                continue
            if ur.rol is None:
                continue
            for rp in ur.rol.permisos:
                if rp.fecha_expiracion and rp.fecha_expiracion < datetime.utcnow():
                    continue
                if rp.permiso and rp.permiso.nombre_permiso == nombre_permiso:
                    return True
        return False

    @classmethod
    def validar(cls, email, password):
        usuario = cls.query.filter_by(email=email).first()
        if not usuario or not usuario.estado or usuario.cuenta_bloqueada:
            return None
        if usuario.validar_password(password):
            usuario.intentos_login = 0
            db.session.commit()
            return usuario
        usuario.intentos_login = (usuario.intentos_login or 0) + 1
        if usuario.intentos_login >= 5:
            usuario.cuenta_bloqueada = True
        db.session.commit()
        return None


class RolDetalle(db.Model):
    __tablename__ = 'roles_detalle'
    rol_id = Column(Integer, primary_key=True)
    nombre_rol = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text, nullable=False)
    nivel_permisos = Column(Integer, nullable=False)
    puede_crear_usuarios = Column(Boolean, default=False)
    puede_eliminar_datos = Column(Boolean, default=False)
    puede_configurar_sistema = Column(Boolean, default=False)
    acceso_total = Column(Boolean, default=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    creado_por = Column(Integer, db.ForeignKey('usuarios.usuario_id'))

    creador = relationship('Usuario', foreign_keys=[creado_por])
    usuarios = relationship('UsuarioRol', back_populates='rol')
    permisos = relationship('RolPermiso', back_populates='rol', lazy='selectin')


class Permiso(db.Model):
    __tablename__ = 'permisos'
    permiso_id = Column(Integer, primary_key=True)
    nombre_permiso = Column(String(100), unique=True, nullable=False)
    descripcion = Column(Text, nullable=False)
    categoria = Column(Enum('lectura', 'escritura', 'eliminacion', 'administracion'), nullable=False)
    modulo = Column(String(50), nullable=False)
    es_critico = Column(Boolean, default=False)

    roles = relationship('RolPermiso', back_populates='permiso')


class RolPermiso(db.Model):
    __tablename__ = 'rol_permisos'
    rol_permiso_id = Column(Integer, primary_key=True)
    rol_id = Column(Integer, db.ForeignKey('roles_detalle.rol_id'), nullable=False)
    permiso_id = Column(Integer, db.ForeignKey('permisos.permiso_id'), nullable=False)
    concedido_por = Column(Integer, db.ForeignKey('usuarios.usuario_id'), nullable=False)
    fecha_concesion = Column(DateTime, default=datetime.utcnow)
    fecha_expiracion = Column(DateTime)

    rol = relationship('RolDetalle', back_populates='permisos')
    permiso = relationship('Permiso', back_populates='roles', lazy='joined')
    concedente = relationship('Usuario', foreign_keys=[concedido_por])


class UsuarioRol(db.Model):
    __tablename__ = 'usuario_roles'
    usuario_rol_id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, db.ForeignKey('usuarios.usuario_id'), nullable=False)
    rol_id = Column(Integer, db.ForeignKey('roles_detalle.rol_id'), nullable=False)
    asignado_por = Column(Integer, db.ForeignKey('usuarios.usuario_id'), nullable=False)
    fecha_asignacion = Column(DateTime, default=datetime.utcnow)
    fecha_expiracion = Column(DateTime)
    es_rol_principal = Column(Boolean, default=False)

    usuario = relationship('Usuario', foreign_keys=[usuario_id], back_populates='roles')
    rol = relationship('RolDetalle', back_populates='usuarios', lazy='joined')
    asignante = relationship('Usuario', foreign_keys=[asignado_por])