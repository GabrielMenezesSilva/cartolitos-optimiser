from app.main import app as fastapi_app
from a2wsgi import ASGIMiddleware
import flask
from werkzeug.wrappers import Response

wsgi_app = ASGIMiddleware(fastapi_app)

flask_app = flask.Flask(__name__)

@flask_app.route('/', defaults={'path': ''}, methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
@flask_app.route('/<path:path>', methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
def catch_all(path):
    response = Response.from_app(wsgi_app, flask.request.environ)
    return flask.Response(response.get_data(), status=response.status_code, headers=dict(response.headers))

if __name__ == "__main__":
    flask_app.run(port=8081)
