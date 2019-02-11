import http.client
import ssl
import json
from base64 import b64encode


class JenkinsClient(object):
    def __init__(self, ip, user, password):
        self.ip = ip
        self.user = user
        self.password = password

    def execute_job(self, job_name):
        conn = self._create_http_transport()
        headers = {'Authorization': 'Basic %s' % self.basic_auth_header()}
        conn.request("POST", "/job/%s/build" % job_name, headers=headers)

        res = conn.getresponse()

        if res.status == 201:
            return True

        raise Exception("Jenkins deploy kick of failed with http status %s"
                        % res.status)

    def get_last_job_status(self, job_name):
        conn = self._create_http_transport()
        headers = {'Authorization': 'Basic %s' % self.basic_auth_header()}
        conn.request("GET", "/job/%s/lastBuild/api/json" % job_name,
                            headers=headers)
        response = conn.getresponse().read()
        return json.loads(response)['result']

    def basic_auth_header(self):
        user_token_raw = "%s:%s" % (self.user, self.password)
        return b64encode(user_token_raw.encode()).decode("ascii")

    def _create_http_transport(self):
        return http.client.HTTPSConnection(
          self.ip,
          context=ssl._create_unverified_context()
        )
