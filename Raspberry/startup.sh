#!/bin/bash

#Install necessary package dependencies
apt install python

#Install python package dependencies
pip install mysql-connector-python

#Run server
python scope.py