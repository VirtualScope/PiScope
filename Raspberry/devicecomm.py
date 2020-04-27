#Pi Control Server Imports
import sys
import json
import requests
from gevent.pywsgi import WSGIServer
from flask import Flask, request, jsonify
from flask_restful import Resource, Api
import threading                    #Threading for locks and spawning new threads
import importlib

try:
    print("Importing Modules")
    importlib.import_module('lightcontrols')
    importlib.import_module('steppercontrol')
    from lightcontrols import LightControls
    from steppercontrol import StepperControl
except:
    print("Error, some modules are missing! Exiting...") # Needed for IDLE error message
    sys.exit("Error, some modules are missing! Exiting...")


#Start the control Server        
class DeviceComm(Resource):
    motorCalls = 0

    def start(self):
        app = Flask(__name__)
        api = Api(app)
        #ERROR_JSON = {'status':'error', 'message':'invalid input'}
        
        api.add_resource(DeviceComm, '/api/device/')
        
        print("Starting Web Server") # More secure web server instead of directly using Flask.
        
        http_server = WSGIServer(('0.0.0.0', 5000), app)
        http_server.serve_forever()
    def post(self):
        print("Recieved a request.")
        req = request.json # Note 'dict' is a python dictionary object.
        if req['device'] == 'light' and req['command'] == 'switch' and type(req['value']) == bool:
            #Start a new thread to test the light
            lightRequest = LightControls("", "", req['value']) # creates a new lightControls object
            lightThread = threading.Thread(target=LightControls.noTimerSwitch, kwargs=dict(self=lightRequest), name='lightThread')
            lightThread.start()
        elif req['device'] == 'motor' and req['command'] == 'move' and type(req['value']) == int:
            DeviceComm.motorCalls += 1
            threadName = 'motorThread' + str(DeviceComm.motorCalls)
            displacement = StepperControl(req['value'])
            motorThread = threading.Thread(target=StepperControl.move, kwargs=dict(self=displacement), name=threadName)
            motorThread.start()
        elif req['device'] == 'light' and req['command'] == 'timer' and type(req['value']) == float:
            lightRequest = LightControls(True, req['value'], True) # creates a new lightControls object
            lightThread = threading.Thread(target=LightControls.timerOn, kwargs=dict(self=lightRequest), name='lightThread')
            lightThread.start()
