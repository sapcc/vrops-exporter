from flask import Blueprint, request, make_response
from mockingServer.modules.RequestHandler import RequestHandler
import json
# import master_password

authBluePrint = Blueprint('AuthenticationService', import_name=__name__)


class Authentication(RequestHandler):
    def __init__(self):
        super().__init__()
        self.username = "Mocking"
        self.password = "Server"
        self.url = '127.0.0.1'

    def post(self):
        if not self.login():
            return make_response('Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
        return self.session_id

    def delete(self):
        return make_response('Success', 200)

    def login(self):
        auth = json.loads(request.data.decode())
        if auth and self.check_auth(auth['username'], auth['password']):
            return True
        return False

    def check_auth(self, username, password):
        if username == self.username and password == self.password:
            return True
        return False


authBluePrint.add_url_rule('/suite-api/api/auth/token/acquire', view_func=Authentication.as_view('Authentication'))
