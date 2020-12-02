#!/usr/bin/python
# -*- coding:utf-8 -*-

#    ___       __   ________  _______   ________  _____ ______   _______   ________  ________  ___  ___  ________  ________  ________   ___  __       
#   |\  \     |\  \|\   __  \|\  ___ \ |\   __  \|\   _ \  _   \|\  ___ \ |\   ____\|\   ____\|\  \|\  \|\   __  \|\   __  \|\   ___  \|\  \|\  \     
#   \ \  \    \ \  \ \  \|\  \ \   __/|\ \  \|\  \ \  \\\__\ \  \ \   __/|\ \  \___|\ \  \___|\ \  \\\  \ \  \|\  \ \  \|\  \ \  \\ \  \ \  \/  /|_   
#    \ \  \  __\ \  \ \   __  \ \  \_|/_\ \   _  _\ \  \\|__| \  \ \  \_|/_\ \_____  \ \  \    \ \   __  \ \   _  _\ \   __  \ \  \\ \  \ \   ___  \  
#     \ \  \|\__\_\  \ \  \ \  \ \  \_|\ \ \  \\  \\ \  \    \ \  \ \  \_|\ \|____|\  \ \  \____\ \  \ \  \ \  \\  \\ \  \ \  \ \  \\ \  \ \  \\ \  \ 
#      \ \____________\ \__\ \__\ \_______\ \__\\ _\\ \__\    \ \__\ \_______\____\_\  \ \_______\ \__\ \__\ \__\\ _\\ \__\ \__\ \__\\ \__\ \__\\ \__\
#       \|____________|\|__|\|__|\|_______|\|__|\|__|\|__|     \|__|\|_______|\_________\|_______|\|__|\|__|\|__|\|__|\|__|\|__|\|__| \|__|\|__| \|__|
#                                                                            \|_________|                                                             
#   Copyright © 2020 David Breitz
                                                                                                                                                  
import serial           # Import pyserial library
import os               # Import os library
import sys              # Import sys library
import logging          # Import logging library
import glob             # Import glob library
import time             # Import time library
import datetime         # Import datetime library
from RPLCD.i2c import CharLCD       # Import LCD library
import RPi.GPIO as GPIO # Import RPi GPIO library

temp_c = 0.0
tempdata = 0.0

#-------GPIOsetup-------
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(27, GPIO.OUT)
GPIO.setup(22, GPIO.OUT)
GPIO.setup(24, GPIO.OUT)

HEIZUNG = 24

#-------Setup of logging library-------
logging.basicConfig(level=logging.INFO)
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

#-------Setup of waveshare_2_CH_RS485_HAT------- 
ser = serial.Serial(
    port='/dev/ttyUSB0',
    baudrate=115200,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_EVEN,
    stopbits=serial.STOPBITS_ONE,
    timeout=1.1
)

#-------Setup of lcd-------
lcd = CharLCD('PCF8574', 0x3f)

# Setup of ds18b20
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
 
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

#-------Definition of varaibles for ds18b20 temperature sensor-------
def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines
 
def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c

def check_temp(temp):
    if temp < 50.0:
        GPIO.output(HEIZUNG, True)
        print("Heizung an")
        lcd.cursor_pos = (2, 11)
        lcd.write_string("Heat: on ")
    elif temp > 51.0:
        GPIO.output(HEIZUNG, False)
        print("Heizung aus")
        lcd.cursor_pos = (2, 11)
        lcd.write_string("Heat: off")
    else:
        GPIO.output(HEIZUNG, False)
        print("Heizung aus")
        lcd.cursor_pos = (2, 11)
        lcd.write_string("Heat: off")
            

#-------Start of Wärmeschrank program------- 
data = ''
data_t = ''
i = 0

ser.write('$01V1\r\n')
time.sleep(0.005)   #Time passed to send

try:
    while(1):
        GetDateTime = datetime.datetime.now() .strftime("%Y-%m-%d %H:%M:%S")
        
        tempdata = read_temp()
        tempcurrent = tempdata
        tempdata = str(tempdata)

        check_temp(tempcurrent)
        
        data_t = ''
        ser.write('$01V1\r\n')
        time.sleep(0.01)   #Time passed to send
        data_t = ser.read()
        data = data + str(data_t)

        fo = open("/media/pi/LOGS/crash_log/crash-" + GetDateTime[0:11] + ".txt","a+")

        if(data_t == '\r'):
            print("[" + GetDateTime + "] Modul Antwortet.")
            print("[" + data + "]")
            fo.write("[" + GetDateTime + "] Modul Antwortet: " + data)
            fo.write("\n")
            fo.close()
            ser.flushInput()   # clear out old stuff
            lcd.cursor_pos = (0, 0)
            lcd.write_string("Folterkammer "+ GetDateTime[11:16])
            lcd.cursor_pos = (1, 0)
            lcd.write_string("Temperatur: " + tempdata[0:4] + " C")
            lcd.cursor_pos = (2, 0)
            lcd.write_string("State: ok ")
            lcd.cursor_pos = (3, 0)
            lcd.write_string(data[1:21])
            data = ''
            time.sleep(1.0)   # Time passed to send
            i = 0
        elif (len(data)==0 and i>0):
            print("[" + GetDateTime + "] Modul Antwortet nicht.")
            fo.write("[" + GetDateTime + "] Modul Antwortet nicht.")
            fo.write("\n")
            fo.close()
            lcd.cursor_pos = (0, 0)
            lcd.write_string("Folterkammer "+ GetDateTime[11:16])
            lcd.cursor_pos = (1, 0)
            lcd.write_string("Temperatur: " + tempdata[0:4] + " C")
            lcd.cursor_pos = (2, 0)
            lcd.write_string("State: n/a")
            lcd.cursor_pos = (3, 0)
            lcd.write_string("Keine Daten         ")
            GPIO.output(HEIZUNG, False)
        else:
            i = i + 1    

except KeyboardInterrupt:    
    logging.info("ctrl + c:")
    exit()
