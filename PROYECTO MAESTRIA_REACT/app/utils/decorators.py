from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models import Usuario
from app.extensions import db

def _get_user():
    uid = get_jwt_identity()
    return Usuario.query.get(int(uid))

def roles_required(*nombres_roles):
    """Permite solo a los roles indicados (por prefijo si termina en '_')."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = _get_user()
            if not user or not user.estado or user.cuenta_bloqueada:
                return jsonify({"error": "Usuario no válido"}), 403
            rol = user._get_rol_principal()
            if rol is None:
                return jsonify({"error": "Sin rol asignado"}), 403
            # Coincidencia exacta o por prefijo (ej. 'medico_')
            permitido = any(
                rol == r or (r.endswith('_') and rol.startswith(r))
                for r in nombres_roles
            )
            if not permitido:
                return jsonify({"error": "No autorizado para este rol"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def permiso_required(nombre_permiso):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = _get_user()
            if not user or not user.tiene_permiso(nombre_permiso):
                return jsonify({"error": f"Falta permiso: {nombre_permiso}"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def owner_or_roles(*nombres_roles, id_param='paciente_id'):
    """Permite el acceso si el usuario autenticado es el dueño del recurso
    o tiene uno de los roles indicados."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = _get_user()
            if not user:
                return jsonify({"error": "No autenticado"}), 401
            owner_id = kwargs.get(id_param)
            if str(user.usuario_id) == str(owner_id):
                return fn(*args, **kwargs)
            rol = user._get_rol_principal()
            if rol and any(rol == r or (r.endswith('_') and rol.startswith(r))
                           for r in nombres_roles):
                return fn(*args, **kwargs)
            return jsonify({"error": "No autorizado"}), 403
        return wrapper
    return decorator