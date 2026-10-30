# app/api/alertas.py
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import Alerta
from app.utils.decorators import roles_required

alertas_bp = Blueprint('alertas', __name__)

def _alerta_to_dict(a):
    return {
        "alerta_id": a.alerta_id,
        "paciente_id": a.paciente_id,
        "paciente_nombre": a.paciente.nombre if a.paciente else None,
        "tipo_signo_vital": a.tipo_signo_vital,
        "valor_registrado": float(a.valor_registrado) if a.valor_registrado is not None else None,
        "nivel_urgencia": a.nivel_urgencia,
        "mensaje": a.mensaje,
        "fecha_generacion": a.fecha_generacion.isoformat() if a.fecha_generacion else None,
        "fecha_resolucion": a.fecha_resolucion.isoformat() if a.fecha_resolucion else None,
        "resuelta_por": a.resuelta_por,
        "estado": a.estado,
        "accion_tomada": a.accion_tomada,
    }

@alertas_bp.route('/alertas', methods=['GET'])
@jwt_required()
def listar_alertas():
    """Admin/médico/enfermero ven todas; paciente ve solo las suyas."""
    uid = int(get_jwt_identity())
    from app.models import Usuario
    u = Usuario.query.get(uid)
    rol = u._get_rol_principal() if u else None

    query = Alerta.query
    if rol and rol.startswith('paciente'):
        query = query.filter_by(paciente_id=uid)
    # admin/médico/enfermero: sin filtro
    estado = request.args.get('estado')
    if estado:
        query = query.filter_by(estado=estado)

    alertas = query.order_by(Alerta.fecha_generacion.desc()).all()
    return jsonify([_alerta_to_dict(a) for a in alertas]), 200


@alertas_bp.route('/alertas/<int:alerta_id>/resolver', methods=['POST'])
@jwt_required()
@roles_required('administrador_sistema', 'medico_', 'enfermero_')
def resolver_alerta(alerta_id):
    a = Alerta.query.get(alerta_id)
    if not a:
        return jsonify({"error": "Alerta no encontrada"}), 404
    if a.estado == 'resuelta':
        return jsonify({"error": "La alerta ya está resuelta"}), 400

    data = request.get_json(silent=True) or {}
    a.estado = 'resuelta'
    a.fecha_resolucion = datetime.utcnow()
    a.resuelta_por = int(get_jwt_identity())
    a.accion_tomada = data.get('accion') or a.accion_tomada
    db.session.commit()
    return jsonify(_alerta_to_dict(a)), 200