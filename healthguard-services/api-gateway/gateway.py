# gateway.py
import os
import httpx
from flask import Flask, request, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

AUTH_URL = os.getenv('AUTH_URL', 'http://localhost:5001')
CLINICAL_URL = os.getenv('CLINICAL_URL', 'http://localhost:5002')

def _proxy(base_url):
    # Construye la URL destino (incluye query string si lo hay)
    url = base_url + request.full_path.rstrip('?')
    
    # Prepara los headers (quitando el host original)
    headers = {k: v for k, v in request.headers if k.lower() not in ('host', 'content-length')}
    
    try:
        # Reenvía la petición al microservicio correspondiente
        r = httpx.request(
            method=request.method,
            url=url,
            headers=headers,
            content=request.get_data(),
            timeout=30.0,
        )
        # Devuelve la respuesta al cliente
        return Response(
            r.content,
            status=r.status_code,
            headers=[(k, v) for k, v in r.headers.items()
                     if k.lower() not in ('content-encoding', 'transfer-encoding', 'connection')]
        )
    except httpx.RequestError as e:
        return Response(
            f'{{"error":"gateway error: no se pudo conectar a {base_url}"}}',
            status=502, mimetype='application/json'
        )

# Rutas para Auth Service (usa <path:subpath> en vez de <path:_>)
@app.route('/api/auth/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
@app.route('/api/auth', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def proxy_auth(subpath=''):
    return _proxy(AUTH_URL)

# Rutas para Clinical Service
@app.route('/api/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
@app.route('/api', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def proxy_clinical(subpath=''):
    return _proxy(CLINICAL_URL)

if __name__ == '__main__':
    print("Iniciando API Gateway en http://localhost:5000...")
    print(f"-> /api/auth/* redirige a {AUTH_URL}")
    print(f"-> /api/* redirige a {CLINICAL_URL}")
    app.run(host='0.0.0.0', port=5000, debug=True)