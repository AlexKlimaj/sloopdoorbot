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

people = 0 #Number of people in the gym
SLEEPTIME = 1 #time to wait between in/out counts in seconds
BOUNCETIME = 300 #laser debounce time
BUFF = 1024
HOST = '' #Listen to all hosts
start = datetime.datetime.now()

############################################################################

GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(24, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

############################################################################
   
def runscript():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(
                paramiko.AutoAddPolicy())
        ssh.connect(MAINDOORIP, username="pi", password="sloopbomb")
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('sudo python /home/pi/maindoordb.py &')    
    except Exception,e: 
        print "ERROR: Couldn't send command to start maindoordb.py"
        print str(e)
        with open('Door.log','a') as f:
            now = time.strftime("%c")
            temp = '%s %s\n' % (now, e)
            f.write(temp)
            f.close() # you can omit in most cases as the destructor will call if
            
############################################################################

def playbell():
    pygame.mixer.init()
    pygame.mixer.music.load("Get-to-the-chopper.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy() == True:
        continue

############################################################################

def response(key):
    return 'Server response: ' + key

def handler(clientsock,addr):
    while 1:
        global start
        data = clientsock.recv(BUFF)
        if not data: break
        print repr(addr) + ' recv:' + repr(data)
        clientsock.send(response(data))
        print repr(addr) + ' sent:' + repr(response(data))
        if "close" == data.rstrip(): break # type 'close' on client console to close connection from the server side
        
        stop = datetime.datetime.now()
        elapsed = stop - start
        if elapsed > datetime.timedelta(seconds=30):
            if data == "ringbell":
              print "TIME TO RING THE BELL!"
              try:
                thread.start_new_thread(playbell, ())
              except:
                print "ERROR: Couldn't Start playbell Thread"
              start = datetime.datetime.now()

    clientsock.close()
    print addr, "- closed connection" #log on console

############################################################################    

def sendcommand(string):
    # SOCK_STREAM == a TCP socket
    sock = socket(AF_INET, SOCK_STREAM)
    #sock.setblocking(0)  # optional non-blocking
    sock.connect((MAINDOORIP, PORT))

    print "sending data => [%s]" % (string)

    sock.send(string)
    reply = sock.recv(16384)  # limit reply to 16K
    print "reply => \n [%s]" % (reply)
    sock.close()
    return reply

############################################################################
    
def sensor1function(channel):
   global people
   people += 1
   print "Someone came in the members door"
   print "People in the gym: " + str(people)
   try:
      sendcommand("in")
   except Exception,e: 
      print "ERROR: Couldn't send 'in' to main door"
      runscript() #try to start the script on the main door
      print str(e)
      with open('Door.log','a') as f:
          now = time.strftime("%c")
          temp = '%s %s\n' % (now, e)
          f.write(temp)
          f.close() # you can omit in most cases as the destructor will call if
   time.sleep(SLEEPTIME)

def sensor2function(channel):
    global people
    if people > 0:
        people -= 1
        print "Someone went out the members door"
        print "People in the gym: " + str(people)
    try:
        sendcommand("out")
    except Exception,e: 
        print "ERROR: Couldn't send 'out' to main door"
        runscript() #try to start the script on the main door
        print str(e)
        with open('Door.log','a') as f:
            now = time.strftime("%c")
            temp = '%s %s\n' % (now, e)
            f.write(temp)
            f.close() # you can omit in most cases as the destructor will call if
    time.sleep(SLEEPTIME)

    
def lasers():
   GPIO.add_event_detect(24, GPIO.FALLING, callback=sensor1function, bouncetime=BOUNCETIME)
   GPIO.add_event_detect(23, GPIO.FALLING, callback=sensor2function, bouncetime=BOUNCETIME)
   print("Digital Turnstile started")

   while True:
      count = 0

   GPIO.cleanup()

############################################################################

if __name__=='__main__':

    try:
       thread.start_new_thread(lasers, ())
    except:
       print "ERROR: Couldn't Start Laser Thread"
   
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
