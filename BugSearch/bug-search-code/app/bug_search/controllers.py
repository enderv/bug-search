__author__ = 'Chris'
from flask import Blueprint, request
from flask.ext.restplus import Api, Resource, fields
from app.common.elastic_help import ElasticSearch
from app.common.bug import clean_bug_data
from app import api, app

#TODO make this config load projects and create client for each!
search_clients = {}
for project in app.config['PROJECTS']:
    search_clients[project] = ElasticSearch(index=project, hosts=app.config['ELASTIC_SEARCH_HOST'], doc_type=app.config['DOC_TYPE'])

bug_search_module = Blueprint('bug_search_module', __name__, url_prefix='/bug')
bug_search_module_api = Api(bug_search_module)

bug_parser = api.parser()
bug_parser.add_argument('title', type=str, required=True, help='Bug Title', location='form')
bug_parser.add_argument('description', type=str, required=True, help='Bug Description', location='form')


@api.doc(responses={404: 'Not found'}, params={'bug_id': 'The Bug ID'})
class GeneralBug(Resource):
    @api.doc(description='Will do a general bug search bug_id should be a string', responses={200: 'Found'})
    def get(self, bug_id):
        bug = search_clients['bug'][bug_id]
        if not bug:
            return 'Not found', 404
        else:
            return bug, 200
    @api.doc(description='Will create a searchable bug not tied to a project', responses={201: 'Created'}, parser=bug_parser)
    def post(self, bug_id):
        try:
            json_data = request.get_json(force=True)
            search_clients['bug'][bug_id] = clean_bug_data(json_data)
            return '', 201
        except:
           return 'Error Saving', 409

@api.doc(responses={404: 'Not found'}, params={'bug_id': 'The Bug ID', 'project':"Project Name predefined in config currently"})
class ProjectBug(Resource):

    @api.doc(description='Will GET a bug by project and ID ', responses={200: 'Bug'})
    def get(self, project, bug_id):
        if project not in app.config['PROJECTS']:
            return 'Project Not defined', 409
        bug = search_clients[project][bug_id]
        if not bug:
            return 'Not found', 404
        else:
            return bug, 200

    @api.doc(description='Will create a searchable bug tied to the project', responses={201: 'Created', 409: 'Project Not defined', 500: 'Server Error'},
             parser=bug_parser)
    def post(self, project, bug_id):
        if project not in app.config['PROJECTS']:
            return 'Project Not defined', 409
        try:
            json_data = request.get_json(force=True)
            search_clients[project][bug_id] = clean_bug_data(json_data)
            return '', 201
        except:
            return 'Error Saving', 500


#Parser for the next few calls
parser = api.parser()
parser.add_argument('field', type=str, required=False, help='Field to query', location='args')

class GeneralBugSearch(Resource):
    @api.doc(description='Will search title description without project specified ', responses={200: 'Bug'}, parser=parser)
    def get(self, query):
        args = parser.parse_args()
        if not args['field']:
            results = search_clients['bug'].search_fields(['title', 'description'], query)
        else:
            results = search_clients['bug'].search_field(request.args.get('field'), query)

        if len(results) == 0:
            return 'Not Found', 404
        else:
            return results, 200

class ProjectBugSearch(Resource):
    @api.doc(description='Will search title description without project specified ', responses={200: 'Bug'}, parser=parser)
    def get(self, project, query):
        args = parser.parse_args()
        if not args['field']:
            results = search_clients[project].search_fields(['title', 'description'], query, index=project)
        else:
            results = search_clients[project].search_field(args['field'], query, index=project)

        if len(results) == 0:
            return 'Not Found', 404
        else:
            return results, 200

bug_search_module_api.add_resource(GeneralBug, '/<string:bug_id>')
bug_search_module_api.add_resource(ProjectBug, '/<string:project>/<string:bug_id>')
bug_search_module_api.add_resource(GeneralBugSearch, '/search/<string:query>')
bug_search_module_api.add_resource(ProjectBugSearch, '/search/<string:project>/<string:query>')
