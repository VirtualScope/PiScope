#!/bin/bash

#Check if script is being run as root
if [ `whoami` != root ]; then
    echo "To run this script, use \"sudo ./startup.sh\""
    exit
fi

#If python3 is not installed, install Python3
data >> startup.log
echo "Checking for Python 3..."
if ! dpkg -s python3 >/dev/null 2>&1; then
    echo "Installing python3..."
    apt install python3 >> startup.log
fi

#Install python package dependencies as user pi
echo "Checking for python packages..."
sudo -u pi pip3 install mysql-connector-python >> startup.log
sudo -u pi pip3 install gevent >> startup.log
sudo -u pi pip3 install flask_restful >> startup.log
sudo -u pi pip3 install flask >> startup.log

#Run server
echo "Starting VirtualScope..."
python3 virtualscope.py