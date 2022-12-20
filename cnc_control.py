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


def serial_read(timeout=0.1):
    global serialport

    serialport.timeout = 0.01

    start = time.time()
    data = ""
    while not data.endswith("\n") and not data.endswith(">") and (time.time() - start) < timeout:
        temp = serialport.read(1024).decode()
        if len(temp) > 0:
            data += temp
    return data


def init_serial():
    global serialport

    print('Initializing communication.', flush=True)
    try:
        serialport = serial.Serial(PORT, BAUD)
        data = serial_read(timeout=3)

        print("RECEIVED: {}".format(data), flush=True)

    except Exception as e:
        sys.exit("ERROR: {}".format(e))


def query_grbl(msg, timeout=1):
    global serialport

    dbg_print("Sending: {}".format(msg.replace('\n', '')))
    serialport.write(msg.encode())
    data = serial_read(timeout=timeout)
    return data


def get_status(wait_for_idle=False):

    response = query_grbl("?")
    if wait_for_idle:
        while not response.startswith("<Idle"):
            response = query_grbl("?")

    status_text = response.replace('\n', '')
    status_data = response.split("|")
    off_x = 0
    off_y = 0
    off_z = 0
    for data in status_data:
        if data.startswith("MPos:"):
            [off_x, off_y, off_z] = data.split(":")[1].split(",")
            break

    float_x = float(off_x)
    float_y = float(off_y)
    float_z = float(off_z)

    print("Status: {}\n\tOffset:{:.2f},{:.2f},{:.2f}".format(status_text, float_x, float_y, float_z))


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


def laser_ctrl(power):
    try:
        pwr = int(power)
    except:
        pwr = 0

    if pwr:
        msg = f"M03 S{pwr}\n"
    else:
        msg = "M05\n"

    response = query_grbl(msg)
    dbg_print("Response:".format(response))


def remove_comment(string):
    if string.find(';') == -1:
        return string
    else:
        return string[:string.index(';')]


def stream(file_path):
    global serialport

    try:
        dbg_print(f'Opening gcode file: {file_path}')
        f = open(file_path, 'r')
        dbg_print('Sending gcode')
        for line in f:
            ln = remove_comment(line)
            ln = ln.strip()  # Strip all EOL characters for streaming
            if not ln.isspace() and len(ln) > 0:
                dbg_print('Sending: ' + ln)

                serialport.write((ln + '\n').encode())  # Send g-code block
                grbl_out = serialport.readline()  # Wait for response with carriage return
                dbg_print(' : ' + grbl_out.decode().strip())
        f.close()
    except Exception as e:
        print("ERROR: ", e)


# Setup command line parameters
parser = argparse.ArgumentParser(
    description='Leveling CNC router using GRBL commands and a Z axis probe. NOTE: Please use "=" to assign values'
)
parser.add_argument('-l', '--level', help='Do the leveling. Touches the conductive surface with the milling tool.', action='store_true')
parser.add_argument('-p', '--port', help='CNC router port.', default=PORT)
parser.add_argument('-x', '--x', help='Move along X axis')
parser.add_argument('-y', '--y', help='Move along Y axis')
parser.add_argument('-z', '--z', help='Move along Z axis')
parser.add_argument('-f', '--f', help='Set feed rate.', default=FEED_RATE)
parser.add_argument('-0', '--zero', help='Move to x=0, y=0', action='store_true')
parser.add_argument('-v', '--verbose', help='Write additional debug messages', action='store_true')
parser.add_argument('-g', '--gcode', help='G-code file path. If other commands included, this is done last.',
                    required=False)
parser.add_argument('-b', '--beam', help='Laser beam intensity', type=int)

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

dbg_print(
    f"Accepting following parameters:\n  port = {PORT},\n  leveling = {LEVEL_FLAG},\n  moving to home = {HOME_FLAG},"
    "\n  offset_x = {MOVE_X},\n  offset_y = {MOVE_Y},\n  offset_z = {MOVE_Z},\n  feed rate = {FEED_RATE}, "
    "gcode_file = {args.gcode}"
)

init_serial()
get_status()

offset(MOVE_X, MOVE_Y, MOVE_Z)

if LEVEL_FLAG:
    level()

if HOME_FLAG:
    home()

if args.beam:
    laser_ctrl(args.beam)

if args.gcode is not None:
    stream(args.gcode)

get_status(wait_for_idle=True)

serialport.close()
