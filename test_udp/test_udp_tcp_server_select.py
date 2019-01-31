import selectors
import socket
import datetime
import time
import os
import sys
import signal

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

log = my_log()

sel = selectors.DefaultSelector()
connBook = {}
def read_udp(sock,mask):
    data, address = sock.recvfrom(65535)
    text = data.decode('utf-8',"ignore")

    log.send_cmd('recv {} bytes from {},{}'.format(len(data),address,text))
    sock.sendto(data,address)

def accept(sock, mask):
    conn, addr = sock.accept()  # Should be ready
    time_now = int(time.time())
    connBook[conn] = time_now
    #print(connBook)
    log.send_cmd( '{}:{} connected'.format(addr[0],addr[1]))
    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ, read)

def read(conn, mask):
    try:
        addr,port = conn.getpeername()
        while True:
            try:
                data = conn.recv(1024)  # Should be ready
                if not data:
                    raise ConnectionResetError
                #print('echoing', repr(data), 'to', conn)
                test = data.decode('utf-8',"ignore")
                log.send_cmd('recv {} bytes from {}:{},{}'.format(len(data),addr,port,test))
                conn.sendall(data)  # Hope it won't block
                time_now = int(time.time())
                connBook[conn] = time_now
            except BlockingIOError:
                return
    except ConnectionResetError :
        log.send_cmd('closing {}:{}'.format(addr,port) )
        if conn in connBook:
            connBook.pop(conn)
            sel.unregister(conn)
        conn.close()
    except OSError:
        #print(conn)
        log.send_cmd('recv rst ' )
        if conn in connBook:
            connBook.pop(conn)
            sel.unregister(conn)
        conn.close()

def hander_signal(signal_num,frame):
    time_now = int(time.time())
    for key, value in list(connBook.items()):
        if  time_now-value > 240:
            sel.unregister(key)
            connBook.pop(key)
            key.close()
    print('10 secondes ')
    signal.alarm(300)

def exit(signal_num,frame):
    print('function exit\n')
    sys.exit()
    
sock_tcp = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sock_tcp.setblocking(False)
sock_tcp.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
sock_tcp.bind(('', 7000))
sock_tcp.listen(300)


sock_udp = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
sock_udp.setblocking(False)
sock_udp.bind(('', 7000))


sel.register(sock_tcp, selectors.EVENT_READ, accept)
sel.register(sock_udp, selectors.EVENT_READ, read_udp)

signal.signal(signal.SIGINT,exit)
signal.signal(signal.SIGALRM,hander_signal)
signal.alarm(300)

while True:
    events = sel.select()
    for key, mask in events:
        callback = key.data
        callback(key.fileobj, mask)