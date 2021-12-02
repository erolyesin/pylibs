#!/bin/python3
#
#  Copyright (c) 2019-2021.  SandboxZilla
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this
#  software and associated documentation files (the "Software"), to deal in the Software
#  without restriction, including without limitation the rights to use, copy, modify,
#  merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
#  permit persons to whom the Software is furnished to do so.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
#  INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
#  PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#  HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
#  OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#
from __future__ import absolute_import

__author__ = "Erol Yesin"

import base64
import json
import socket
import time
import urllib
from datetime import datetime
from pathlib import Path
from threading import Thread
from typing import Any

from paho.mqtt.client import Client

from .comm_queues import Queue as Q
from .event_handler import EventHandler as Eventer
from .log_wrapper import LoggerWrapper


class MQTT_Wrapper(object):
    def __init__(
        self,
        broker: str,
        certs: (str, None) = None,
        name: str = "TS",
        user: (str, None) = None,
        sn_filter: list = ["+"],
        logger: (LoggerWrapper, None) = None,
        debug: bool = True,
    ):

        self.name = name
        self.cid = "%s-%s-%s" % (
            name,
            socket.getfqdn(),
            str(int(time.time() * (10 ** 9))),
        )

        self.subscriptions = []
        self.subscribed = dict()

        self.client = Client(client_id=self.cid)

        self.sn_filter = sn_filter

        if "+" not in self.sn_filter and isinstance(self.sn_filter, list):
            self.sn_filter.append("+")

        self.event = {"status": Eventer(event="status", src="broker_client")}
        self.topic_event = dict()

        self.in_q = Q()
        self.continue_thread = True
        self.connected = False
        self.in_qprocT = Thread(
            name="mqtt_InqT", target=self.in_qproc, args=[self.in_q]
        )
        self.in_qprocT.start()

        self.out_q = Q()
        self.out_qprocT = Thread(
            name="mqtt_OutqT", target=self.out_qproc, args=[self.out_q]
        )
        self.out_qprocT.start()

        self.debug_file = None
        if debug:
            self.debug_subscriptions = self.subscriptions.copy()
            self.debug_on()
            self.debug_write(topic=broker, data="ID: " + self.cid)

        self.server = broker.split(":")[0]
        self.port = int(broker.split(":")[1])
        self.on_connect = self._on_connect
        self.on_message = self._on_message
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        self.client.on_subscribe = self._on_subscribe
        self.client.on_unsubscribe = self._on_unsubscribe
        if self.port in (8883, 443):
            if user is not None and ":" in user:
                user, password = str(user).split(":", maxsplit=1)
                self.client.username_pw_set(username=user, password=password)
            self.client.tls_set(ca_certs=certs)
        self.client.connect(host=self.server, port=self.port, keepalive=10)
        self.client.loop_start()

    def in_qproc(self, inq: Q):
        while self.continue_thread:
            item = inq.get()
            if item is not None and str(item) not in ["exit", "quit"]:
                found_topic = self._section_compare(
                    pub=item.topic, subs=list(self.topic_event.keys())
                )
                if found_topic is not None:
                    # self.debug_write(topic=found_topic, data=item.payload)
                    self.topic_event[found_topic].post(payload=item)
            else:
                pass
        else:
            pass

    def out_qproc(self, outq: Q):
        while self.continue_thread:
            item = outq.get()
            if item is not None and isinstance(item, dict):
                if "payload" not in item or "topic" not in item:
                    continue
                rc, rc_msg = self.publish(
                    topic=item["topic"],
                    qos=item["qos"],
                    retain=item["retain"],
                    payload=item["payload"],
                )
                # QOS level 2 already does retries
                if rc != 0 and item["qos"] != 2:
                    self.out_q.put_back(item=item)
                    time.sleep(0.5)
                time.sleep(0.5)
                item = None

    def send(
        self, data: str, channel: (str, None) = None, qos: int = 1, retain: bool = True
    ):
        msg = {"topic": channel, "qos": qos, "retain": retain, "payload": data}
        if channel is None:
            for channel in self.subscriptions:
                msg["topic"] = channel
                self.out_q.put(item=msg)
        else:
            self.out_q.put(item=msg)

    def publish(self, topic, payload, qos=1, retain=True):
        try:
            json_object = json.loads(payload)
        except ValueError as ve:
            self.debug_write(
                topic=ve.msg,
                data=payload,
            )
            raise ve

        rc, cnt = self.client.publish(
            topic=topic, payload=payload, qos=qos, retain=retain
        )
        if rc == 0:
            rc_msg = "SUCCESSFUL PUBLISH:rc=%d: Good job!  Gimme another" % int(rc)
        elif rc == 1:
            rc_msg = "FAILED PUBLISH:rc=%d: Incorrect protocol version" % int(rc)
        elif rc == 2:
            rc_msg = "FAILED CONNECTION:rc=%d: Invalid client identifier" % int(rc)
        elif rc == 3:
            rc_msg = "FAILED CONNECTION:rc=%d: Server unavailable" % int(rc)
        elif rc == 4:
            rc_msg = "FAILED CONNECTION:rc=%d: Bad username or password" % int(rc)
        elif rc == 5:
            rc_msg = "FAILED CONNECTION:rc=%d: Not authorised" % int(rc)
        else:
            rc_msg = "UNKNOWN ERROR:rc=%d: What did u do?" % int(rc)

        self.debug_write(
            topic=rc_msg,
            data=payload,
        )
        return rc, rc_msg

    # Events for internal events, like the app is starting or going down
    # Topics are external events, like the topic we subscribe to on the broker
    def subscribe(
        self,
        name: str,
        call_back: callable,
        event: str = None,
        topic: (str, list) = None,
        cookie: Any = None,
    ):
        if name is None or call_back is None:
            return self
        if event is not None:
            if event not in self.event:
                self.event[event] = Eventer(event=event, src="broker_event")
            self.event[event].subscribe(name=name, on_event=call_back, cookie=cookie)
            self.debug_update(event)

        if topic is not None:
            if isinstance(topic, str):
                topics = [topic]
            else:
                topics = topic
            for topic in topics:
                if topic not in self.topic_event:
                    self.topic_event[topic] = Eventer(event=topic, src="broker_topic")
                self.topic_event[topic].subscribe(
                    name=name, on_event=call_back, cookie=cookie
                )
                self.client.subscribe(topic=topic, qos=2)
                if topic not in self.subscriptions:
                    self.subscriptions.append(topic)
                    self.debug_update(topic)

        # Both event and topic are None
        elif event is None:
            for topic in self.subscriptions:
                self.subscribe(
                    name=name, call_back=call_back, topic=topic, cookie=cookie
                )

        self.debug_write(topic=topic, data="Registered %s for %s event" % (name, topic))
        return self

    def unsubscribe(self, name: str, event: str = None, topic: str = None):
        if event is not None:
            if event in self.event:
                self.event[event].unsubscribe(name)
                self.debug_write(
                    topic=topic, data="Unregistered %s from %s event" % (name, event)
                )
        if topic is not None:
            if topic in self.topic_event:
                self.topic_event[topic].unsubscribe(name)
                self.debug_write(
                    topic=topic, data="Unregistered %s from %s topic" % (name, topic)
                )

    def start(
        self, topic: (str, list), name: str, call_back: callable, cookie: Any = None
    ):
        self.event["status"].post(
            payload="Start logging topic %s to %s" % (topic, name)
        )
        self.subscribe(topic=topic, name=name, call_back=call_back, cookie=cookie)
        return self

    def stop(self, event: str, name: str):
        self.event["status"].post(payload="Stop logging topic %s to %s" % (event, name))
        self.unsubscribe(topic=event, name=name)
        return self

    def close(self):
        self.debug_write(topic="CLOSE", data="SHUTDOWN")
        self.client.loop_stop()
        self.client.disconnect()
        self.debug_off()

        self.continue_thread = False
        self.in_q.put(item="quit")
        self.in_qprocT.join(timeout=4)
        self.out_q.put(item="quit")
        self.out_qprocT.join(timeout=4)

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        if mid not in self.subscribed:
            return
        msg = "%s:qos=%s" % (self.subscribed[mid], str(granted_qos[0]))
        self.debug_write(topic="SUBSCRIBED", data=msg)

    def _on_unsubscribe(self, client, userdata, mid):
        if mid not in self.subscribed:
            return
        msg = "Unsubscribed: " + self.subscribed[mid]
        self.debug_write(topic="UNSUBSCRIBED", data=self.subscribed[mid])
        del self.subscribed[mid]
        self.event["status"].post(payload=msg)

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        if rc != 0:
            self.debug_write(topic="DISCONNECT:rc=%d" % int(rc), data="UNEXPECTED")
        else:
            self.debug_write(topic="DISCONNECT:rc=%d" % int(rc), data="SHUTDOWN")
            self.subscribed.clear()

    # The callback for when the client receives a CONNACK response from the server.
    def _on_connect(self, client, userdata, flags, rc):
        if rc != 0:
            self.connected = False
            if rc == 1:
                self.debug_write(
                    topic="FAILED CONNECTION:rc=%d" % int(rc),
                    data="incorrect protocol version",
                )
            elif rc == 2:
                self.debug_write(
                    topic="FAILED CONNECTION:rc=%d" % int(rc),
                    data="invalid client identifier",
                )
            elif rc == 3:
                self.debug_write(
                    topic="FAILED CONNECTION:rc=%d" % int(rc), data="server unavailable"
                )
            elif rc == 4:
                self.debug_write(
                    topic="FAILED CONNECTION:rc=%d" % int(rc),
                    data="bad username or password",
                )
            elif rc == 5:
                self.debug_write(
                    topic="FAILED CONNECTION:rc=%d" % int(rc), data="not authorised"
                )
            return

        msg = "Connected: " + self.server
        self.debug_write(topic="CONNECTED:rc=%d" % int(rc), data=self.server)
        self.event["status"].post(payload=msg)
        for subscription in self.subscriptions:
            if "<MAC>" not in subscription and "<UUID>" not in subscription:
                rc, mid = self.client.subscribe(topic=subscription, qos=2)
                if rc != 0:
                    err_msg = "Received error %d on attemtping to subscribe to %s" % (
                        rc,
                        subscription,
                    )
                    self.debug_write(topic=subscription, data=err_msg)
                else:
                    self.subscribed[mid] = subscription
                pass
        self.connected = True

    # The callback for when a PUBLISH message is received from the server.
    def _on_message(self, client, userdata, msg):
        msg.payload = "".join(chr(x) for x in msg.payload)

        found_topic = self._section_compare(
            pub=msg.topic, subs=list(self.topic_event.keys())
        )

        if found_topic is not None:
            self.in_q.put(item=msg)
            self.debug_write(topic=msg.topic, data=msg.payload)

    def _section_compare(self, pub: str, subs: list):
        if pub in subs:
            return pub
        pub = pub.split("/")
        found_topic = None
        for indx, sub in enumerate(subs):
            sub = sub.split("/")
            found_topic = subs[indx]
            for inner, sec in enumerate(sub):
                if inner >= len(pub):
                    break
                if sec != pub[inner] and sec not in self.sn_filter:
                    found_topic = None
            if found_topic is not None:
                return found_topic

        return found_topic

    def debug_on(self):
        if self.debug_file is None:
            self.debug_file = Path("logs", "mqtt_helper.log")
            if not self.debug_file.parent.exists():
                self.debug_file.parent.mkdir(parents=True)
            self.debug_write(topic="DEBUG", data="ON")

        for topic in self.subscriptions:
            self.debug_update(topic=topic)

    def debug_update(self, topic):
        if self.debug_file is not None and topic not in self.debug_subscriptions:
            self.debug_subscriptions.append(topic)
            self.subscribe(name="debug", call_back=self.dbg_callback, topic=topic)

    def debug_off(self):
        if self.debug_file is not None:
            self.debug_write(topic="DEBUG", data="OFF")
        for topic in self.subscriptions:
            self.unsubscribe(name="debug", topic=topic)
        self.debug_file = None
        return self

    def debug_write(self, topic, data):
        if self.debug_file is not None:
            pid = str(os.getpid())
            entry = "%s,%s,%s,%s\n" % (str(datetime.now()), str(pid), topic, data)
            self.debug_file.open("a").write(entry)

    def dbg_callback(self, msg):
        if self.debug_file is not None and msg is not None:
            topic = msg["payload"].topic
            payload = msg["payload"].payload
            try:
                data_dict = json.loads(payload)
                if "time" in data_dict:
                    data_dict["time"] = time.strftime(
                        "%H:%M:%S", time.gmtime(data_dict["time"])
                    )
                if "timestamp" in data_dict:
                    data_dict["timestamp"] = time.strftime(
                        "%H:%M:%S", time.gmtime(data_dict["timestamp"])
                    )
                if "payload" in data_dict and "ts.0" in data_dict["payload"]:
                    data_dict["payload"]["ts.0"] = time.strftime(
                        "%H:%M:%S", time.gmtime(data_dict["payload"]["ts.0"])
                    )
                if "hwbrain/from_fan" in topic and '"msg"' in payload:
                    data_dict["hex"] = base64.b64decode(data_dict["msg"]).hex()
                self.debug_write(topic=topic, data=str(data_dict))
            except ValueError as e:
                payload = urllib.parse.unquote(str(payload))
                self.debug_write(topic=topic, data=payload)


if __name__ == "__main__":

    def _on_msg(pkt):
        print(str(pkt))

    client = None
    try:
        client = MQTT_Wrapper(
            broker="mq.telesense.net:1883",
            certs=None,
            subscriptions=["gw/+/tsng/gw_log"],
        )

        client.start(topic="gw/+/tsng/gw_log", name="utest", call_back=_on_msg)
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nRemember me fondly!")
    finally:
        client.close()
