#!/usr/bin/env python3
import time
import os
from lib.jenkins.client import JenkinsClient
from lib.jenkins.servicemanager import ServiceManager as JenkinsServiceManager

JENKINS_DEPLOY_JOB_NAME = 'deploy-primestox-prod'


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


def create_jenkins_client(jenkins_server_ip):
    deployer_password = os.environ['JENKINS_DEPLOYER_PASSWORD']
    return JenkinsClient(
        ip=jenkins_server_ip,
        user='deployer',
        password=deployer_password
    )


def main():
    jenkins_service_manager = JenkinsServiceManager()

    print("Starting Jenkins instance")
    jenkins_service_manager.start_server()

    print("Jenkins instance running on https://%s" %
          jenkins_service_manager.get_ip())

    print('Pinging if Jenkins app is ready and running')
    jenkins_service_manager.wait_until_ready()

    print("\nReady to go, running deploy job")
    run_deploy_job(create_jenkins_client(jenkins_service_manager.get_ip()))

    print('Stopping Jenkins instance...')
    jenkins_service_manager.stop_server()


if __name__ == '__main__':
    main()
