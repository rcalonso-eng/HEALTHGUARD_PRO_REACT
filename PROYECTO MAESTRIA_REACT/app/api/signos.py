from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import text
from app.extensions import db
from app.models import SignoVital, Usuario
from app.utils.decorators import owner_or_roles, roles_required

signos_bp = Blueprint('signos', __name__)

def _signo_to_dict(s):
    return {
        "signo_vital_id": s.signo_vital_id,
        "paciente_id": s.paciente_id,
        "glucosa": float(s.glucosa) if s.glucosa is not None else None,
        "presion_sistolica": s.presion_sistolica,
        "presion_diastolica": s.presion_diastolica,
        "peso": float(s.peso) if s.peso is not None else None,
        "frecuencia_cardiaca": s.frecuencia_cardiaca,
        "oxigenacion": float(s.oxigenacion) if s.oxigenacion is not None else None,
        "tipo_registro": s.tipo_registro,
        "fecha_registro": s.fecha_registro.isoformat() if s.fecha_registro else None,
        "observaciones": s.observaciones,
    }

@signos_bp.route('/pacientes/<int:paciente_id>/signos', methods=['GET'])
@jwt_required()
@owner_or_roles('administrador_sistema', 'medico_', 'enfermero_',
                id_param='paciente_id')
def listar_signos(paciente_id):
    signos = SignoVital.consulta_por_paciente(paciente_id)
    return jsonify([_signo_to_dict(s) for s in signos]), 200


@signos_bp.route('/pacientes/<int:paciente_id>/signos', methods=['POST'])
@jwt_required()
@roles_required('administrador_sistema', 'medico_', 'enfermero_')
def crear_signo(paciente_id):
    data = request.get_json(silent=True) or {}

    # Valida que el paciente exista
    if not Usuario.query.get(paciente_id):
        return jsonify({"error": "Paciente no encontrado"}), 404

    # Llama al procedimiento almacenado existente
    uid = int(get_jwt_identity())
    try:
        db.session.execute(
            text("""CALL sp_registrar_signos_sin_transaccion(
                :pid, :glu, :sis, :dia, :peso, :fc, :oxi,
                :tipo, :obs, :uid
            )"""),
            {
                "pid": paciente_id,
                "glu": data.get('glucosa'),
                "sis": data.get('presion_sistolica'),
                "dia": data.get('presion_diastolica'),
                "peso": data.get('peso'),
                "fc": data.get('frecuencia_cardiaca'),
                "oxi": data.get('oxigenacion'),
                "tipo": data.get('tipo_registro', 'manual'),
                "obs": data.get('observaciones'),
                "uid": uid,
            }
        )
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

    return jsonify({"mensaje": "Signo vital registrado"}), 201