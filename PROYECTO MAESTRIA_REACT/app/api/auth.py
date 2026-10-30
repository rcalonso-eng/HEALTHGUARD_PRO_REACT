from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from datetime import datetime
from app.extensions import db
from app.models import Usuario, RolDetalle, UsuarioRol

auth_bp = Blueprint('auth', __name__)

# ---------- Helpers ----------
def _usuario_to_dict(u):
    rol = u._get_rol_principal()
    return {
        "usuario_id": u.usuario_id,
        "nombre": u.nombre,
        "email": u.email,
        "telefono": u.telefono,
        "direccion": u.direccion,
        "codigo_postal": u.codigo_postal,
        "genero": u.genero,
        "estado": u.estado,
        "cuenta_bloqueada": u.cuenta_bloqueada,
        "rol_principal": rol,
        "permisos": [
            rp.permiso.nombre_permiso
            for ur in u.roles if ur.rol
            for rp in ur.rol.permisos if rp.permiso
        ],
    }

# ---------- Login ----------
@auth_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or not password:
        return jsonify({"error": "Email y contraseña obligatorios"}), 400

    usuario = Usuario.validar(email, password)

    if not usuario:
        return jsonify({"error": "Credenciales inválidas o cuenta bloqueada"}), 401

    usuario.ultimo_login = datetime.utcnow()
    usuario.intentos_login = 0
    db.session.commit()

    access = create_access_token(identity=usuario.usuario_id)
    refresh = create_refresh_token(identity=usuario.usuario_id)

    return jsonify({
        "access_token": access,
        "refresh_token": refresh,
        "usuario": _usuario_to_dict(usuario)
    }), 200

# ---------- Refresh ----------
@auth_bp.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    uid = get_jwt_identity()
    new_access = create_access_token(identity=int(uid))
    return jsonify({"access_token": new_access}), 200

# ---------- Perfil ----------
@auth_bp.route('/auth/me', methods=['GET'])
@jwt_required()
def me():
    uid = int(get_jwt_identity())
    usuario = Usuario.query.get(uid)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(_usuario_to_dict(usuario)), 200

# ---------- Registro público (paciente) ----------
@auth_bp.route('/auth/registro', methods=['POST'])
def registro():
    data = request.get_json(silent=True) or {}
    nombre = (data.get('nombre') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not nombre or not email or not password:
        return jsonify({"error": "Nombre, email y contraseña obligatorios"}), 400
    if len(password) < 6:
        return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400
    if Usuario.query.filter_by(email=email).first():
        return jsonify({"error": "Ya existe una cuenta con ese email"}), 409

    nuevo = Usuario(
        nombre=nombre, email=email,
        telefono=data.get('telefono') or None,
        direccion=data.get('direccion') or None,
        estado=True,
    )
    nuevo.password = password
    db.session.add(nuevo)
    db.session.flush()

    rol_paciente = RolDetalle.query.filter_by(nombre_rol='paciente').first()
    if rol_paciente:
        db.session.add(UsuarioRol(
            usuario_id=nuevo.usuario_id,
            rol_id=rol_paciente.rol_id,
            asignado_por=nuevo.usuario_id,
            es_rol_principal=True,
        ))
    db.session.commit()

    return jsonify({
        "mensaje": "Registro exitoso",
        "usuario_id": nuevo.usuario_id
    }), 201