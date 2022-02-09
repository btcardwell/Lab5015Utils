import zmq
import serial
import time

class SerialServer:
    def __init__(self, port, device):
        context = zmq.Context()
        self.socket = context.socket(zmq.REP)
        self.socket.bind("tcp://*:%d"%port)
        self.instr = serial.Serial(device, 115200, timeout=0)
        self.xMax = 429
        self.yMax = 189

        # Wake up grbl
        wakeUp = "\r\n\r\n"
        self.instr.write(wakeUp.encode())
        time.sleep(2)  # Wait for grbl to initialize
        self.instr.flushInput()  # Flush startup text in serial input

        #Homing cycle
        command = "$H\n"
        self.instr.write(command.encode()) # Send g-code block to grbl
        grbl_out = self.instr.readline()

        #set coordinateds to 0,0
        command = "G10 P0 L20 X0 Y0 Z0\n"
        self.instr.write(command.encode()) # Send g-code block to grbl
        grbl_out = self.instr.readline()
        self.globalX = 0.0
        self.globalY = 0.0

        print("SerialServer listening at *:%d relaying to %s" % (port,device))


    def loop(self):
        while True:
            msg = self.socket.recv().decode("utf-8").strip()
            print("Processing %s" % msg)
            msg = msg.split()

            reply = ""
            if "delta" in msg:
                self.globalX += float(msg[1])
                self.globalY += float(msg[2])
                command = "G90 G0 X"+str(self.globalX)+" Y"+str(self.globalY)+"\n"
                self.instr.write(command.encode()) # Send g-code block to grbl
                time.sleep(0.2)
                reply = self.instr.readline()
                self.socket.send(reply) #no need to decode and encode

            if "go" in msg:
                if float(msg[1]) > self.xMax:
                    print ("requested x value is too high, setting x to {}".format(self.xMax))
                if float(msg[2]) > self.yMax:
                    print("requested y value is too high, setting y to {}".format(self.yMax))
                self.globalX = min(self.xMax, float(msg[1]))
                self.globalY = min(self.yMax, float(msg[2]))
                command = "G90 G0 X"+str(self.globalX)+" Y"+str(self.globalY)+"\n"
                self.instr.write(command.encode()) # Send g-code block to grbl
                time.sleep(0.2)
                reply = self.instr.readline()
                self.socket.send(reply) #no need to decode and encode

            if "get" in msg:
                reply = str(self.globalX)+" "+str(self.globalY)
                self.socket.send(reply.encode())

            if "unlock" in msg:
                command = "$x\n"
                self.instr.write(command.encode()) # Send g-code block to grbl
                time.sleep(0.2)
                reply = self.instr.readline()
                self.socket.send(reply) #no need to decode and encode



from optparse import OptionParser
parser = OptionParser()
parser.add_option("-p","--port")
parser.add_option("-d","--device")
(options,args)=parser.parse_args()

myServer = SerialServer(int(options.port), options.device)
myServer.loop()
