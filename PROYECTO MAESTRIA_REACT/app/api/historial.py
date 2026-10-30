# app/api/historial.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import HistorialClinico, Usuario, Notificacion
from app.utils.decorators import roles_required, owner_or_roles

historial_bp = Blueprint('historial', __name__)

def _entrada_to_dict(e):
    return {
        "historial_id": e.historial_id,
        "paciente_id": e.paciente_id,
        "paciente_nombre": e.paciente.nombre if e.paciente else None,
        "tipo_entrada": e.tipo_entrada,
        "titulo": e.titulo,
        "descripcion": e.descripcion,
        "archivo_url": e.archivo_url,
        "profesional_id": e.profesional_id,
        "profesional_nombre": e.profesional.nombre if e.profesional else None,
        "fecha_creacion": e.fecha_creacion.isoformat() if e.fecha_creacion else None,
        "es_urgente": e.es_urgente,
        "categoria": e.categoria,
        "nivel_confidencialidad": e.nivel_confidencialidad,
    }

@historial_bp.route('/pacientes/<int:paciente_id>/historial', methods=['GET'])
@jwt_required()
@owner_or_roles('administrador_sistema', 'medico_', 'enfermero_',
                id_param='paciente_id')
def listar_historial(paciente_id):
    entradas = HistorialClinico.consulta_por_paciente(paciente_id)
    return jsonify([_entrada_to_dict(e) for e in entradas]), 200


@historial_bp.route('/pacientes/<int:paciente_id>/historial', methods=['POST'])
@jwt_required()
@roles_required('administrador_sistema', 'medico_')
def crear_entrada(paciente_id):
    if not Usuario.query.get(paciente_id):
        return jsonify({"error": "Paciente no encontrado"}), 404

    data = request.get_json(silent=True) or {}
    tipos_validos = {'diagnostico', 'medicamento', 'antecedente', 'laboratorio', 'evolucion'}
    if data.get('tipo_entrada') not in tipos_validos:
        return jsonify({"error": "tipo_entrada inválido"}), 400

    titulo = (data.get('titulo') or '').strip()
    if not titulo:
        return jsonify({"error": "El título es obligatorio"}), 400

    uid = int(get_jwt_identity())
    entrada = HistorialClinico(
        paciente_id=paciente_id,
        tipo_entrada=data['tipo_entrada'],
        titulo=titulo,
        descripcion=data.get('descripcion'),
        archivo_url=data.get('archivo_url'),
        profesional_id=uid,
        es_urgente=bool(data.get('es_urgente', False)),
        categoria=data.get('categoria'),
        nivel_confidencialidad=data.get('nivel_confidencialidad', 'medio'),
    )
    db.session.add(entrada)
    db.session.flush()

    # Si es urgente, notificar al paciente (equivalente al SP original)
    if entrada.es_urgente:
        db.session.add(Notificacion(
            usuario_id=paciente_id,
            titulo='Nueva entrada urgente en historial',
            mensaje=f'Se ha registrado una entrada urgente: {titulo}',
            tipo='alerta',
            prioridad='urgente',
            url_destino=f'/historial/{entrada.historial_id}',
        ))

    db.session.commit()
    return jsonify(_entrada_to_dict(entrada)), 201