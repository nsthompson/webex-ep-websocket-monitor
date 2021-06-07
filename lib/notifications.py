import os

from dotenv import load_dotenv
from datetime import datetime

from .plugins.ha import HA


class Notifications:

    def __init__(self, log=None):
        # Logging Configuration
        self.log = log

        # Load Environment Variables
        load_dotenv()

        # Load Home-Assistant Specific Configuration Values
        ha_address = os.environ.get('HA_ADDRESS')
        ha_port = os.environ.get('HA_PORT')
        ha_api_key = os.environ.get('HA_API_KEY')

        # Load Specific ZWave Configuration Values
        self.ha_zwave_device_id = os.environ.get('HA_ZWAVE_DEVICE_ID')
        self.ha_zwave_parameter = os.environ.get('HA_ZWAVE_PARAMETER')
        self.ha_zwave_on_video = os.environ.get('HA_ZWAVE_ON_VIDEO')
        self.ha_zwave_on_call = os.environ.get('HA_ZWAVE_ON_CALL')
        self.ha_zwave_off = os.environ.get('HA_ZWAVE_OFF')

        # Instantiate Home-Assistant Connection
        self.ha = HA(ha_address, ha_port, ha_api_key, self.log)

    def video_notification_on(self):
        # Turn on Video Notification
        set_param = self.ha.set_zwave_config_parameter(
                self.ha_zwave_device_id,
                self.ha_zwave_parameter,
                self.ha_zwave_on_video
        )
        if set_param == []:
            msg = (
                f'{datetime.now()} Notification Value set to '
                f'{self.ha_zwave_on_video}...'
            )
            self.log.warning(msg)
        else:
            msg = f'{datetime.now()} Error setting notification value!'
            self.log.warning(msg)

    def call_notification_on(self):
        # Turn on Call Notification
        set_param = self.ha.set_zwave_config_parameter(
                self.ha_zwave_device_id,
                self.ha_zwave_parameter,
                self.ha_zwave_on_call
        )
        if set_param == []:
            msg = (
                f'{datetime.now()} Notification Value set to '
                f'{self.ha_zwave_on_call}...'
            )
            self.log.warning(msg)
        else:
            msg = f'{datetime.now()} Error setting notification value!'
            self.log.warning(msg)

    def notification_off(self):
        # Turn off Notifications
        set_param = self.ha.set_zwave_config_parameter(
                self.ha_zwave_device_id,
                self.ha_zwave_parameter,
                self.ha_zwave_off
        )
        if set_param == []:
            msg = (
                f'{datetime.now()} Notification Value set to '
                f'{self.ha_zwave_off}...'
            )
            self.log.warning(msg)
        else:
            msg = f'{datetime.now()} Error setting notification value!'
            self.log.warning(msg)
