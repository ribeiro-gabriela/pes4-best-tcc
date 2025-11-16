import os
import tftpy
import logging
logging.basicConfig(level=logging.DEBUG)

class Test:
    def callback(self, filename: str, **args):
        print(filename)
        return None
    
test = Test()
# os.mkdir('tmp')
server = tftpy.TftpServer("tmp", test.callback)
server.listen()
print("here")