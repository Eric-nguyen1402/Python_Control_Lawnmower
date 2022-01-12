import time
import serial
import pymysql
import os
from datetime import datetime

time.sleep(3)
ser = serial.Serial('/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0', 115200, timeout=1)
con_update = pymysql.connect(host="localhost", user="root", passwd="raspberry", database="tanker")
cursor_update = con_update.cursor()
arr = [0.0, 0.0]
x = 0.0
y = 0.0
z = 0.0
distance = 0
a = 0
while 1:
    ans = ("get\n")
    ans = ans.encode("utf-8")
    ser.write(ans)
    readOuts = ser.readline().decode('utf-8').split(",", 4)
    # print(readOuts)
    if len(readOuts) == 4:
        distance = int(readOuts[0])
        x = float(readOuts[2])
        y = float(readOuts[1])
        z = float(readOuts[3])
    update_retrive = "UPDATE `GY25` SET `X` = " + str(x) + ", `Y` = " + str(y) + ", `Z` = " + str(z) +" WHERE `GY25`.`id` = 1;"
    # executing the quires
    cursor_update.execute(update_retrive)
    con_update.commit()
    # khai báo lệnh update data vào database
    update_retrive = "UPDATE `move_control` SET `ultrasonic` = " + str(distance) + " WHERE `move_control`.`id` = 1;"
    # executing the quires
    cursor_update.execute(update_retrive)
    con_update.commit()
    # print("x = " + str(x), "y = " + str(y), "z = " + str(z), "distance " + str(distance))
    
    retrive = "Select * from move_control;"
    # executing the quires
    cursor_update.execute(retrive)
    rows = cursor_update.fetchall()
    check_connection = rows[0][1] - rows[0][0]
    level = rows[0][1]
    # print(check_connection)
    # ---------------------------------------------send value to draw a chart-------------------------------
    if check_connection > 0:
             a = a + 1
             if a == 5:
                formatted_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor_update.execute("INSERT INTO `data_XYZ` (`X`,`Y`, `Z`,`Record_time_start`,`Level`) VALUES (%s, %s, %s, %s, %s)",(x,y,z,formatted_date,level))
                con_update.commit()
                #print("x = " + str(x),"y = " + str(y),"z = " + str(z),"time = " + str(formatted_date), "level" + str(level))
                a = 0

