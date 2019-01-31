import os.path
import time
import datetime
import argparse
import threading
import re
import sys
import signal


'''
                elif rsp == 2:
                    self.send('at+cfun=0')
                    if '+CEREG' in self.wait_response('+CEREG', 20):
                        pass
                    time.sleep(1)
                    self.send('at+cfun=1')
                    if '+CEREG' in self.wait_response('+CEREG', 20):
                        pass
                    time.sleep(1)
                    self.send('AT+TSOCL=1')
                    if 'OK' in self.wait_response('OK', 10):
                        pass
                    self.create_sock() 
                    self.send('AT+TSOST=1,"148.70.31.180",7000,{},"{}",{}'.format(len(My_com.senddata)+5, My_com.senddata, self.send_seq))
                    rsp = 0
                    timeout = 0
                    continue
'''

class my_com(object):

    def __init__(self, port, baudrate):
        self.comport = port
        self.baud = baudrate
        self.timeout = 3
        self.com = None
        self.data = None
        self.atcommand = None
        self.rsp = "OK"
        self.senddata = "867352040569573&MCU+D21100&MesCNT:238"
        self.send_seq = 1
        self.last_time = 0
        self.now_time = 0
        self.time = 0
        self.acked = 0
        self.fh = None
        self.re_transtimes = 0
        self.rq = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        self.path_name = os.path.dirname(sys.argv[0]) + '\\' + self.rq + '.log'
        try:
            self.fh = open(self.path_name, 'w')
        except:
            self.fh = None
        self.start_time = time.time()

    def __enter__(self):
        self.open(self.timeout)
        return self

    def __del__(self):
        if self.fh is not None:
            self.fh.close()

    def __write(self, out):
        if self.fh is not None:
            self.fh.write(out)
            self.fh.flush()
        sys.stdout.write(out)


    def __exit__(self, typeof, value, tbx):
        self.close()

    def send_cmd(self, line):
        stamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.__write("[%s]>>> %s\n" % (stamp, line.strip()))

    # Connect to the specified AT COM Port with a required Timeout
    def open(self, timeout=10):
        self.timeout = timeout
        try:
            import serial
        except ImportError:
            raise Exception('Not able to find PySerial installation or may be is not installed.')

        self.com = serial.Serial(self.comport, self.baud, timeout=10)
        self.send_cmd("Now  {} is Open, baudrate is {}".format(self.comport, self.baud))

    # Send an AT Command, store output data and response in a tuple and return it
    def send(self, atcommand, TIMEWAITING=.3, resp=False):

        self.com.flushInput()
        self.com.flushOutput()
        self.atcommand = atcommand
        self.com.write((self.atcommand + "\r\n").encode())
        self.send_cmd(atcommand)
        if resp:
            time.sleep(TIMEWAITING)
            return self.read()
        else:
            return None

    # Read the output data and response from DUT
    def read(self, timeout=0):
        if timeout is not 0:
            endtime = time.time() + timeout
        while True:  # try 10 times in 1s interval
            if timeout is not 0 and time.time() > endtime:
                return False
            time.sleep(0.1)
            size = self.com.inWaiting()
            if size > 0:
                raw = self.com.readline().decode().strip()
                if not raw.upper().startswith('AT'):
                    self.send_cmd(raw)
                break
            else:
                continue
        return raw

    def recv_response(self):
        timeout = 0
        while (True):
            line = self.read(timeout)
            if isinstance(line, str):
                if line.upper().startswith("+COAP"):
                    resline = re.findall("\d+", line)
                    data = ''.join(resline)
                    if int(data) != 454:
                        self.send_cmd('coap get data size error')
                        continue
                    continue

                elif line.upper().startswith("OK"):
                    self.now_time = int(time.time())
                    break
                elif line.upper().startswith("+CME ERROR"):
                    self.send_cmd('coap get data error')
                    self.now_time = int(time.time())
                    break
                

    def wait_response(self, rsp=None, timeout=None):
        if timeout is not None:
            endtime = time.time() + timeout
        while (True):
            if timeout is not None and time.time() > endtime:
                return 'False'
            line = self.read()
            if isinstance(line, str):
                line = line.upper()
            else:
                continue
            if rsp is not None:
                if line.upper().startswith(rsp):
                    break
            elif '+CME ERROR' in line or 'ERROR' in line or 'COMMAND NO RESPONSE!' in line or rsp in line:
                break
            else:
                continue
        return line

    
    def create_sock(self):
        while True:
            self.send('AT+CGACT=1,1')
            if 'OK' in self.wait_response('OK', 5):
                break
            else:
                self.send('AT+TRB')
                time.sleep(30)
                continue


    def test_send(self):
        while True:
            self.send('AT^COAPGET="coap://203.195.244.181/test","-p 5683"')
            self.last_time = int(time.time())
            self.recv_response()
            self.time = self.now_time - self.last_time
            sleep_time = 6-self.time
            print(sleep_time)
            if sleep_time >= 0:
                time.sleep(sleep_time)
            else:
                continue

    def close(self):
        self.com.flushInput()
        self.com.flushOutput()
        self.com.close()

def exit(signal_num,frame):
    print("func exit")
    sys.exit()

signal.signal(signal.SIGINT, exit)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='com test')
    parser.add_argument('COM', help='input the com port',default='com4')
    parser.add_argument('baud', help='input the baud',default=57600)


    My_com = my_com(parser.parse_args().COM,parser.parse_args().baud)
    My_com.open()
    My_com.create_sock()
    My_com.test_send()




