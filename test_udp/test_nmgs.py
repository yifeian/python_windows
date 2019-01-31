import os.path
import time,sys
import datetime
import argparse
import threading
import socket
import re


class RelayControl(object):
    """ Open/close relay channel through socket """

    def __init__(self):
        self.host = "localhost"
        self.port = 9999
        self.bufsize = 1024
        self.addr = (self.host, self.port)

    def __conn_host(self, masg):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(self.addr)
        client.send(masg.strip().encode())
        data = client.recv(self.bufsize).decode()
        if 'OK' not in data:
            client.close()
            raise Exception("Error when %s" % masg)
        client.close()

    def open_channel(self, index=1):
        self.__conn_host('open %d' % index)

    def close_channel(self, index=1):
        self.__conn_host('close %d' % index)


""" Global object"""
relayCtrl = RelayControl()

class my_log(object):
    def __init__(self):
        self.fh = None
        self.rq = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        self.path_name = os.path.dirname(sys.argv[0])+ '\\' + self.rq + '.log'
        try:
            self.fh = open(self.path_name, 'w')
        except:
            self.fh = None
        self.start_time = time.time()

    def __del__(self):
        if self.fh is not None:
            self.fh.close()
    
    def __write(self, out):
        if self.fh is not None:
            self.fh.write(out)
            self.fh.flush()
        sys.stdout.write(out)

    def send_cmd(self, line):
        stamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.__write("[%s]>>> %s\n" % (stamp, line.strip()))
    
class my_com(object):
    
    def __init__(self, port, baudrate):
        self.comport = port
        self.baud = baudrate
        self.timeout = 3
        self.com = None
        self.data = None
        self.atcommand = None
        self.rsp = "OK"
        

    def __enter__(self):
        self.open(self.timeout)
        return self

    def __exit__(self, typeof, value, tbx):
        self.close()
    
    # Connect to the specified AT COM Port with a required Timeout
    def open(self,timeout=10):
        self.timeout = timeout
        try:
            import serial
        except ImportError:
            raise Exception('Not able to find PySerial installation or may be is not installed.')

        self.com = serial.Serial(self.comport, self.baud, timeout=10)
        My_log.send_cmd("{} is Open, baudrate is {}".format(self.comport,self.baud))

    # Send an AT Command, store output data and response in a tuple and return it
    def send(self, atcommand, TIMEWAITING=.3, resp=False):
        self.com.flushInput()
        self.com.flushOutput()
        self.atcommand = atcommand
        self.com.write((self.atcommand + "\r\n").encode())
        My_log.send_cmd(atcommand)
        if resp:
            time.sleep(TIMEWAITING)
            return self.read()
        else:
            return None

    # Read the output data and response from DUT
    def read(self):
        
        while True:  # try 10 times in 1s interval
            time.sleep(0.1)
            size = self.com.inWaiting()
            if size > 0:
                break
            else:
                continue
        raw = self.com.readline().decode().strip()
        if not raw.upper().startswith('AT'):
            My_log.send_cmd(raw)
        return raw
        

    def waitresponse(self,timeout):
        if timeout is not None:
            endtime = time.time() + timeout
        while(True):
            if timeout is not None and time.time() > endtime:
                return False
            line = self.read()
            if type(line) == str:
                line = line.upper() 
            else:
                continue           
            if 'ERROR' in line or 'COMMAND NO RESPONSE!' in line or '+CME ERROR' in line or 'OK' in line:
                break
        return line

    def waitres_nmgs_response(self,rsp,timeout):
        if timeout is not None:
            endtime = time.time() + timeout
        while(True):
            if timeout is not None and time.time() > endtime:
                return False
            line = self.read()
            if isinstance(line, str):
                line = line.upper() 
            else:
                continue 
            if '+CME ERROR' in line or 'ERROR' in line or 'COMMAND NO RESPONSE!' in line or rsp in line:
                break
        return line
    
    # Clear the Input and Output buffer, and close the serial connection.
    def close(self):
        self.com.flushInput()
        self.com.flushOutput()
        self.com.close()

def waitServerRequest():
    fails = 0
    i = 0
    global index
    while True:
        line = My_com.read()
        if isinstance(line, str):
            if line.strip().upper().startswith("+CSCON:"):
                data = re.findall(r'\d+',line)
                if data[0] == '0':
                    My_log.send_cmd("PSM mode ")
                    time.sleep(5)
                    My_log.send_cmd("Wake up ")
                    relayCtrl.open_channel()
                    time.sleep(1)
                    relayCtrl.close_channel()
                    index = 1
                    time.sleep(1)
            if line


if __name__ == '__main__':
    
    PSMindex = 0
    STATSindex = 0
    parser = argparse.ArgumentParser(description='com test')
    parser.add_argument('COM',help='input the com port')
    parser.add_argument('baud',help = 'input the baud')

    My_log = my_log()
    My_com = my_com(parser.parse_args().COM,parser.parse_args().baud)
    My_com.open()

    My_com.send('AT+PING="180.101.147.115",5,64,3')
    My_com.waitresponse(20)

    t = threading.Thread(target=waitServerRequest, name='waitServerRequest')
    t.start()

    while True:
        if index == 1:
            print('ping ')
            index = 0
            My_com.send('AT+PING="180.101.147.115",5,64,3')
            time.sleep(30)
            index = 1
            relayCtrl.open_channel()
            time.sleep(1)
            relayCtrl.close_channel()

        