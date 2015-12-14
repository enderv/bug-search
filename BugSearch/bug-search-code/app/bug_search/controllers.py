__author__ = 'Chris'
from flask import Blueprint, request
from flask_restful import Api, Resource
from app.common.elastic_help import ElasticSearch
from app.common.bug import clean_bug_data
from app import app

#TODO make this config load projects and create client for each!
search_clients = {}
for project in app.config['PROJECTS']:
    search_clients[project] = ElasticSearch(index=project, hosts=app.config['ELASTIC_SEARCH_HOST'], doc_type=app.config['DOC_TYPE'])

bug_search_module = Blueprint('bug_search_module', __name__, url_prefix='/bug')
bug_search_module_api = Api(bug_search_module)
# Set the route and accepted methods

class GeneralBug(Resource):
    def get(self, bug_id):
        bug = search_clients['bug'][bug_id]
        if not bug:
            return 'Not found', 404
        else:
            return bug, 200

    def post(self, bug_id):
        try:
            json_data = request.get_json(force=True)
            search_clients['bug'][bug_id] = clean_bug_data(json_data)
            return '', 201
        except:
           return 'Error Saving', 409

class ProjectBug(Resource):
    def get(self, project, bug_id):
        if project not in app.config['PROJECTS']:
            return 'Project Not defined', 409
        bug = search_clients[project][bug_id]
        if not bug:
            return 'Not found', 404
        else:
            return bug, 200

    def post(self, project, bug_id):
        if project not in app.config['PROJECTS']:
            return 'Project Not defined', 409
        try:
            json_data = request.get_json(force=True)
            search_clients[project][bug_id] = clean_bug_data(json_data)
            return '', 201
        except:
            return 'Error Saving', 409


class GeneralBugSearch(Resource):
    #TODO add argpaser
    def get(self, query):
        if not request.args.get('field'):
            results = search_clients['bug'].search_fields(['title', 'description'], query)
        else:
            results = search_clients['bug'].search_field(request.args.get('field'), query)

        if len(results) == 0:
            return 'Not Found', 404
        else:
            return results, 200

class ProjectBugSearch(Resource):
    #TODO add argpaser
    def get(self, project, query):
        if not request.args.get('field'):
            results = search_clients[project].search_fields(['title', 'description'], query, index=project)
        else:
            results = search_clients[project].search_field(request.args.get('field'), query, index=project)

        if len(results) == 0:
            return 'Not Found', 404
        else:
            return results, 200

bug_search_module_api.add_resource(GeneralBug, '/<string:bug_id>')
bug_search_module_api.add_resource(ProjectBug, '/<string:project>/<string:bug_id>')
bug_search_module_api.add_resource(GeneralBugSearch, '/search/<string:query>')
bug_search_module_api.add_resource(ProjectBugSearch, '/search/<string:project>/<string:query>')
