import sys
import os
import subprocess
import ftplib
import signal
from picamera import PiCamera
from time import sleep
import mysql.connector
from mysql.connector import Error
import threading
import datetime
import configparser
import importlib
try:
  print("Importing VirtualScope Modules")
  importlib.import_module('devicecomm')
  from devicecomm import DeviceComm
except:
  print("Error, some modules are missing in virtualscope.py! Exiting...") # Needed for IDLE error message
  sys.exit("Error, some modules are missing! Exiting...")


#Original pi code.
class scope(): 
  def __init__(self):
    #Define the microscope name !!IMPORTANT it comes from terminal argument
    #my_name = sys.argv[1]

    config = configparser.ConfigParser()

    #If the config file doesn't exist, prompt the user for config info
    if len(config.read('virtualscope.ini')) == 0:
      config['Database'] = {'Host IP': input("Enter the host IP Address: "),
                            'Database Name': input("Enter the database name: "),
                            'Username': input("Enter the database username: "),
                            'Password': input("Enter the database password: ")}

      config['FTP'] = {'Hostname': input("Enter the FTP hostname: "),
                            'Port': '21',
                            'Username': input("Enter the FTP username: "),
                            'Password': input("Enter the FTP password: ")}

      config['Miscellaneous'] = {'Microscope Name': input("Enter the name of this microscope: "),
                                  'Pictures Path': '/home/pi/MicroscopeImages/'}
      config['Miscellaneous']['Working Images Path'] = 'public_html/microscopes/' + config['Miscellaneous']['Microscope Name'] + '/images/'

      with open('virtualscope.ini', 'w') as configfile:
        config.write(configfile)

    config.read('virtualscope.ini')

    #Grab settings from config file
    databaseConfig = config['Database']
    ftpConfig = config['FTP']
    miscConfig = config['Miscellaneous']

    #Establish the database connection
    try:
      connection = mysql.connector.connect(host=databaseConfig['Host IP'],
                          database=databaseConfig['Database Name'],
                          user=databaseConfig['Username'],
                          password=databaseConfig['Password'])

      if connection.is_connected():
        #Select the time increment from the microscopes table
        cursor = connection.cursor()
        select_stmt = "SELECT picture_time_increment, youtube_stream FROM microscopes WHERE microscope_name = %(microscope_name)s"
        cursor.execute(select_stmt, { 'microscope_name': miscConfig['Microscope Name'] })
        info = cursor.fetchone()
        time_increment = info[0]
        stream_link = info[1]

    #Error connecting -> Use default time_increment
    except Error as e:
      print("Error while connecting to MySQL", e)
      time_increment = 3
      if (not('connection' in locals())):
          sys.exit("Error while connecting to MySQL. Check virtualscope.ini Exiting...")
      
    #Close the database connection
    finally:
      if ('connection' in locals() and connection.is_connected()):
        cursor.close()
        connection.close()

    #Connect to FTP server for file uploading
    ftp = ftplib.FTP()
    host = ftpConfig['Hostname']
    port = int(ftpConfig['Port'])
    ftp.connect(host, port)
    ftp.login(ftpConfig['Username'], ftpConfig['Password'])
    ftp.cwd(miscConfig['Working Images Path'])

    #The concatonated command for streaming
    stream_command = "raspivid -o - -t 0 -w 1280 -h 720 -fps 30 -b 6000000 | ffmpeg -re -f s16le -ac 2 -i /dev/zero -f h264 -i - -vcodec copy -g 50 -strict experimental -f flv " + stream_link

    #Picture folder where photos are saved on the Pi
    pic_folder = miscConfig['Pictures Path']

    #NEW: Start Control Server
    DeviceCommThread = threading.Thread(target=DeviceComm.start, args=(DeviceComm,), name='DeviceCommMainThread')
    DeviceCommThread.start()

    while True:
      #Run stream for designated time interval
      pro = subprocess.Popen(stream_command, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid) 

      sleep((time_increment * 60)+3)
      os.killpg(os.getpgid(pro.pid), signal.SIGTERM)
      
      #Define picture path and capture photo
      now = datetime.datetime.now() #Get timestamp
      picture_name = now.strftime("date_%m-%d-%Y_time_%H-%M-%S.jpg") #format image name
      picture_path = pic_folder + "current_image.jpg"
      camera = PiCamera()
      sleep(0.75)
      camera.capture(picture_path, resize=(1230, 924)) #take pictue and resize
      camera.close()
      
      #Send pic via ftp
      file = open(picture_path,"rb")                  # file to send
      ftp.storbinary("STOR " + picture_name, file)     # send the file
      file.close()

scope()