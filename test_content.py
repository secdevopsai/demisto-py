
import argparse
import demisto
import test_integration
import json


def options_handler():
    parser = argparse.ArgumentParser(description='Utility for batch action on incidents')
    parser.add_argument('-u', '--user', help='The username for the login')
    parser.add_argument('-p', '--password', help='The password for the login')
    parser.add_argument('-s', '--server', help='The server URL to connect to', required=True)
    options = parser.parse_args()

    return options


def main():
    options = options_handler()
    username = options.user
    password = options.password
    server = options.server

    if not (username and password and server):
        raise ValueError('You must provide server user & password arguments')

    c = demisto.DemistoClient(None, server, username, password)
    res = c.Login()
    if res.status_code is not 200:
        raise ValueError("Login has failed")

    with open('./conf.json') as data_file:
        conf = json.load(data_file)

    integrations = conf['integrations']
    if not integrations or len(integrations) is 0:
        print 'no integrations are configured for test'
    for integration in integrations:
        test_options = {
            'timeout': integration['timeout'] if 'timeout' in integration else conf['testTimeout'],
            'interval': conf['testInterval']
        }
        test_integration.test_integration(c, integration['name'], integration['params'], integration['playbookID'],
                                          test_options)


if __name__ == '__main__':
    main()
