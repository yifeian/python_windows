import os.path
import time,sys
import datetime
import argparse
import threading
import re
import signal
import difflib

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
        self.mysendline = None
        self.mygetline = None
        self.number = 0

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

        My_log.send_cmd("Now  {} is Open, baudrate is {}".format(self.comport,self.baud))

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

    # Send an AT Command, store output data and response in a tuple and return it
    def send_raw(self, data, TIMEWAITING=.3, resp=False):
        self.com.flushInput()
        self.com.flushOutput()
        self.com.write(data)
        My_log.send_cmd('send data')
        My_log.send_cmd(data)
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

    # Read the output data and response from DUT
    def read_raw(self,timeout=None):
        if timeout is not None:
            endtime = time.time() + timeout
        while True:  # try 10 times in 1s interval
            if timeout is not None and time.time() > endtime:
                My_log.send_cmd('read data error')
                My_log.send_cmd('size is {}'.format(size))
                print('test end')
                sys.exit()
                #break
            time.sleep(0.1)
            size = self.com.inWaiting()
            if size >= 2000:
                break
            else:
                continue
        raw = self.com.read(size)
        My_log.send_cmd(raw)
        return raw

    def waitresponse(self,timeout=None):
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

    
    def wait_raw(self,timeout=None):
        if timeout is not None:
            endtime = time.time() + timeout
        while(True):
            if timeout is not None and time.time() > endtime:
                return False
            line = self.read_raw(5)
            if line:
                self.mygetline = str(line)
                break
            else:
                continue    
        return line

    def difflib_test(self):
        print_time = 0
        diff = difflib.SequenceMatcher(None,self.mysendline,self.mygetline)
        for block in diff.get_matching_blocks():
            print_time+=1
            My_log.send_cmd("a[%d] and b[%d] match for %d elements" % block)
        if print_time != 2:
            My_log.send_cmd('data error ')

    # Clear the Input and Output buffer, and close the serial connection.
    def close(self):
        self.com.flushInput()
        self.com.flushOutput()
        self.com.close()

def exit(signal_num,frame):
    print('function exit\n')
    sys.exit() 


if __name__ == '__main__':
    signal.signal(signal.SIGINT,exit)
    parser = argparse.ArgumentParser(description='com test')
    parser.add_argument('COM',help='input the com port')
    parser.add_argument('baud',help = 'input the baud')
    parser.add_argument('sendbytes',help = 'input the sendbytes')

    My_log = my_log()
    My_com = my_com(parser.parse_args().COM,parser.parse_args().baud)
    My_com.open()
    send_data = b'0'*(int(parser.parse_args().sendbytes))

    while True:
        My_com.number+=1
        My_log.send_cmd('test rand {}'.format(My_com.number))
        My_com.mysendline = str(send_data)
        My_com.send_raw(send_data)
        if My_com.wait_raw() == None:
            pass
        else:
            My_com.difflib_test()
        time.sleep(0.2)
        

        







        