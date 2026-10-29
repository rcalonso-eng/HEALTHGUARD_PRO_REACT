import os
from datetime import timedelta

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://root:1234@127.0.0.1/healthguard_pro'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # MISMA clave que auth-service para que los tokens cruzen
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'cambia-esta-clave-en-produccion')
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')