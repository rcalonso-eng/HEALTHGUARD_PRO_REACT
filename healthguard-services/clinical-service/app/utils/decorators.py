from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def roles_required(*nombres_roles):
    """Permite solo a los roles indicados. Acepta prefijos terminados en '_'."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            rol = claims.get('rol')
            if rol is None:
                return jsonify({"error": "Sin rol en el token"}), 403
            permitido = any(
                rol == r or (r.endswith('_') and rol.startswith(r))
                for r in nombres_roles
            )
            if not permitido:
                return jsonify({"error": "No autorizado para este rol"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def owner_or_roles(*nombres_roles, id_param='paciente_id'):
    """Permite si el usuario es el dueño del recurso o tiene uno de los roles."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            uid = str(claims.get('sub'))
            owner = kwargs.get(id_param)
            if str(uid) == str(owner):
                return fn(*args, **kwargs)
            rol = claims.get('rol')
            if rol and any(rol == r or (r.endswith('_') and rol.startswith(r))
                           for r in nombres_roles):
                return fn(*args, **kwargs)
            return jsonify({"error": "No autorizado"}), 403
        return wrapper
    return decorator


def permiso_required(nombre_permiso):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            permisos = get_jwt().get('permisos', [])
            if nombre_permiso not in permisos:
                return jsonify({"error": f"Falta permiso: {nombre_permiso}"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator