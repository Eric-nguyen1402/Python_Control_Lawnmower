import os
from math import floor
import time
from adafruit_rplidar import RPLidar
# from rplidar import RPLidar

# Setup the RPLidar
PORT_NAME = '/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0'
lidar = RPLidar(None, PORT_NAME, timeout=3)
counter = 0
max_distance = 300

def process_data(data):
    print(data)
scan_data = [0] * 360
try:
    #    print(lidar.get_info())
    for scan in lidar.iter_scans():
        for (_, angle, distance) in scan:
            scan_data[min([359, floor(angle)])] = distance
        if scan_data[0] != 0:
            if scan_data[0] < max_distance and scan_data[3] < max_distance and scan_data[357] < max_distance and scan_data[355] < max_distance:
                print("front obstacle")
                time.sleep(0.05)
            elif  scan_data[87] < max_distance and scan_data[90] < max_distance and scan_data[93] < max_distance and scan_data[95] < max_distance:
                print("left obstacle")
                time.sleep(0.05)

except KeyboardInterrupt:
    print("Stopping.")
lidar.stop()
lidar.disconnect()

