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

    from .api.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api')

    @jwt.user_lookup_loader
    def user_lookup_callback(_h, jwt_data):
        from .models import Usuario
        return Usuario.query.get(int(jwt_data["sub"]))

    @jwt.user_identity_loader
    def user_identity_lookup(user):
        return str(user)

    @jwt.expired_token_loader
    def expired_token(_h, _p):
        return jsonify({"error": "Token expirado"}), 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return jsonify({"error": "Token inválido", "detalle": reason}), 422

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"error": "Recurso no encontrado"}), 404

    return app