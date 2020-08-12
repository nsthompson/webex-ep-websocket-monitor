#!/usr/bin/env python3
#
# Cisco Webex Endpoint Websocket Monitor
# Written by Nick Thompson (@nsthompson)
# Copyright (C) 2020 World Wide Technology
# All Rights Reserved
#

import websockets
import ssl
import asyncio
import base64
import os
import sys
import json
import logging
import types
import signal

from datetime import datetime
from dotenv import load_dotenv

from lib.notifications import Notifications


async def readWebSocket(host, username, password, queue, log=None):
    # Define the Websocket URL
    ws_url = f'wss://{host}/ws/'

    # Construct our Authorization String
    credentials = base64.b64encode(
        bytes(f'{username}:{password}', encoding='utf-8')
    ).decode('utf-8')

    # Construct Authorization Header
    headers = {
        "Authorization": f'Basic {credentials}',
    }

    try:
        # Open Websocket Connection to Endpoint
        ws = await websockets.connect(
            ws_url,
            ssl=ssl._create_unverified_context(),
            extra_headers=headers
        )

        # Build the payload to subscribe to system state events
        system_payload = {
            "jsonrpc": "2.0",
            "id": "100",
            "method": "xFeedback/Subscribe",
            "params": {
                "Query": [
                    "Status",
                    "SystemUnit",
                    "State"
                ],
                "NotifyCurrentValue": True
            }
        }

        # Build the payload to subscribe to video state events
        video_payload = {
            "jsonrpc": "2.0",
            "id": "200",
            "method": "xFeedback/Subscribe",
            "params": {
                "Query": [
                    "Status",
                    "Video",
                    "Input",
                    "MainVideoMute"
                ],
                "NotifyCurrentValue": True
            }
        }

        # Subscribe to System State Events
        await ws.send(json.dumps(system_payload))
        msg = f'{datetime.now()} Sending: {json.dumps(system_payload)}'
        log.warning(msg)

        # Subscribe to Video State Events
        await ws.send(json.dumps(video_payload))
        msg = f'{datetime.now()} Sending: {json.dumps(video_payload)}'
        log.warning(msg)

        while True:
            # Wait for Data from Endpoint
            data = await ws.recv()
            # Log Received Data
            msg = f'{datetime.now()} Received: {data}'
            log.warning(msg)
            # Send Data to the Queue
            await queue.put(data)
    except websockets.WebSocketException:
        raise


async def monitor_endpoint(host, username, password, sn_obj, log=None):
    queue = asyncio.Queue()

    # Spawn a Worker to Read Websocket Data
    asyncio.create_task(
        readWebSocket(
            host,
            username,
            password,
            queue,
            log
        ),
        name="readWebSocket"
    )

    while True:
        try:
            data = await queue.get()
            parse_recv_data(data, sn_obj, log)
        except asyncio.CancelledError:
            msg = f'{datetime.now()} Received CancelledError...'
            log.warning(msg)
            break

    msg = f'{datetime.now()} Done executing coroutine...'
    log.warning(msg)
    asyncio.get_event_loop().stop()


async def shutdown(loop, signal=None, log=None):
    if signal and log:
        msg = f'{datetime.now()} Received exit signal {signal.name}...'
        log.warning(msg)

    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    for task in tasks:
        msg = f'{datetime.now()} Cancelling task {task.get_name()}...'
        logging.warning(msg)
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()


def handle_exceptions(loop, context):
    # Get the Logger
    log = logging.getLogger()

    # Get the Exception Message
    e = context.get("exception", context["message"])
    msg = f'{datetime.now()} Caught Exception: {e}'
    log.warning(msg)
    asyncio.create_task(shutdown(loop))


def parse_recv_data(data, sn_obj, log=None):
    # Convert Received Data to JSON
    data_dict = json.loads(data)
    if data_dict.get("params") is not None:
        if data_dict['params']['Status'].get("SystemUnit") is not None:
            NumberOfActiveCalls = (
                data_dict['params']['Status']
                ['SystemUnit']['State'].get("NumberOfActiveCalls")
            )
            CameraLid = (
                data_dict['params']['Status']
                ['SystemUnit']['State'].get("CameraLid")
            )

            if CameraLid == "Open":
                sn_obj.onvideo = True
            elif CameraLid == "Closed":
                sn_obj.onvideo = False

            if NumberOfActiveCalls == 1:
                msg = f'{datetime.now()} Active Calls: {NumberOfActiveCalls}'
                sn_obj.oncall = True
                log.warning(msg)
            elif NumberOfActiveCalls == 0:
                msg = f'{datetime.now()} Active Calls: {NumberOfActiveCalls}'
                sn_obj.oncall = False
                log.warning(msg)
        elif data_dict['params']['Status'].get("Video") is not None:
            MainVideoMute = (
                data_dict['params']['Status']['Video']
                ['Input'].get("MainVideoMute")
            )

            # MainVideoMute On = No Video Being Transmitted
            if MainVideoMute == "On":
                sn_obj.onvideo = False
            elif MainVideoMute == "Off":
                sn_obj.onvideo = True

        if sn_obj.oncall and sn_obj.onvideo and not sn_obj.vidnotification:
            msg = f'{datetime.now()} Turning on Video Notification'
            log.warning(msg)
            sn_obj.notifier.video_notification_on()
            sn_obj.vidnotification = True
            sn_obj.callnotification = False
        elif (
            sn_obj.oncall
            and not sn_obj.onvideo
            and not sn_obj.callnotification
        ):
            msg = f'{datetime.now()} Turning on Call Notification'
            log.warning(msg)
            sn_obj.notifier.call_notification_on()
            sn_obj.callnotification = True
            sn_obj.vidnotification = False
        elif (
            not sn_obj.oncall
            and (sn_obj.vidnotification or sn_obj.callnotification)
        ):
            msg = f'{datetime.now()} Turning off Notification'
            log.warning(msg)
            sn_obj.notifier.notification_off()
            sn_obj.notification = False


def main():
    # Load Environment Variables
    load_dotenv()

    username = os.environ.get('EP_USERNAME')
    password = os.environ.get('EP_PASSWORD')
    host = os.environ.get('EP_ADDRESS')

    # Configure Logging
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)

    log_stdout = logging.StreamHandler(sys.stdout)
    log_stdout.setLevel(logging.WARNING)
    log.addHandler(log_stdout)

    # Build a SimpleNamespace object for data sharing between methods
    sn_obj = types.SimpleNamespace()
    sn_obj.oncall = False
    sn_obj.onvideo = False
    sn_obj.callnotification = False
    sn_obj.vidnotification = False

    # Instantiate Notifications
    sn_obj.notifier = Notifications(log)

    # Get asyncio event loop
    loop = asyncio.get_event_loop()

    # Create asyncio future object
    asyncio.ensure_future(
        monitor_endpoint(
            host,
            username,
            password,
            sn_obj,
            log
        )
    )

    # Signal & Exception Handling
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(shutdown(loop, s, log))
        )
    loop.set_exception_handler(handle_exceptions)

    # Run asyncio event loop until stopped
    loop.run_forever()


if __name__ == "__main__":
    main()
