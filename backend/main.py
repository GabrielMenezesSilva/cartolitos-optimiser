from firebase_functions import https_fn, options
from a2wsgi import ASGIMiddleware
from app.main import app as fastapi_app
import flask
from werkzeug.wrappers import Response
import firebase_admin

# Inicializa o admin apenas se não estiver inicializado
try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app()

# 1. Converte ASGI (FastAPI) para WSGI
wsgi_app = ASGIMiddleware(fastapi_app)

# 2. Cria um App Flask para intermediar a Cloud Function
flask_app = flask.Flask(__name__)

@flask_app.route('/', defaults={'path': ''}, methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
@flask_app.route('/<path:path>', methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
def catch_all(path):
    response = Response.from_app(wsgi_app, flask.request.environ)
    return flask.Response(response.get_data(), status=response.status_code, headers=dict(response.headers))

# 3. Exporta a Firebase Cloud Function em 'api'
@https_fn.on_request(region="southamerica-east1", cors=options.CorsOptions(cors_origins="*", cors_methods=["GET", "POST", "OPTIONS"]))
def api(req: https_fn.Request) -> https_fn.Response:
    with flask_app.request_context(req.environ):
        return flask_app.full_dispatch_request()
