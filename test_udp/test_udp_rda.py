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
    def read(self,compare=0, timeout=0):
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
                if compare == 1:
                    if not raw.upper().startswith('+RECV'):
                        continue
                break
            else:
                continue
        return raw

    def recv_response(self):
        rsp = 0
        timeout = 0
        re_transtime = 0
        time_ok = 0
        while (True):
            line = self.read(rsp,timeout)
            if isinstance(line, str):
                if line.upper().startswith("+TSOST"):
                    timeout = 0
                    self.now_time = int(time.time()) - time_ok
                    resline = re.findall("\d+", line)
                    if int(resline[1]) == self.send_seq:
                        self.send_cmd("between send and ack,time is {}s".format(self.now_time))
                        rsp = 1
                        if re_transtime == 0:
                            timeout = 3

                        elif re_transtime == 1:
                            timeout = 5

                        elif re_transtime == 2:
                            timeout = 9
                        else:
                            continue
                        
                elif line.upper().startswith("OK"):
                    time_ok = int(time.time())
                    continue
                elif line.upper().startswith("+RECV"):
                    reline =  re.findall("\d+",line.upper())
                    if reline[0] == '0123456789':
                        if int(reline[2]) == self.send_seq:
                            self.time = int(time.time()) - self.last_time
                            rsp = 0
                            timeout = 0
                            break
                        else:
                            self.time = int(time.time()) - self.last_time
                            rsp = 0
                            timeout = 0
                            self.send_cmd('out-of-order')
                            break
                else:
                    pass
            elif line == False:
                if rsp == 1:
                    re_transtime += 1
                    self.re_transtimes += 1
                    if re_transtime == 3:
                        self.re_transtimes -= 1
                        re_transtime = 0
                        self.time = int(time.time()) - self.last_time
                        self.send_cmd("break fot timeout")
                        break
                    self.send('AT+TSOST=1,"203.195.244.181",7000,{},"{}",{}'.format(len(My_com.senddata)+5, My_com.senddata, self.send_seq))
                    rsp = 0
                    timeout = 0
                    continue

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
                pass
            else:
                self.send('AT+TRB')
                time.sleep(30)
                continue
            self.send('AT+TSOCR="DGRAM",17,6000,1')
            if 'OK' in self.wait_response('OK', 10):
                break
            else:
                time.sleep(2)
                continue

    def test_send(self):
        while True:
            self.send('at+tuestats="CELL"')
            if 'OK' == self.wait_response('OK',timeout=5):
                pass
            self.senddata = "+RECV:0123456789abcde&MCU+D21100&MesCNT:{}".format(My_com.send_seq)
            self.send('AT+TSOST=1,"203.195.244.181",7000,{},"{}",{}'.format(len(My_com.senddata)+5, My_com.senddata, self.send_seq))
            self.last_time = int(time.time())
            self.recv_response()
            if self.time >= 10:
                self.send_cmd("check ue status")
            if self.time >= 30:
                self.send_cmd("overtime")
            self.send_cmd("seq:{},time:{},retrans times:{}".format(self.send_seq,self.time,self.re_transtimes))
            self.re_transtimes = 0
            self.send_seq += 1
            sleep_time = 30-self.time
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



if __name__ == '__main__':
    signal.signal(signal.SIGINT, exit)
    parser = argparse.ArgumentParser(description='udp test')
    parser.add_argument('COM', help='input the com port',default='com4')
    parser.add_argument('baud', help='input the baud',default=57600)


    My_com = my_com(parser.parse_args().COM,parser.parse_args().baud)
    My_com.open()
    My_com.create_sock()
    My_com.test_send()




