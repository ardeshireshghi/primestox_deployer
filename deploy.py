#!/usr/bin/env python3

import socket
import time
import os
import http.client
import ssl
from lib.aws.ec2 import client as ec2_client
from lib.jenkins.client import JenkinsClient


JENKINS_DEPLOY_JOB_NAME = 'deploy-primestox-prod'


def create_socket():
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def check_jenkins_up(server_ip):
    sock = create_socket()
    result = sock.connect_ex((server_ip, 443))
    print('.', end='', flush=True)

    if result == 0:
        conn = http.client.HTTPSConnection(
          server_ip,
          context=ssl._create_unverified_context()
        )

        conn.request('GET', '/')
        res = conn.getresponse()

        if res.status == 503:
            time.sleep(10)
            return check_jenkins_up(server_ip)
        return True
    else:
        time.sleep(10)
        return check_jenkins_up(server_ip)


def jenkins_instance_name():
    return 'build-deploy-server-jenkins'


def jenkins_ec2_instance(client=None):
    ec2 = client if client else ec2_client()
    instances = ec2.instances.filter(
        Filters=[{'Name': 'tag:Name', 'Values': [jenkins_instance_name()]}])
    for instance in instances:
        return instance


def start_jenkins(instance):
    instance.start()
    instance.wait_until_running()


def run_deploy_job(jenkins_client):
    res = jenkins_client.execute_job(JENKINS_DEPLOY_JOB_NAME)
    if res:
        print('Jenkins deploy to LIVE kicked off...')
    time.sleep(10)

    while True:
        status = jenkins_client.get_last_job_status(JENKINS_DEPLOY_JOB_NAME)
        print("Jenkins deploy in progress, current state: %s" %
              status['result'])

        if status['result'] in ['FAILURE', 'SUCCESS']:
            print("Jenkins deploy to LIVE finished with %s" % status['result'])
            print(status)
            break

        time.sleep(5)


def main():
    jenkins_instance = jenkins_ec2_instance()
    deployer_password = os.environ['JENKINS_DEPLOYER_PASSWORD']

    if jenkins_instance.state.get('Name') == 'stopped':
        print("Starting Jenkins instance")
        start_jenkins(jenkins_instance)

    instance_ip = jenkins_instance.public_ip_address
    print("Jenkins instance is running on https://%s" % instance_ip)

    print('Pinging if Jenkins app is running')
    check_jenkins_up(server_ip=instance_ip)

    print("\nReady to go, running deploy job")

    jenkins_client = JenkinsClient(
        ip=instance_ip,
        user='deployer',
        password=deployer_password
    )
    run_deploy_job(jenkins_client)

    print('Stopping Jenkins instance...')
    jenkins_instance.stop()


if __name__ == '__main__':
    main()
