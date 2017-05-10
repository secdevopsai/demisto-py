
import argparse
import demisto
import time


def options_handler():
    parser = argparse.ArgumentParser(description='Utility for batch action on incidents')
    parser.add_argument('-k', '--key', help='The API key to access the server', required=True)
    parser.add_argument('-s', '--server', help='The server URL to connect to', required=True)
    parser.add_argument('-n', '--name', help='Incident name', required=True)
    options = parser.parse_args()

    return options


# create incident with given name & playbook, and then fetch & return the incident
def create_incident_with_playbook(client, name, playbook_id):
    # create incident
    kwargs = {'createInvestigation': True, 'playbookId': playbook_id}
    r = client.CreateIncident(name, None, None, None, None,
                         None, None, **kwargs)
    response_json = r.json()
    incId = response_json['id']

    # wait for incident to be created
    time.sleep(1)

    # get incident
    incidents = client.SearchIncidents(0, 50, 'id:' + incId)

    if incidents['total'] != 1:
        print 'failed to get incident with id:' + incId
        return

    return incidents['data'][0]


def get_investigation_playbook_state(client, inv_id):
    res = client.req('GET', '/inv-playbook/' + inv_id, {})
    investigation_playbook = res.json()

    return investigation_playbook['state']


def main():
    options = options_handler()
    c = demisto.DemistoClient(options.key, options.server)

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