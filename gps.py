from pymysql import connections
import serial
import time
import string
import pymysql  # database
import datetime
import os
import paho.mqtt.client as mqtt

# os.system("sudo systemctl stop serial-getty@ttyS0.service")
# os.system("sudo systemctl stop serial-getty@serial0.service")
time.sleep(3)
class gps:
    def __init__(self, hosts, users, passwds, databases):
        self.connection = pymysql.connect(host=hosts, user=users, password=passwds, database=databases)
        self.cursor = self.connection.cursor()
        # self.ser = serial.Serial(ports, 9600, timeout=0.5)
        self.command = os.popen("sudo cat /dev/ttyAMA0", "r")
        self.lat = 0.000000
        self.lng = 0.000000
        self.i  = 0
        self.timestamp2 = 0
        self.distance = 0.0
        self.counter = 0
    def convert_lat_to_degrees(self, raw_value, sign):
        self.dd = int(raw_value/100)
        self.ss = raw_value - (self.dd * 100)
        self.LatDec = self.dd + self.ss / 60
        if sign == "S":
            self.LatDec = self.LatDec *(-1)
        self.positionLat = "%.6f" % (self.LatDec)
        return self.positionLat
    def convert_lng_to_degrees(self, raw_value, sign):
        self.dd = int(raw_value/100)
        self.ss = raw_value - (self.dd * 100)
        self.LngDec = self.dd + self.ss / 60
        if sign == "W":
            self.LngDec = self.LngDec *(-1)
        self.positionLng = "%.6f" % (self.LngDec)
        return self.positionLng
    def on_connect(self,client, userdata, flags, rc):
        print('connected (%s)' % client._client_id)
    def on_message(self,client, userdata, message):
        print('------------------------------')
        print('topic: %s' % message.topic)
        print('payload: %s' % message.payload)
        print('qos: %d' % message.qos)
    def on_publish(self,client,userdata,result):         
        print("data published \n")
        pass
    def calculate_ODO(self, speed, latitude, longtitude, current, battery):
        if self.counter == 1:
            delta_time = self.timestamp1 - self.timestamp2
        else:
            delta_time = self.timestamp2 - self.timestamp1
        ground_speed = speed * 1.85
        self.distance += (ground_speed) * (delta_time) / (60*60*1000)
        time_now = datetime.datetime.now().strftime('%H%M%S')
        self.data = "2.00B,MPFLAWN001,0,0.0,0,"+ str(round(self.distance,1)) +",3.8,0,0,0,0,0,0,0.00,0,0,"+ str(latitude) + ","+ str(longtitude) + "," + str(ground_speed) +",0,1,,0,"+ str(battery)+","+ str(current)+",0,0,0,1," + str(time_now) + ",,,,,,,,,,0,0,0,0,0,0,0"
        # print(self.data)
        self.client.loop_start()
        time.sleep(10)
        self.client.publish("normal", self.data, qos=0, retain=True)
    def run_main(self):
        while 1:
            self.cmt_read = "SELECT * FROM `GY25` WHERE 1;"
            self.cursor.execute(self.cmt_read)
            self.rows = self.cursor.fetchall()
            self.newdata = self.command.readline()
            # print(self.newdata)
            if str(self.newdata[0:6]) == "$GPRMC":
                self.newdata = str(self.newdata).replace("\r\n", "").split(",", 12)
                # print(self.newdata)
                if self.newdata[3] != "":
                    self.counter += 1
                    if self.counter == 1:
                        self.timestamp1 = time.mktime(datetime.datetime.now().timetuple())
                    else:
                        self.timestamp2 = time.mktime(datetime.datetime.now().timetuple())
                        self.counter = 0
                    self.now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.lat = float(self.newdata[3])
                    lat_minus_plus = self.newdata[4]
                    self.lng = float(self.newdata[5])
                    lng_minus_plus = self.newdata[6]
                    self.ground_speed = self.newdata[7]
                    self.lat_in_degrees = self.convert_lat_to_degrees(self.lat, lat_minus_plus)
                    self.lon_in_degrees = self.convert_lng_to_degrees(self.lng, lng_minus_plus)
                    # print("Lat:" + str(self.lat_in_degrees) + " lng:" + str(self.lon_in_degrees))
                    update_retrive = "UPDATE `GY25` SET `latitude` = " + str(self.lat_in_degrees) + ", `longitude` = " + str(self.lon_in_degrees) + " WHERE `GY25`.`id` = 1;"
                    # executing the quires
                    self.cursor.execute(update_retrive)
                    self.connection.commit()
                    retrive = "Select * from move_control;"
                    self.cursor.execute(retrive)
                    rows = self.cursor.fetchall()
                    level = rows[0][1]
                    self.current = rows[0][4]
                    self.battery = rows[0][11]
                    # self.cursor.execute("INSERT INTO record_data (lat, lng) VALUES (%s, %s)",(self.lat_in_degrees, self.lon_in_degrees))  # chạy lệnh update
                    # self.connection.commit()  
                    self.cursor.execute("INSERT INTO `data_map` (`lat`,`lng`, `level`) VALUES (%s, %s, %s)",(self.lat_in_degrees, self.lon_in_degrees, level))
                    self.connection.commit()  
                    # self.i += 1
                    # if self.i >= 10 and rows[0][6] == 1:   
                    #     #executing the quires
                    #     self.cursor.execute("INSERT INTO record_data (lat, lng) VALUES (%s, %s)",(self.lat_in_degrees, self.lon_in_degrees))  # chạy lệnh update
                    #     self.connection.commit()  # xác nhận update
                    #     self.i=0
                    # if level != 0:
                    #     self.cursor.execute("INSERT INTO `data_map` (`lat`,`lng`, `level`) VALUES (%s, %s, %s)",(self.lat_in_degrees, self.lon_in_degrees, level))
                    #     self.connection.commit()  # xác nhận update
                    # self.calculate_ODO(self.ground_speed,self.lat_in_degrees,self.lon_in_degrees, self.current, self.battery)
def main():
    lawn_control = gps("localhost","root","raspberry","tanker")
    while True:
        lawn_control.run_main()    
if __name__ == '__main__':
    main()


