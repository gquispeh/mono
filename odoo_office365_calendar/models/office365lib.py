# See LICENSE file for full copyright and licensing details.
import json
import simplejson
import http.client as httplib
domain = 'graph.microsoft.com'


class Session:

    def Initialize(self, token):
        self.token = token


class Call:

    def makecall(self, request_type, request, vals):
        conn = httplib.HTTPSConnection('graph.microsoft.com')
        vals = json.dumps(vals)
        conn.request(request_type, "/v1.0/me/" + request, vals, headers={
            'Authorization': self.Session.token,
            'Content-Type': 'application/json'
        })
        if request_type == 'DELETE':
            return conn.getresponse()
        response = simplejson.loads(conn.getresponse().read())
        return json.dumps(response)


class Office365:

    Session = Session()

    def __init__(self, token):
        self.Session.Initialize(token)

    def makerequest(self, request, request_type, vals):
        api = Call()
        api.Session = self.Session
        return api.makecall(request, request_type, vals)
