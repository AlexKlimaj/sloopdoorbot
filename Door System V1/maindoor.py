import RPi.GPIO as GPIO
import time
from datetime import datetime
from datetime import timedelta
from socket import *
import thread
from threading import Thread
import paramiko
import os
import tweepy
import sys

start = datetime.now()
MEMBERIP = '192.168.1.74' #Enter the IP address of the members door pi
DOORBELLPORT = 12346 #Port to send the doorbell command through
PORT = 12345 #Send in out info over this port

people = 0 #Number of people in the gym
sensor1 = 0 #flag for sensor 1
sensor2 = 0 #flag for sensor 2
SLEEPTIME = 0.2 #time to wait for the 2nd sensor to trip after the first one in seconds
BOUNCETIME = 300 #laser debounce time in ms
WAITTIME = 0.5 #Time to wait between people 
BUFF = 1024
HOST = '' #Listen to all hosts

CARBON_SERVER = '0.0.0.0'
CARBON_PORT = 2003

#enter the corresponding information from your Twitter application:
CONSUMER_KEY = 'a0uZ9ezjpvIB4eRKbDcfyQsSf'#keep the quotes, replace this with your consumer key
CONSUMER_SECRET = 'yMIg5tfYz0STlbBw6niDh2kQVLgnBfuVBmyeUI8HO6z3xxKf2V'#keep the quotes, replace this with your consumer secret key
ACCESS_KEY = '2521249735-ZJhiotU3t6bDHWb5sfco3J35Gm4RPblgQvC8Xbn'#keep the quotes, replace this with your access token
ACCESS_SECRET = '53n3aJfVoFjgENamQ67E9PIheL0pGr1uMavkDqDH2weyF'#keep the quotes, replace this with your access token secret
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)
############################################################################

GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(24, GPIO.IN, pull_up_down = GPIO.PUD_UP)

############################################################################

def updatetwitter():
    global people
    while 1:
        now = time.strftime("%c")
        line = now + "\nNumber of people in Slo Op: " + str(people)
        api.update_status(line)
        time.sleep(600) #update twitter every 10 minutes
        
############################################################################

def endscript():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(
                paramiko.AutoAddPolicy())
        ssh.connect(MEMBERIP, username="pi", password="sloopbomb")
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('sudo pkill -9 -f membersdoor.py &')
    except Exception,e: 
        print "ERROR: Couldn't send command to end memberdoor.py"
        print str(e)
        with open('Door.log','a') as f:
            now = time.strftime("%c")
            temp = 'Couldnt send command to end memberdoor.py: %s %s\n' % (now, e)
            f.write(temp)
            f.close() # you can omit in most cases as the destructor will call if
    return
    
############################################################################

def response(key):
    return 'Server response: ' + key

def handler(clientsock,addr):
    global people
    while 1:
        data = clientsock.recv(BUFF)
        if not data: break
        print repr(addr) + ' recv:' + repr(data)
        clientsock.send(response(data))
        print repr(addr) + ' sent:' + repr(response(data))
        if "close" == data.rstrip(): break # type 'close' on client console to close connection from the server side

        if data == "in":
          people += 1
          print "Someone came in the members door"
          print "People in the gym: " + str(people)
        if data == "out":
          if people > 0:
            people -= 1
          print "Someone went out the members door"
          print "People in the gym: " + str(people)
        
    clientsock.close()
    print addr, "- closed connection" #log on console
    return

############################################################################     

def sendcommand(string):
    # SOCK_STREAM == a TCP socket
    sock = socket(AF_INET, SOCK_STREAM)
    #sock.setblocking(0)  # optional non-blocking
    print "sending data => [%s]" % (string)
    try:
        sock.connect((MEMBERIP, DOORBELLPORT))
        sock.send(string)
        reply = sock.recv(16384)  # limit reply to 16K
        print "reply => \n [%s]" % (reply)
        return reply
    except Exception,e: 
        print "ERROR: Couldn't send Ring to membersdoor.py"
        print str(e)
        with open('Door.log','a') as f:
            now = time.strftime("%c")
            temp = 'Couldnt send Ring to membersdoor.py: %s %s\n' % (now, e)
            f.write(temp)
            f.close() # you can omit in most cases as the destructor will call if

    sock.close()
    return "No Reply Received"

############################################################################
    
def runscript():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(
                paramiko.AutoAddPolicy())
        ssh.connect(MEMBERIP, username="pi", password="sloopbomb")
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('sudo python /home/pi/membersdoor.py &')    
    except Exception,e: 
        print "ERROR: Couldn't send command to start membersdoor.py"
        print str(e)
        with open('Door.log','a') as f:
            now = time.strftime("%c")
            temp = 'Couldnt send command to start membersdoor.py: %s %s\n' % (now, e)
            f.write(temp)
            f.close() # you can omit in most cases as the destructor will call if
    return
    
