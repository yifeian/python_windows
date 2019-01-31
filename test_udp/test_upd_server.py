import select
import socket 
import logging
import sys
import threading
import argparse
from time import sleep

'''
server select 

    def run(self):
        while True:
            readable, writeable, exceptional = select.select(self.socketfd, [], [], g_select_timeout)
            if not (readable or writeable or exceptional):
                continue
            for s in readable:
                if s is self.server:
                    data, address = s.recvfrom(self.__buffer_size)
                    text = data.decode("ascii")
                    print("client {} data {!r}".format(address, text))
                    self.client_info.append(str(address))
                    print(self.client_info)
                if s is self.__fileno:
                    data = sys.stdin.read()
                    print("recev data {!r}".format(text))
                    if data and len(self.client_info):
                        text = data.encode("ascii")
                        for i in len(self.client_info):
                            self.server.sendto(text,tuple(self.client_info[i]))
                            print("send to self.client_info[i]")
            for fd in writeable:
                pass
            
            for fd in exceptional:
                pass
'''
g_select_timeout = 10

class Server(object):
    def __init__(self, host='',port=7000,timeout=2,client_nums=10):
        self.__host = host
        self.__port = port
        self.__timeout = timeout
        self.__client_nums = client_nums
        self.__buffer_size = 65535
        self.__count = 0
        self.__isexist = 0
        self.__quit = 1

        self.server_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server_tcp.bind((self.__host, self.__port))
        except:
            raise "tcp bind error"
        self.server_tcp.listen(1024)

        self.server_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #self.server.setblocking(True)
        self.server_host_udp = (self.__host, self.__port)

        try:
            self.server_udp.bind(self.server_host_udp)
        except:
            raise
        
        self.socketfd = [self.server_tcp,self.server_udp]
        self.client_info = {}
        
    def send_msg(self):
        while True:
            data = sys.stdin.readline()
            if data and len(self.client_info):
                text = data.encode("ascii")
                print(text)
                print("input data {!r}".format(text))
                for cli in self.client_info:
                    print(type(cli))
                    self.server.sendto(text, self.client_info[cli])
                    print("send to {}".format(self.client_info[cli]))
                    sleep(1)
            elif data:
                text = data.encode("ascii")

                print("input data {!r}".format(text))

    def recv_msg(self):
        while True:
            data, address = self.server.recvfrom(self.__buffer_size)
            text = data.decode("ascii")
            print("client {} data {!r}".format(address, text))

            for cli in self.client_info:
                if self.client_info[cli] == address:
                    self.__isexist = 1
            if not self.__isexist:
                self.client_info[self.__count % self.__client_nums] = address
                self.__count += 1
                self.__isexist = 0
            print(self.client_info)
            if self.__count >= self.__client_nums:
                self.__count = 0

    def run(self):
        while True:
            readable, writeable, exceptional = select.select(self.socketfd, [], [], 0)
            if not (readable or writeable or exceptional):
                continue
            for s in readable:
                if s is self.server_tcp:
                    
                    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='udp server test')
    parser.add_argument('-p',metavar='PORT',type=int,default=7000,help='UDP port (default 7000)')
    args = parser.parse_args()
    Server(port=args.p).run()

          





    
