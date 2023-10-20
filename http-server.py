# Uncomment this to pass the first stage
import socket
import threading
import sys
import os
from queue import Queue


class ReadThread(threading.Thread):
    def __init__(self, file, result):
        threading.Thread.__init__(self)
        self.file = file
        self.result = result

    def run(self):
        with open(self.file, 'rb') as file:
            data = file.read()
            self.result = data

class WriteThread(threading.Thread):
    def __init__(self, file, content):
        threading.Thread.__init__(self)
        self.file = file
        self.content = content

    def run(self):
        with open(self.file, 'w') as file:
            file.write(self.content)

threads = []

def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    while True:
        server_socket = socket.create_server(
        ("localhost", 4221), reuse_port=True)
        conn, addr = server_socket.accept()
        try:
            rec = [i for i in conn.recv(4096).decode('utf-8').split('\r\n') if i]
            while rec and not rec[0]:
                rec.pop(0)
            if not rec:
                resp = b'HTTP/1.1 400 Bad Request\r\n\r\n'
            else:
                req, dir, protocol = rec[0].split(' ')
                resp = None
                print(rec)
                if dir == '/':
                    resp = b'HTTP/1.1 200 OK\r\n\r\n'
                elif dir.startswith('/echo/'):
                    string = dir.replace('/echo/', '')
                    resp = str.encode(f'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(string)}\r\n\r\n{string}\r\n\r\n''')
                elif dir == '/user-agent':
                    agent_line, = [i for i in rec if 'User-Agent' in i]
                    agent = agent_line.split(': ')[1]
                    resp = str.encode(f'HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(agent)}\r\n\r\n{agent}\r\n\r\n''')
                elif req == 'GET' and dir.startswith('/files/'):
                    filename = dir.replace('/files/', '')
                    path = sys.argv[2]
                    if os.path.exists(path+filename):
                        result = ''
                        t = ReadThread(path+filename, result)
                        threads.append(t)
                        t.start()
                        t.join()
                        result = t.result
                        print(result)
                        resp = str.encode(f"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: {len(result)}\r\n\r\n{result.decode('utf-8')}\r\n\r\n")
                    else:
                        resp = b'HTTP/1.1 404 Not Found\r\n\r\n'
                elif req == 'POST' and dir.startswith('/files/'):
                    print(rec)
                    filename = dir.replace('/files/', '')
                    path = sys.argv[2]
                    print(path)
                    if os.path.exists(path):
                        content = rec[-1]
                        t = WriteThread(path+filename, content)
                        threads.append(t)
                        t.start()
                        t.join()
                        resp = str.encode("HTTP/1.1 201 Created\r\n\r\n")
                    else:
                        resp = b'HTTP/1.1 404 Not Found\r\n\r\n'
                else:
                    resp = b'HTTP/1.1 404 Not Found\r\n\r\n'
                print(resp)
        except Exception as e:
            print(str(e))
        finally:
            conn.send(resp)
            conn.close()



if __name__ == "__main__":
    for i in range(4):
        x = threading.Thread(target=main)
        threads.append(x)
        x.start()
    for i in threads:
        i.join()