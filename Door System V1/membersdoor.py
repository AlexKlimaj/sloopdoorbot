import RPi.GPIO as GPIO
import time
from socket import *
import thread
from threading import Thread
import os
import datetime
import pygame
import paramiko

MAINDOORIP = '192.168.1.17' #Enter the IP address of the main door
DOORBELLPORT = 12346 #Port to send the doorbell command through
PORT = 12345 #Send in out info over this port
DOORBELL = "doorbell.mp3"

people = 0 #Number of people in the gym
sensor1 = 0 #flag for sensor 1
sensor2 = 0 #flag for sensor 2
SLEEPTIME = 0.2 #time to wait for the 2nd sensor to trip after the first one in seconds
BOUNCETIME = 300 #laser debounce time in ms
WAITTIME = 0.5 #Time to wait between people in seconds
BUFF = 1024
HOST = '' #Listen to all hosts
start = datetime.datetime.now()

############################################################################

GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(24, GPIO.IN, pull_up_down = GPIO.PUD_UP)
            
############################################################################

def playbell():
    pygame.mixer.init()
    pygame.mixer.music.load(DOORBELL)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy() == True:
        continue
    return

############################################################################

def response(key):
    return 'Server response: ' + key

def handler(clientsock,addr):
    global start
    while 1:
        data = clientsock.recv(BUFF)
        if not data: break
        print repr(addr) + ' recv:' + repr(data)
        clientsock.send(response(data))
        print repr(addr) + ' sent:' + repr(response(data))
        if "close" == data.rstrip(): break # type 'close' on client console to close connection from the server side
        
        if data == "ringbell":
            print "TIME TO RING THE BELL!"
            try:
                thread.start_new_thread(playbell, ())
            except:
                print "ERROR: Couldn't Start playbell Thread"
                
    clientsock.close()
    print addr, "- closed connection" #log on console
    return

############################################################################    

def sendcommand(string):
    # SOCK_STREAM == a TCP socket
    sock = socket(AF_INET, SOCK_STREAM)
    #sock.setblocking(0)  # optional non-blocking
    sock.connect((MAINDOORIP, PORT))

    print "sending data => [%s]" % (string)

    sock.send(string)
    #reply = sock.recv(16384)  # limit reply to 16K
    #print "reply => \n [%s]" % (reply)
    sock.close()
    #return reply
    return

############################################################################
    
def sensor1function(channel):
   global sensor1
   sensor1 = 1

def sensor2function(channel):
   global sensor2
   sensor2 = 1

def lasers():
   global people
   global sensor1
   global sensor2

   GPIO.add_event_detect(23, GPIO.FALLING, callback=sensor1function, bouncetime=BOUNCETIME)
   GPIO.add_event_detect(24, GPIO.FALLING, callback=sensor2function, bouncetime=BOUNCETIME)

   print("Digital Turnstile started")

   while True:

      if sensor1 == 1:
         time.sleep(SLEEPTIME)
         if sensor2 == 1:
            people += 1
            print "Someone came in the members door"
            print "People in the gym: " + str(people)
            sensor1 = 0
            sensor2 = 0
            try:
               #sendcommand("in")
               thread.start_new_thread(sendcommand, ('in',))
            except Exception,e: 
               print "ERROR: Couldn't send 'in' to main door"
               #runscript() #try to start the script on the main door
               print str(e)
               with open('Door.log','a') as f:
                 now = time.strftime("%c")
                 temp = 'Couldnt send in to main door: %s %s\n' % (now, e)
                 f.write(temp)
                 f.close() # you can omit in most cases as the destructor will call if
            time.sleep(WAITTIME)
         sensor1 = 0
         sensor2 = 0

      elif sensor2 == 1:
         time.sleep(SLEEPTIME)
         if sensor1 == 1:
            if people > 0:
               people -= 1
            print "Someone went out the members door"
            print "People in the gym: " + str(people)
            sensor1 = 0
            sensor2 = 0
            try:
               #sendcommand("out")
               thread.start_new_thread(sendcommand, ('out',))
            except Exception,e: 
               print "ERROR: Couldn't send 'out' to main door"
               #runscript() #try to start the script on the main door
               print str(e)
               with open('Door.log','a') as f:
                 now = time.strftime("%c")
                 temp = 'Couldnt send out to main door: %s %s\n' % (now, e)
                 f.write(temp)
                 f.close() # you can omit in most cases as the destructor will call if
            time.sleep(WAITTIME)
         sensor1 = 0
         sensor2 = 0

   GPIO.cleanup()

############################################################################

if __name__=='__main__':

    try:
       thread.start_new_thread(lasers, ())
    except Exception,e:
        print "ERROR: Couldn't Start Laser Thread"
        print str(e)
        with open('Door.log','a') as f:
         now = time.strftime("%c")
         temp = 'Couldnt Start Laser Thread: %s %s\n' % (now, e)
         f.write(temp)
         f.close() # you can omit in most cases as the destructor will call if       
       
    ADDR = (HOST, DOORBELLPORT)
    serversock = socket(AF_INET, SOCK_STREAM)
    serversock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    serversock.bind(ADDR)
    serversock.listen(5)
    while 1:
        print 'waiting for connection... listening on port', DOORBELLPORT
        clientsock, addr = serversock.accept()
        print '...connected from:', addr
        thread.start_new_thread(handler, (clientsock, addr))

############################################################################
