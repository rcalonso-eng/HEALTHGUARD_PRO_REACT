from flask import Flask, jsonify
from config import Config
from .extensions import db, jwt, cors

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}},
        supports_credentials=True,
    )

    from .api.pacientes import pacientes_bp
    from .api.signos import signos_bp
    from .api.alertas import alertas_bp
    from .api.historial import historial_bp

    for bp in (pacientes_bp, signos_bp, alertas_bp, historial_bp):
        app.register_blueprint(bp, url_prefix='/api')

    @jwt.user_identity_loader
    def user_identity_lookup(user):
        return str(user)

    @jwt.expired_token_loader
    def expired_token(_h, _p):
        return jsonify({"error": "Token expirado"}), 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return jsonify({"error": "Token inválido", "detalle": reason}), 422

    @jwt.unauthorized_loader
    def missing_token(reason):
        return jsonify({"error": "Token faltante", "detalle": reason}), 401

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"error": "Recurso no encontrado"}), 404

    @app.errorhandler(500)
    def server_error(_e):
        return jsonify({"error": "Error interno del servidor"}), 500

    return app