
import argparse
import demisto
import test_integration


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
        raise ValueError("You must provide server user & password arguments")

    c = demisto.DemistoClient(None, server, username, password)
    res = c.Login()
    if res.status_code is not 200:
        raise ValueError("Login has failed")

    integration_name = 'Cisco Umbrella Investigate'
    integration_params = {
        'Cisco Umbrella API token': '64267415-bf26-4434-900b-65f2ef6e06fa'
    }
    playbook_id = 'Cisco-Umbrella-Test'

    test_integration.test_integration(c, integration_name, integration_params, playbook_id)

if __name__ == '__main__':
    main()

# TODO - 1. use created instance in running pb (assume 1 instance is exists)
# TODO - 2. define all pbs, integrations & integrations params
# TODO - 3. configure sleep/timeout times
# TODO - 4. deployment:
#    a. keep integration params (secret) in circle-env
#    b. use demo5 to as server (keep in mind API key)
#    c. get branch content to demo 5 (copy it to res)

# get api key by login
# configure times/pb name/integration name/ integration params
        # replace secret with env variables
# managaer script
# upload file to investigation