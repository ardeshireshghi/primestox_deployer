import socket
import http.client
import ssl
import time

from ..aws.ec2 import client as ec2_client


def create_socket():
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM)


class ServiceManager(object):
    def __init__(self, instance=None, client=None):
        self.ec2 = client if client else ec2_client()
        self._instance = instance if instance else self.ec2_instance()

    def start_server(self):
        if self.ec2_instance().state.get('Name') == 'stopped':
            self._instance.start()
            self._instance.wait_until_running()

    def stop_server(self):
        self._instance.stop()

    def ec2_instance(self, client=None):
        if hasattr(self, '_instance'):
            return self._instance

        instances = self.ec2.instances.filter(
            Filters=[{'Name': 'tag:Name', 'Values': [self.instance_name()]}])
        for instance in instances:
            return instance

    def get_ip(self):
        return self._instance.public_ip_address

    def instance_name(self):
        return 'build-deploy-server-jenkins'

    def wait_until_ready(self):
        sock = create_socket()
        result = sock.connect_ex((self.get_ip(), 443))
        print('.', end='', flush=True)

        if result == 0:
            conn = http.client.HTTPSConnection(
              self.get_ip(),
              context=ssl._create_unverified_context()
            )

            conn.request('GET', '/')
            res = conn.getresponse()

            if res.status == 503:
                time.sleep(10)
                return self.wait_until_ready()
            return True
        else:
            time.sleep(10)
            return self.wait_until_ready()
