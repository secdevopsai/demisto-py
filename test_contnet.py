
import argparse
import demisto
import time
import pprint


def options_handler():
    parser = argparse.ArgumentParser(description='Utility for batch action on incidents')
    parser.add_argument('-k', '--key', help='The API key to access the server', required=True)
    parser.add_argument('-s', '--server', help='The server URL to connect to', required=True)
    parser.add_argument('-n', '--name', help='Incident name', required=True)
    options = parser.parse_args()

    return options


# return true if succeed
def create_integration_instance(client, integration_name, integration_params):

    # get integration module-conf
    res = client.req('POST', '/settings/integration/search', {
        'page': 0, 'size': 50, 'query': 'name=' + integration_name #  TODO - fix query
    })

    res = res.json()
    all_configurations = res['configurations']
    match_configurations = [x for x in all_configurations if x['name'] == integration_name]

    if not match_configurations or len(match_configurations) == 0:
        print 'integration was not found'
        return False

    configuration = match_configurations[0]
    # define instance params in integration params
    module_configuration = configuration['configuration']

    module_instance = {
        'brand': configuration['id'],
        'category': configuration['category'],
        'configuration': configuration,
        'data': [],
        'enabled': "true",
        'engine': '',
        'id': '',
        'isIntegrationScript': True,
        'name': integration_name + '_test',
        'passwordProtected': False,
        'version': 1  # TODO - how to handle this
    }

    for param_conf in module_configuration:
        if param_conf['name'] in integration_params:
            param_conf['value'] = integration_params[param_conf['name']]
            param_conf['hasvalue'] = True
        elif param_conf['required'] is True:
            param_conf['value'] = param_conf['defaultValue']
        module_instance['data'].append(param_conf)

    # create instance
    #pprint.pprint(integration[0]['configuration'])

    res = client.req('PUT', '/settings/integration', module_instance)


    create_res = res.json()


    pprint.pprint(create_res)
    return False


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


def get_investigation_playbook_state(client, inv_id):
    res = client.req('GET', '/inv-playbook/' + inv_id, {})
    investigation_playbook = res.json()

    return investigation_playbook['state']


def main():
    options = options_handler()
    c = demisto.DemistoClient(options.key, options.server)

    integration_name = 'Cisco Umbrella Investigate'
    integration_params = {
        'APIToken': '64267415-bf26-4434-900b-65f2ef6e06fa'
    }

    # create integration instance
    ok = create_integration_instance(c, integration_name, integration_params)

    if not ok:
        print 'return'
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

    print 'finished'

if __name__ == '__main__':
    main()