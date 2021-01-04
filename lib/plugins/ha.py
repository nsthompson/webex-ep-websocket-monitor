import requests
import json


class HA:

    def __init__(self, host, port, api_token, log=None):

        self.base_url = f'https://{host}:{port}/api'
        self.api_token = api_token

        self.log = log

        self.headers = {
            "Authorization": f'Bearer {self.api_token}',
            "Content-Type": "application/json"
        }

    def _get(self, endpoint, params=None):
        try:
            response = requests.get(
                endpoint,
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            exception_type = e.__class__.__name__
            msg = str(e)
            return(exception_type, msg)

        if response.status_code == 200:
            return(response.json())

    def _post(self, endpoint, payload=None, params=None):
        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                data=payload,
                params=params
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            exception_type = e.__class__.__name__
            msg = str(e)
            return(exception_type, msg)

        if response.status_code == 200:
            return(response.json())

    def get_entity_state(self, entity_id):
        endpoint = f'{self.base_url}/states/{entity_id}'

        state_result = self._get(endpoint)

        return(state_result)

    def set_entity_state(self, entity_id, state):
        endpoint = f'{self.base_url}/states/{entity_id}'

        payload_dict = {
            "state": state
        }

        payload = json.dumps(payload_dict)

        set_result = self._post(endpoint, payload)

        return(set_result)

    def turn_on_light(self, entity_id):
        endpoint = f'{self.base_url}/services/light/turn_on'

        payload_dict = {
            "entity_id": entity_id
        }

        payload = json.dumps(payload_dict)

        on_result = self._post(endpoint, payload)

        return(on_result)

    def turn_off_light(self, entity_id):
        endpoint = f'{self.base_url}/services/light/turn_off'

        payload_dict = {
            "entity_id": entity_id
        }

        payload = json.dumps(payload_dict)

        off_result = self._post(endpoint, payload)

        return(off_result)

    def set_zwave_config_parameter(
        self,
        instance_id,
        node_id,
        parameter,
        value
    ):
        endpoint = f'{self.base_url}/services/ozw/set_config_parameter'

        payload_dict = {
            "instance_id": instance_id,
            "node_id": node_id,
            "parameter": parameter,
            "value": value
        }

        payload = json.dumps(payload_dict)

        set_config_result = self._post(endpoint, payload)

        return(set_config_result)
