from flask.views import MethodView
from flask import request


class RequestHandler(MethodView):
    def __init__(self):
        self.session_id = {'token': '779b8ede-1337-11eb-9581-3c58c27e75a6'}

    def check_token(self):
        auth_values = request.headers.get('Authorization').split(' ')
        if self.session_id['token'] not in auth_values:
            return False
        return True
