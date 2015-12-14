__author__ = 'Chris'
import os
import sys

from flask import Flask, Blueprint


#To fix imports below Sometimes this is needed
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
from flask_restful import Api

app = Flask(__name__)
api_bp = Blueprint('api', __name__)

if os.environ['PYTHON_ENV'] == 'local':
    app.config.from_object('config.LocalConfig')
else:
    app.config.from_object('config.DockerConfig')
api = Api(api_bp)

simple_page = Blueprint('simple_page', __name__,
                        template_folder='templates')
@simple_page.route('/')
def hello_world():
    return 'Hello World!'

from app.bug_search.controllers import bug_search_module

app.register_blueprint(bug_search_module)

if __name__ == '__main__':
    app.run()
