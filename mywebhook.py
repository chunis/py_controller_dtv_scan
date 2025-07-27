#!/usr/bin/python3

import json
from flask import Flask, request
import base64
import logging


nodes_rx_db = {}  # save all nodes with their uplink freq

app = Flask(__name__)
app.logger.disabled = True
log = logging.getLogger('werkzeug')
log.disabled = True

@app.route('/kill', methods=['POST'])
def kill():
    print('exit webhook now...')
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/webhook', methods=['GET', 'POST'])
def get_webhook():
    if request.method == 'POST':
        #print("received data: ", request.data)
        # received data:  b'{"applicationID":"2","applicationName":"dtv-scan-eu868","deviceName":"node2","devEUI":"/v////3/ACA=","rxInfo":[],"txInfo":{"frequency":867500000,"modulation":"LORA","loRaModulationInfo":{"bandwidth":125,"spreadingFactor":12,"codeRate":"4/5","polarizationInversion":false}},"adr":true,"dr":0,"fCnt":3977,"fPort":2,"data":"GAAAAA==","objectJSON":"","tags":{},"confirmedUplink":false,"devAddr":"ABFV1g==","publishedAt":"2023-03-06T03:50:24.147679917Z","deviceProfileID":"691ac9ca-62e2-4c83-af9c-7060faace4ff","deviceProfileName":"eu868-device-profile"}'
        data = request.data.decode()
        data = json.loads(data)
        #print('data:', data)

        deveui = data["devEUI"]
        deveui = base64.b64decode(deveui)
        deveui = '-'.join(["%02x" %x for x in deveui])
        #print('deveui:', deveui)

        freq = data["txInfo"]["frequency"]
        #print('freq:', freq)
        try:
            nodes_rx_db.update({ deveui: int(float(freq)) })
        except:
            print("something wrong when update nodes rx database")
    else:
        print("received GET data")

    return 'success', 200


def continue_recv():
    app.run(host='0.0.0.0', port=2222)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=2222)