############################################################################
   
def sensor1function(channel):
   global sensor1
   sensor1 = 1

def sensor2function(channel):
   global sensor2
   sensor2 = 1
   
############################################################################
   
def updategraphite():
    while 1:
        try:
            ## date and time representation
            temp = 'people %d %d\n' % (people, int(time.time()))
            print 'sending message:\n%s' % temp
            carbonsock = socket()
            carbonsock.connect((CARBON_SERVER, CARBON_PORT))
            carbonsock.sendall(temp)
            carbonsock.close()
        except Exception,e: 
           print "ERROR: Couldn't send command to graphite"
           #print "Trying to start graphite"
           #os.system("sudo python /opt/graphite/bin/carbon-cache.py start &")
           print str(e)
           with open('Door.log','a') as f:
             now = time.strftime("%c")
             temp = 'Couldnt update graphite: %s %s\n' % (now, e)
             f.write(temp)
             f.close() # you can omit in most cases as the destructor will call if
        time.sleep(300)

############################################################################
         
def lasers():
   global people
   global sensor1
   global sensor2
   global start

   GPIO.add_event_detect(23, GPIO.FALLING, callback=sensor1function, bouncetime=BOUNCETIME)
   GPIO.add_event_detect(24, GPIO.FALLING, callback=sensor2function, bouncetime=BOUNCETIME)

   print("Digital Turnstile started")

   while True:

      #Sensor handling in/out detection
      if sensor1 == 1:
         time.sleep(SLEEPTIME)
         if sensor2 == 1:
            people += 1
            print "Someone came in the main door"
            print "People in the gym: " + str(people)
            sensor1 = 0
            sensor2 = 0
            stop = datetime.now()
            elapsed = stop - start
            if elapsed > timedelta(seconds=30):
                start = datetime.now()
                try:
                    thread.start_new_thread(sendcommand, ('ringbell',))
                except Exception,e: 
                    print "ERROR: Couldn't send command to ring doorbell"
                    print str(e)
                    with open('Door.log','a') as f:
                     now = time.strftime("%c")
                     temp = 'Couldnt send command to ring doorbell: %s %s\n' % (now, e)
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
            print "Someone went out the main door"
            print "People in the gym: " + str(people)
            sensor1 = 0
            sensor2 = 0
         time.sleep(WAITTIME)
         sensor1 = 0
         sensor2 = 0
      sensor1 = 0
      sensor2 = 0

   GPIO.cleanup()

############################################################################

if __name__=='__main__':

    try:
        endscript()
    except Exception,e:
        print "ERROR: Couldn't end membersdoor.py" 
        print str(e)
        with open('Door.log','a') as f:
         now = time.strftime("%c")
         temp = 'Couldnt end membersdoor.py: %s %s\n' % (now, e)
         f.write(temp)
         f.close() # you can omit in most cases as the destructor will call if
         
    time.sleep(10)  
    
    try:
        runscript()
    except Exception,e:
        print "ERROR: Couldn't run membersdoor.py" 
        print str(e)
        with open('Door.log','a') as f:
         now = time.strftime("%c")
         temp = 'Couldnt run membersdoor.py: %s %s\n' % (now, e)
         f.write(temp)
         f.close() # you can omit in most cases as the destructor will call if
         
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

    try:
       thread.start_new_thread(updategraphite, ())
    except Exception,e:
        print "ERROR: Couldn't Start updategraphite Thread"
        print str(e)
        with open('Door.log','a') as f:
         now = time.strftime("%c")
         temp = 'Couldnt Start updategraphite Thread: %s %s\n' % (now, e)
         f.write(temp)
         f.close() # you can omit in most cases as the destructor will call if
       
    try:
        thread.start_new_thread(updatetwitter, ())
    except Exception,e:
        print "ERROR: Couldn't Start Twitter Thread"
        print str(e)
        with open('Door.log','a') as f:
         now = time.strftime("%c")
         temp = 'Couldnt Start Twitter Thread: %s %s\n' % (now, e)
         f.write(temp)
         f.close() # you can omit in most cases as the destructor will call if
        
    ADDR = (HOST, PORT)
    serversock = socket(AF_INET, SOCK_STREAM)
    serversock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    serversock.bind(ADDR)
    serversock.listen(5)
    while 1:
        print 'waiting for connection... listening on port', PORT
        clientsock, addr = serversock.accept()
        print '...connected from:', addr
        thread.start_new_thread(handler, (clientsock, addr))

############################################################################
