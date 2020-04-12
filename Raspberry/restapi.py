# FLASK Must be replaced by another web server, as it is not secure.
#!/usr/bin/python3
import importlib
import sys
import json
import requests
from gevent.pywsgi import WSGIServer

try:
    print("Importing Modules")
    importlib.import_module('light')
    importlib.import_module('motor')
except:
    print("Error, some modules are missing! Exiting...") # Needed for IDLE error message
    sys.exit("Error, some modules are missing! Exiting...")
from flask import Flask, request, jsonify
from motor import moveMotorFromWeb
from light import lightOnNoTimerWeb, lightWithTimerWeb, temporaryLightPowerTest
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

class DeviceComm(Resource):
    def post(self):
        req = request.json # Note 'dict' is a python dictionary object.
        if req['device'] == 'motor' and req['command'] == 'move' and type(req['value']) == int:
            if req['value'] > 0:
                moveMotor(true, req[value]) #True/False for direction, positive int for how far.
            else:
                moveMotor(false, abs(req['value'])
        elif req['device'] == 'light' and req['command'] == 'switch' and type(req['value']) == boolean:
            lightRequest = abs(req['setLightValue']) # keys() and values() to list info
            temporaryLightPowerTest(lightRequest)
        elif req['device'] == 'light' and req['command'] == 'timer' and type(req['value']) == int:
            lightRequest = abs(req['setLightValue']) # keys() and values() to list info
            temporaryLightPowerTest(lightRequest)
        print(request.json)

api.add_resource(DeviceComm, '/api/devicecomm/')

if __name__ == '__main__':
    print("Starting Web Server") # More secure web server instead of directly using Flask.
    http_server = WSGIServer(('0.0.0.0', 5000), app)
    http_server.serve_forever()
