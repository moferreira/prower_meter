#!/usr/bin/python3

# load necessary Python modules
import serial
import crcmod
import time
import sys
import paho.mqtt.client as paho
import datetime
from os.path import exists
import os
import syslog

### CHANGE TO MATCH YOUR SYSTEM ######################################
MQTT_SERVER   ="192.168.0.250"        # MQTT broker address
MQTT_USER     ="mqttuser"             # MQTT user name to be used
MQTT_PASSWORD ="VerySecret"           # MQTT user password
MQTT_TOPIC    ="kaifa/counters"       # topic to be published
SERIAL_PORT   ='/dev/ttyUSB0'         # serial port to be used
BAUD_RATE     ='9600'                 # baudrate to be used
FILE_DIR      ="/home/linaro/"        # directory to save data
######################################################################

FILE_NAME     = (FILE_DIR +
                "{:0>2d}".format(datetime.datetime.today().year)  +
                "{:0>2d}".format(datetime.datetime.today().month) +
                ".csv")               # create a file name to save data locally

# open serial port
try:
    ser = serial.Serial(
                port=SERIAL_PORT,             # your serial device ID
                baudrate=BAUD_RATE,           # serial speed
                parity=serial.PARITY_NONE,    # no parity (most of meters)
                stopbits=serial.STOPBITS_ONE, # one stop bit
                bytesize=serial.EIGHTBITS,    # data is eight bits long
                timeout=0)                    # no time out
except IOError:                               # error, report it
    syslog.syslog(syslog.LOG_ERR, "Could not open serial port " + SERIAL_PORT)
    sys.exit(-1)
ser.close()                                   # close serial for now, open it when necessary

# open file to write data
try:
    load_map = open(FILE_NAME, "a+") # open file
except IOError:                      # error, report it
    syslog.syslog(syslog.LOG_ERR, "Could not open file " + FILE_NAME)
    sys.exit(-1)
load_map.seek(0, os.SEEK_SET)        # go to the first line of the file
first_line = load_map.readline()     # read the first line (headers)
if first_line == '':                 # if it is a new file, write headers on it
    load_map.write("year,month,day,hour,minute,+A,-A,import_total,export_total,imported_vazio,imported_ponta,imported_cheia,exported_vazio,exported_ponta,exported_cheia,voltage\n")
load_map.seek(0, os.SEEK_END)        # go to the end of the file

# configure CRC calculation
crc16 = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)

# function to add CRC to command
def add_crc(data):
    # get CRC and return it in hex with 4 digits
    crc = "0x{:04x}".format((crc16(bytearray.fromhex(data))))
    return(data + crc[4:6] + crc[2:4])

# function to get register data
def get_data(data):
    ser.open()                              # open serial port
    ser.flushOutput                         # clear serial output buffer
    ser.flushInput                          # clear serial intput buffer
    cmd = bytearray.fromhex(add_crc(data))  # add CRC to the command
    got = 1                                 # main loop, get data
    while got:                              # loop until get valid response to command
        ser.write(serial.to_bytes(cmd))     # write request to serial
        time.sleep(0.8)                     # wait a while before reading a modbus response...
        resp = ser.read(1).hex()            # read 1 byte from the serial
        c = 0                               # counter to prevent looping forever
        while resp != data[0:2]:            # check up to 32 bytes if response comes from the right slave
            resp = ser.read(1).hex()        # if not, keep reading serial buffer
            c += 1                          # prevent looping forever
            if c == 32:                     # there was a loop, start from beginning
                break
        resp = resp + ser.read(1).hex()     # possibly found slave number response corret so add the command and check it
        if resp == data[0:4]:               # break the loop if the response includes the requested sent command
            resp = resp + ser.read(1).hex()        # get how many bytes are there to retrieve
            get_more = int(resp[4:6], 16) + 2      # set the number of additional bytes to read and do it, includding CRC
            resp = resp + ser.read(get_more).hex() # get the remaining data
            crc = crc16(bytearray.fromhex(resp))   # check CRC response sanity
            if crc == 0:                           # check if CRC is ok
                got = 0                            # got good data, break the main get data loop and return data
    ser.close()                              # close serial port
    return(resp)                             # return colected data


# get data
reg  = []                        # set array to receive all requested data
resp = get_data("01440001")      # request last profile
reg.append(int(resp[ 6:10], 16)) # reg-0  last profile year
reg.append(int(resp[10:12], 16)) # reg-1  last profile month
reg.append(int(resp[12:14], 16)) # reg-2  last profile day
reg.append(int(resp[16:18], 16)) # reg-3  last profile hour
reg.append(int(resp[18:20], 16)) # reg-4  last profile minutes
reg.append(int(resp[32:40], 16)) # reg-5  last profile +A
reg.append(int(resp[56:64], 16)) # reg-6  last profile -A

resp = get_data("010400160001")  # request total imported
reg.append(int(resp[6:14], 16))  # reg-7 imported total

resp = get_data("010400170001")  # request total exported
reg.append(int(resp[6:14], 16))  # reg-8 exported total

resp = get_data("010400260001")  # request imported vazio
reg.append(int(resp[6:14], 16))  # reg-9 imported vazio

resp = get_data("010400270001")  # request imported ponta
reg.append(int(resp[6:14], 16))  # reg-10 imported ponta

resp = get_data("010400280001")  # request imported cheio
reg.append(int(resp[6:14], 16))  # reg-11 imported cheia

resp = get_data("0104002D0001")  # request exported vazio
reg.append(int(resp[6:14], 16))  # reg-12 exported vazio

resp = get_data("0104002E0001")  # request exported ponta
reg.append(int(resp[6:14], 16))  # reg-13 exported ponta

resp = get_data("0104002F0001")  # request exported cheio
reg.append(int(resp[6:14], 16))  # reg-14 exported cheia

resp = get_data("0104006C0001")  # request voltage
reg.append(int(resp[6:10], 16))  # reg-15 voltage

# assemble data to be written to the file and sent via MQTT
msg = ("{:0>4d}".format( reg[0])  + "," +
       "{:0>2d}".format( reg[1])  + "," +
       "{:0>2d}".format( reg[2])  + "," +
       "{:0>2d}".format( reg[3])  + "," +
       "{:0>2d}".format( reg[4])  + "," +
       "{:0>12d}".format(reg[5])  + "," +
       "{:0>12d}".format(reg[6])  + "," +
       "{:0>12d}".format(reg[7])  + "," +
       "{:0>12d}".format(reg[8])  + "," +
       "{:0>12d}".format(reg[9])  + "," +
       "{:0>12d}".format(reg[10]) + "," +
       "{:0>12d}".format(reg[11]) + "," +
       "{:0>12d}".format(reg[12]) + "," +
       "{:0>12d}".format(reg[13]) + "," +
       "{:0>12d}".format(reg[14]) + "," +
       "{:0>4d}".format(reg[15])
       )

load_map.write(msg + "\n")       # write data to the file
load_map.close()                 # close file

# publish data via mqtt
client = paho.Client("PowerReader")    # open MQTT connection
if client.connect(MQTT_SERVER, 1883, 60) != 0:
    syslog.syslog(syslog.LOG_ERR, "Could not connect to MQTT broker")
    sys.exit(-1)
else:
    client.username_pw_set(username=MQTT_USER,password=MQTT_PASSWORD)
    client.publish(MQTT_TOPIC, msg, 0) # publish data
    client.disconnect()                # close MQTT connection

sys.exit(0)
