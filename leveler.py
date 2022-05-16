#!/usr/bin/python3
import time

import serial
import argparse
import sys

PORT = 'dev/ttyUSB0'
BAUD = 115200
serialport = None
FEED_RATE = 1000
DEBUG_MODE = False


def dbg_print(msg):
    if DEBUG_MODE:
        print(msg)


def init_serial():
    global serialport

    print('Initializing communication.')
    try:
        serialport = serial.Serial(PORT, BAUD, timeout=2)
        data = serialport.readline()
        while len(data) < 3:
            data = serialport.readline()

        print("RECEIVED: {}".format(data.decode()))

    except Exception as e:
        sys.exit("ERROR: {}".format(e))


def query_grbl(msg, timeout=None):
    global serialport

    if timeout is not None:
        serialport.timeout = timeout

    serialport.write(msg.encode())
    data = serialport.readline()
    return data.decode()


def get_status():
    response = query_grbl("?")
    print("Status: ", response.replace('\n', ''))


def offset(x=None, y=None, z=None, f=FEED_RATE):
    if x is None and y is None and z is None:
        return

    msg = "$j="

    if x is not None:
        msg += "x{} ".format(x)

    if y is not None:
        msg += "y{} ".format(y)

    if z is not None:
        msg += "z{} ".format(z)

    msg += "f{}\n".format(f)

    dbg_print("Sending:".format(msg.replace('\n', '')))
    dbg_print("Response: {}".format(query_grbl(msg)))


def level(max_z=20):
    probe_touch_msg = "Pn:P"
    status = query_grbl("?")

    if probe_touch_msg not in status:
        offset(z=-max_z, f=50)

        while probe_touch_msg not in status:
            status = query_grbl("?")

        dbg_print("Status:".format(status))
        query_grbl("!")


def home(max_x=500, max_y=500, f=300):
    limit_x_msg = "Pn:X"
    limit_y_msg = "Pn:Y"

    status = query_grbl("?")
    # Move X to the limit switch
    if limit_x_msg not in status:
        offset(x=-max_x, f=f)

        while limit_x_msg not in status:
            status = query_grbl("?")

        query_grbl("!")
        dbg_print("Status:".format(status))

    # Release the limit switch
    offset(x=5, f=50)
    while limit_x_msg in status:
        status = query_grbl("?")

    query_grbl("!")
    dbg_print("Status:".format(status))

    # Move Y to the limit switch
    if limit_y_msg not in status:
        offset(y=-max_y, f=f)

        while limit_y_msg not in status:
            status = query_grbl("?")

        query_grbl("!")
        dbg_print("Status:".format(status))

    # Release the limit switch
    offset(y=5, f=50)
    while limit_y_msg in status:
        status = query_grbl("?")

    query_grbl("!")
    dbg_print("Status:".format(status))


# Setup command line parameters
parser = argparse.ArgumentParser(description='Leveling CNC router using GRBL commands and a Z axis probe.')
parser.add_argument('-l', '--level', help='Do the leveling. Touches the conductive surface with the milling tool.', action='store_true')
parser.add_argument('-p', '--port', help='CNC router port.', default=PORT)
parser.add_argument('-x', '--x', help='Move along X axis')
parser.add_argument('-y', '--y', help='Move along Y axis')
parser.add_argument('-z', '--z', help='Move along Z axis')
parser.add_argument('-f', '--f', help='Set feed rate.', default=FEED_RATE)
parser.add_argument('-0', '--zero', help='Move to x=0, y=0', action='store_true')
parser.add_argument('-v', '--verbose', help='Write additional debug messages', action='store_true')

args = parser.parse_args()

# Parse the params
PORT = '/dev/{}'.format(args.port.replace('dev', '').replace('/', ''))
LEVEL_FLAG = args.level
HOME_FLAG = args.zero
DEBUG_MODE = args.verbose

try:
    MOVE_X = float(args.x)
except:
    MOVE_X = None

try:
    MOVE_Y = float(args.y)
except:
    MOVE_Y = None

try:
    MOVE_Z = float(args.z)
except:
    MOVE_Z = None

try:
    FEED_RATE = int(args.f)
except:
    FEED_RATE = 100

dbg_print("Accepting following parameters:\n  port = {},\n  leveling = {},\n  moving to home = {},"
          "\n  offset_x = {},\n  offset_y = {},\n  offset_z = {},\n  feed rate = {}"
          "".format(PORT, LEVEL_FLAG, HOME_FLAG, MOVE_X, MOVE_Y, MOVE_Z, FEED_RATE))

init_serial()
get_status()

offset(MOVE_X, MOVE_Y, MOVE_Z)

if LEVEL_FLAG:
    level()

if HOME_FLAG:
    home()

get_status()

serialport.close()
