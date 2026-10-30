# app/api/pacientes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import Usuario, RolDetalle, UsuarioRol
from app.utils.decorators import roles_required

pacientes_bp = Blueprint('pacientes', __name__)

def _paciente_to_dict(u):
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
    }

def _query_pacientes():
    return (
        db.session.query(Usuario)
        .join(UsuarioRol, Usuario.usuario_id == UsuarioRol.usuario_id)
        .join(RolDetalle, UsuarioRol.rol_id == RolDetalle.rol_id)
        .filter(RolDetalle.nombre_rol.like('paciente%'), Usuario.estado == True)
        .order_by(Usuario.nombre)
    )

@pacientes_bp.route('/pacientes', methods=['GET'])
@jwt_required()
@roles_required('administrador_sistema', 'medico_', 'enfermero_')
def listar_pacientes():
    pacientes = _query_pacientes().all()
    return jsonify([_paciente_to_dict(u) for u in pacientes]), 200


@pacientes_bp.route('/pacientes', methods=['POST'])
@jwt_required()
@roles_required('administrador_sistema')
def crear_paciente():
    data = request.get_json(silent=True) or {}
    nombre = (data.get('nombre') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not nombre or not email or not password:
        return jsonify({"error": "Nombre, email y contraseña son obligatorios"}), 400
    if len(password) < 6:
        return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400
    if Usuario.query.filter_by(email=email).first():
        return jsonify({"error": "Ya existe un usuario con ese email"}), 409

    nuevo = Usuario(
        nombre=nombre, email=email,
        telefono=data.get('telefono') or None,
        direccion=data.get('direccion') or None,
        codigo_postal=data.get('codigo_postal') or None,
        genero=data.get('genero') or None,
        estado=True,
    )
    nuevo.password = password
    db.session.add(nuevo)
    db.session.flush()

    rol = RolDetalle.query.filter_by(nombre_rol='paciente').first()
    if rol:
        uid_admin = int(get_jwt_identity())
        db.session.add(UsuarioRol(
            usuario_id=nuevo.usuario_id,
            rol_id=rol.rol_id,
            asignado_por=uid_admin,
            es_rol_principal=True,
        ))
    db.session.commit()
    return jsonify(_paciente_to_dict(nuevo)), 201


@pacientes_bp.route('/pacientes/<int:paciente_id>', methods=['GET'])
@jwt_required()
@roles_required('administrador_sistema', 'medico_', 'enfermero_')
def obtener_paciente(paciente_id):
    u = Usuario.query.get(paciente_id)
    if not u:
        return jsonify({"error": "Paciente no encontrado"}), 404
    return jsonify(_paciente_to_dict(u)), 200


@pacientes_bp.route('/pacientes/<int:paciente_id>', methods=['PUT'])
@jwt_required()
@roles_required('administrador_sistema', 'medico_')
def actualizar_paciente(paciente_id):
    u = Usuario.query.get(paciente_id)
    if not u:
        return jsonify({"error": "Paciente no encontrado"}), 404
    data = request.get_json(silent=True) or {}

    for campo in ('nombre', 'telefono', 'direccion', 'codigo_postal', 'genero'):
        if campo in data:
            setattr(u, campo, data[campo])
    if data.get('password'):
        if len(data['password']) < 6:
            return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400
        u.password = data['password']
    if 'estado' in data:
        u.estado = bool(data['estado'])

    db.session.commit()
    return jsonify(_paciente_to_dict(u)), 200


@pacientes_bp.route('/pacientes/<int:paciente_id>', methods=['DELETE'])
@jwt_required()
@roles_required('administrador_sistema')
def desactivar_paciente(paciente_id):
    u = Usuario.query.get(paciente_id)
    if not u:
        return jsonify({"error": "Paciente no encontrado"}), 404
    u.estado = False
    db.session.commit()
    return jsonify({"mensaje": "Paciente desactivado"}), 200