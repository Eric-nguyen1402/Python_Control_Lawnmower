from __future__ import print_function
import serial
import requests
import time
import can  # add thư viện canbus
import pymysql  # database
import os
import math
import numpy as np
import RPi.GPIO as GPIO  # add library GPIO
from threading import Thread
from datetime import datetime
from math import floor
from ctypes import *
from adafruit_rplidar import RPLidar

time.sleep(5) 

class lawn_mower:
    def __init__(self, hosts, users, passwds, databases, chanels, bustypes):
        '''Initialize database and setting id , data frame canbus need to send on raspberry '''
        # khai báo database phpmyadmin
        self.connection = pymysql.connect(
                host=hosts, user=users, passwd=passwds, database=databases)
        self.cursor = self.connection.cursor()
        # Setup the RPLidar
        # PORT_NAME = '/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0'
        # self.lidar = RPLidar(None, PORT_NAME, timeout=3)
        self.max_distance = 300
        self.scan_data = [0] * 360
        self.error = 0
        self.counter = 0
        self.temp_b = 1
        self.temp_c = 0
        
        # Initialize protocol canbus 
        self.bus = can.interface.Bus(channel = chanels, bustype = bustypes)
        # List ID canbus
        self.id_canbus = [101, 201, 211 ,221, 301, 601, 611, 621]
        # Initialize messages that sends to canbus to control motor  

    def dextohex(self,decimal):
        return hex(decimal)[2:]

    def convert_current(self,hexnumber):
        x = int(hexnumber, 16)
        y = int('0xffff',16)
        values = int(hex(y - x + 1),16)
        return values

    def take_angle(self):
        '''Take the angle from database'''
        retrive_1 = "Select * from GY25;"
        # executing the quires
        self.cursor.execute(retrive_1)
        rows_1 = self.cursor.fetchall()
        return rows_1[0][3]

    def convert_angle(self):
        retrive_1 = "Select * from GY25;"
        # executing the quires
        self.cursor.execute(retrive_1)
        angle = self.cursor.fetchall()
        angles = int((float(angle[0][3])*100))
        result= hex((angles + (1 << 16)) % (1 << 16))
        value = [result[i:i+2] for i in range(0,len(result), 2)]
        if len(value) != 3:
            value.append('00')
        return value
    
    def canbus(self,data_msg):
        '''Function send canbus with data messages'''
        msg = can.Message(arbitration_id=301,
                        data=data_msg,
                        is_extended_id=False)  # initialize ID 
        self.bus.send(msg)  # send messages with initial ID

    # def rplidar(self):
    #     for scan in self.lidar.iter_scans():
    #         for (_, angle, distance) in scan:
    #             self.scan_data[min([359, floor(angle)])] = distance
    #         if self.scan_data[0] != 0:
    #             if self.scan_data[0] < self.max_distance and self.scan_data[3] < self.max_distance and self.scan_data[357] < self.max_distance and self.scan_data[355] < self.max_distance:
    #                 print("front obstacle")
    #                 self.canbus(self.data[2])
    #             elif  self.scan_data[87] < self.max_distance and self.scan_data[90] < self.max_distance and self.scan_data[93] < self.max_distance and self.scan_data[95] < self.max_distance:
    #                 print("left obstacle")
    #                 self.canbus(self.data_forward[3])
    #         print(self.rows[0][1])
    #         # if self.rows[0][1] != 5:
    #         #     break
    #     self.lidar.stop()
    #     self.lidar.disconnect()

    def action(self):  
        '''Main function do some task like : 
        -> Read data from database 
        -> Control motor via status button on website 
        -> Run Boundaries based on selection on website
         '''                   
        # queries for retrievint all rows
        update_retrive = "UPDATE `move_control` SET `level` = '0' WHERE `move_control`.`id` = 1;"
        update_retrives = "UPDATE `move_control` SET `auto_level` = '0' WHERE `move_control`.`id` = 1;"
        # executing the quires
        self.cursor.execute(update_retrive)
        self.connection.commit()
        self.cursor.execute(update_retrives)
        self.connection.commit()
        while True:
        # -----------------------------------------------read data from database--------------------------------------------------------
            # queries for retrievint all rows
            retrive = "Select * from move_control;"
            # executing the quires
            self.cursor.execute(retrive)
            self.rows = self.cursor.fetchall()
            
            check_connection = self.rows[0][1] - self.rows[0][0]
            print("level=",self.rows[0][1])
            self.angle_high = int(self.convert_angle()[1],16)
            self.angle_low = int(self.convert_angle()[2],16)
        # ---------------------------------------------assign value from database then send to canbus-------------------------------
            if check_connection >= 0:
                # forward straight
                if self.rows[0][1] == 1: data_msg = [1, 1, 0, 0, self.angle_low, self.angle_high, 0, 0]
                # forward right
                elif self.rows[0][1] == 2: data_msg = [1, 2, 0, 0, self.angle_low, self.angle_high, 0, 0]
                # forward left
                elif self.rows[0][1] == 3: data_msg = [1, 3, 0, 0, self.angle_low, self.angle_high, 0, 0]
                # reverse straight
                elif self.rows[0][1] == 4: data_msg = [2, 1, 0, 0, self.angle_low, self.angle_high, 0, 0]
                # reverse right
                elif self.rows[0][1] == 5: data_msg = [2, 2, 0, 0, self.angle_low, self.angle_high, 0, 0]
                # reverse left
                elif self.rows[0][1] == 6: data_msg = [2, 3, 0, 0, self.angle_low, self.angle_high, 0, 0]
                # circle CW
                elif self.rows[0][1] == 7: data_msg = [3, 1, 0, 0, self.angle_low, self.angle_high, 0, 0]
                # circle CCW
                elif self.rows[0][1] == 8: data_msg = [4, 1, 0, 0, self.angle_low, self.angle_high, 0, 0]
                # boost forward straight speed
                elif self.rows[0][1] == 11: data_msg = [1, 1, 1, 0, self.angle_low, self.angle_high, 0, 0]
                elif self.rows[0][1] == 12: data_msg = [1, 1, 2, 0, self.angle_low, self.angle_high, 0, 0]
                elif self.rows[0][1] == 13: data_msg = [1, 1, 3, 0, self.angle_low, self.angle_high, 0, 0]
                elif self.rows[0][1] == 14: data_msg = [1, 1, 4, 0, self.angle_low, self.angle_high, 0, 0]
                elif self.rows[0][1] == 15: data_msg = [1, 1, 5, 0, self.angle_low, self.angle_high, 0, 0]
                elif self.rows[0][1] == 16: data_msg = [1, 1, 6, 0, self.angle_low, self.angle_high, 0, 0]
                elif self.rows[0][1] == 17: data_msg = [1, 1, 7, 0, self.angle_low, self.angle_high, 0, 0]
                elif self.rows[0][1] == 18: data_msg = [1, 1, 8, 0, self.angle_low, self.angle_high, 0, 0]
                elif self.rows[0][1] == 19: data_msg = [1, 1, 9, 0, self.angle_low, self.angle_high, 0, 0]
                elif self.rows[0][1] == 20: data_msg = [1, 1, 10, 0, self.angle_low, self.angle_high, 0, 0]
                # boost reverse straight speed
                elif self.rows[0][1] == 31: data_msg = [2, 1, 1, 0, self.angle_low, self.angle_high, 0, 0]
                elif self.rows[0][1] == 32: data_msg = [2, 1, 2, 0, self.angle_low, self.angle_high, 0, 0]
                elif self.rows[0][1] == 33: data_msg = [2, 1, 3, 0, self.angle_low, self.angle_high, 0, 0]
                elif self.rows[0][1] == 34: data_msg = [2, 1, 4, 0, self.angle_low, self.angle_high, 0, 0]
                elif self.rows[0][1] == 35: data_msg = [2, 1, 5, 0, self.angle_low, self.angle_high, 0, 0]
                elif self.rows[0][1] == 36: data_msg = [2, 1, 6, 0, self.angle_low, self.angle_high, 0, 0]
                elif self.rows[0][1] == 37: data_msg = [2, 1, 7, 0, self.angle_low, self.angle_high, 0, 0]
                elif self.rows[0][1] == 38: data_msg = [2, 1, 8, 0, self.angle_low, self.angle_high, 0, 0]
                elif self.rows[0][1] == 39: data_msg = [2, 1, 9, 0, self.angle_low, self.angle_high, 0, 0]
                elif self.rows[0][1] == 40: data_msg = [2, 1, 10, 0, self.angle_low, self.angle_high, 0, 0]
                else: data_msg = [0, 0, 0, 0, self.angle_low, self.angle_high, 0, 0]
            else:
                data_msg = [0, 0, 0, 0, self.angle_low, self.angle_high, 0, 0]
                # queries for retrievint all rows
                update_retrive = "UPDATE `move_control` SET `level` = '0' WHERE `move_control`.`id` = 1;"
                # executing the quires
                self.cursor.execute(update_retrive)
                self.connection.commit()
        # ------------------------------------ send canbus everytime ----------------------------------
            for i in range(len(self.id_canbus)):  # send data value to fixed ID address
                if self.id_canbus[i] == 101 or self.id_canbus[i] == 201:
                    msg = can.Message(arbitration_id=self.id_canbus[i],
                                    data=[0, 0, 0, 0, 0, 0, 0, 0],
                                    is_extended_id=False)  # initialize ID value
                else:
                    msg = can.Message(arbitration_id=self.id_canbus[i],
                                    data=data_msg,
                                    is_extended_id=False)  # initialize ID value
                try:
                    self.bus.send(msg)  # send message with initial ID
                    # delay 0.4s when send 5 ID canbus each times
                    time.sleep(0.05)  
                    dataCanbus = self.bus.recv(0.0)
                    # Update response from canbus
                    if dataCanbus is None:
                        print("Don't Have Any Response From CANBUS")
                        # queries for retrievint all rows
                        update_retrive = "UPDATE `move_control` SET `error_can` = 'OK' WHERE `move_control`.`id` = 1;"
                        # executing the quires
                        self.cursor.execute(update_retrive)
                        self.connection.commit()
                    else:
                        if dataCanbus.arbitration_id == 102:
                            voltage = "0x" + \
                                    self.dextohex(dataCanbus.data[5]) + \
                                    self.dextohex(dataCanbus.data[4])
                            voltage2 = int(voltage, 16)
                            # queries for retrievint all rows
                            update_retrive = "UPDATE `move_control` SET `battery` = " + \
                                str(voltage2) + \
                                ",  `error_can` = 'OK' WHERE `move_control`.`id` = 1;"
                            self.cursor.execute(update_retrive)
                            self.connection.commit()
                        if dataCanbus.arbitration_id == 202:
                            current = "0x" + \
                                    self.dextohex(dataCanbus.data[1]) + \
                                    self.dextohex(dataCanbus.data[0])
                            # print("current",current)
                            if len(current) == 6:
                                if current != '0x00':
                                    current2 = self.convert_current(current)
                                    # print("current2",current2)
                                    # queries for retrievint all rows
                                    update_retrive = "UPDATE `move_control` SET `current` = " + \
                                        str(current2) + \
                                        ",  `error_can` = 'OK' WHERE `move_control`.`id` = 1;"
                                    self.cursor.execute(update_retrive)
                                    self.connection.commit()
                                else:
                                    # queries for retrievint all rows
                                    update_retrive = "UPDATE `move_control` SET `current` = " + \
                                        str('0.0') + \
                                        ",  `error_can` = 'OK' WHERE `move_control`.`id` = 1;"
                                    self.cursor.execute(update_retrive)
                                    self.connection.commit()
                    self.error = 0
                except can.CanError:
                    print(can.CanError)
                    # queries for retrievint all rows
                    update_retrive = "UPDATE `move_control` SET `error_can` = 'OK' WHERE `move_control`.`id` = 1;"
                    # executing the quires
                    self.cursor.execute(update_retrive)
                    self.connection.commit()
                    self.error = 1 
                   
def main():
    control = lawn_mower("localhost","root","raspberry","tanker",'can0','socketcan_native')
    while True:
        control.action()    
        
if __name__ == '__main__':
    main()