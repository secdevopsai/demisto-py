
import argparse
import demisto
import time
import pprint
import uuid
import urllib


def options_handler():
    parser = argparse.ArgumentParser(description='Utility for batch action on incidents')
    parser.add_argument('-k', '--key', help='The API key to access the server', required=True)
    parser.add_argument('-s', '--server', help='The server URL to connect to', required=True)
    parser.add_argument('-n', '--name', help='Incident name', required=True)
    options = parser.parse_args()

    return options


# return instance name if succeed, None otherwise
def create_integration_instance(client, integration_name, integration_params):

    # get integration module-conf
    res = client.req('POST', '/settings/integration/search', {
        'page': 0, 'size': 200, 'query': 'name=' + integration_name  # TODO - fix query
    })

    res = res.json()
    all_configurations = res['configurations']
    match_configurations = [x for x in all_configurations if x['name'] == integration_name]

    if not match_configurations or len(match_configurations) == 0:
        print 'integration was not found'
        return False

    configuration = match_configurations[0]
    module_configuration = configuration['configuration']

    instance_name = integration_name + '_test' + str(uuid.uuid4())
    # define module instance
    module_instance = {
        'brand': configuration['name'],
        'category': configuration['category'],
        'configuration': configuration,
        'data': [],
        'enabled': "true",
        'engine': '',
        'id': '',
        'isIntegrationScript': True,
        'name': instance_name,
        'passwordProtected': False,
        'version': 0
    }

    # set module params
    for param_conf in module_configuration:
        if param_conf['name'] in integration_params:
            # param defined by user
            param_conf['value'] = integration_params[param_conf['name']]
            param_conf['hasvalue'] = True
        elif param_conf['required'] is True:
            # param is required - take default falue
            param_conf['value'] = param_conf['defaultValue']
        module_instance['data'].append(param_conf)

    res = client.req('PUT', '/settings/integration', module_instance)

    if res.status_code == 200:
        return instance_name
    else:
        print 'create instance failed with status code ' + str(res.status_code)
        pprint.pprint(res.json())
        return None


# create incident with given name & playbook, and then fetch & return the incident
def create_incident_with_playbook(client, name, playbook_id):
    # create incident
    kwargs = {'createInvestigation': True, 'playbookId': playbook_id}
    r = client.CreateIncident(name, None, None, None, None,
                         None, None, **kwargs)
    response_json = r.json()
    inc_id = response_json['id']

    # wait for incident to be created
    time.sleep(1)

    # get incident
    incidents = client.SearchIncidents(0, 50, 'id:' + inc_id)

    if incidents['total'] != 1:
        print 'failed to get incident with id:' + inc_id
        return

    return incidents['data'][0]


# returns current investigation playbook state - 'inprogress'/'failed'/'completed'
def get_investigation_playbook_state(client, inv_id):
    res = client.req('GET', '/inv-playbook/' + inv_id, {})
    investigation_playbook = res.json()

    return investigation_playbook['state']


# return True if delete-incident succeeded, False otherwise
def delete_incident(client, incident):
    res = client.req('POST', '/incident/batchDelete', {
        'ids': [incident['id']],
        'filter': {},
        'all': False
    })

    if res.status_code is not 200:
        print 'delete incident failed\nStatus code' + str(res.status_code)
        pprint.pprint(res.json())
        return False
    return True


# return True if delete-integration-instance succeeded, False otherwise
def delete_integration_instance(client, instance_name):
    res = client.req('DELETE', '/settings/integration/' + urllib.quote(instance_name), {})
    if res.status_code is not 200:
        print 'delete integration instance failed\nStatus code' + str(res.status_code)
        pprint.pprint(res.json())
        return False
    return True


# 1. create integration instance
# 2. create incident with playbook
# 3. wait for playbook to finish run
# 4. delete incident
# 5. delete instance
def main():
    options = options_handler()
    c = demisto.DemistoClient(options.key, options.server)

    integration_name = 'Cisco Umbrella Investigate'
    integration_params = {
        'APIToken': '64267415-bf26-4434-900b-65f2ef6e06fa'
    }

    # create integration instance
    instance_name = create_integration_instance(c, integration_name, integration_params)

    if not instance_name:
        print 'failed to create instance'
        return

    # create incident with playbook
    playbook_id = 'Cisco-Umbrella-Test'
    incident = create_incident_with_playbook(c, options.name, playbook_id)

    investigation_id = incident['investigationId']
    if investigation_id is None or len(investigation_id) == 0:
        print 'failed to get investigation id of incident:' + incident
        return

    print 'waiting for incident creation'
    time.sleep(0.2)

    timeout_amount = 3 * 10  # 30 seconds from now
    timeout = time.time() + timeout_amount

    interval = 0.10
    i = 1

    # wait for playbook to finish run
    while True:
        # give playbook time to run
        time.sleep(interval)

        # fetch status
        playbook_state = get_investigation_playbook_state(c, investigation_id)

        if playbook_state == 'completed':
            print 'Playbook ' + playbook_id + ' succeed'
            break
        if playbook_state == 'failed':
            print 'Playbook ' + playbook_id + ' failed'
            break
        if time.time() > timeout:
            print 'Playbook ' + playbook_id + ' timeout failure'
            break

        print 'loop no.' + str(i) + ', state is ' + playbook_state
        i = i + 1

    # delete incident
    delete_incident(c, incident)

    # delete integration instance
    delete_integration_instance(c, instance_name)

    print 'finished'

if __name__ == '__main__':
    main()

# TODO - 1. use created instance in running pb (assume 1 instance is exists)
# TODO - 2. define all pbs, integrations & integrations params
# TODO - 3. configure sleep/timeout times
# TODO - 4. deployment:
#    a. keep integration params (secret) in circle-env
#    b. use demo5 to as server (keep in mind API key)
#    c. get branch content to demo 5 (copy it to res)


# replace integration params to display name
# get api key by login
# configure times/pb name/integration name/ integration params
        # replace secret with env variables
# managaer script
# upload file to investigation