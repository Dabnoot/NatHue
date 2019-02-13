#APDS Test Program
#Digital ambient light sense (ALS), and
#Color sense (RGBC)

import urllib.request

from datetime import datetime

from apds9960.const import *     #Import APDS constants
from apds9960 import APDS9960    #Import APDS code

import smbus    #System Management Bus, a subset of the I2C protocol
from time import sleep

import math

#Import tkinter to support the drawing of a screen
# to display RGB samples:
from tkinter import *

def printMessage(sMessage):
    global fLogFile
    print(sMessage)
    fLogFile.write(sMessage + "\n")

sLogFileName = datetime.now().strftime('HueSenseLog_%Y%m%d_%H%M%S.log')
sLogFilePath = "/home/pi/NatHue/Logs/"
print("Openning log file ", sLogFilePath + sLogFileName)
fLogFile = open(sLogFilePath + sLogFileName,'w')
printMessage("HueSense version 1.\n")

# The IP address of the Hue bridge and a list of lights you want to use
bridgeip = '192.168.1.203'  # <<<<<<<<<<<
printMessage("Bridge IP hard-coded as: " + bridgeip)

#Create a subroutine to test and wait for network connectivity:
def wait_for_network_connection():
    while True:
        try:
            response = urllib.request.urlopen('http://' + bridgeip,timeout=1)
            printMessage("Network connection test success.")
            return
        except Exception as e:
            printMessage("Network connection test fail.")
            printMessage("Exception: " + str(e))
            printMessage("Waiting 5 seconds to retry.")
            sleep(5)

#Wait for the network connection to be established
wait_for_network_connection()

port = 1
bus = smbus.SMBus(port)
apds = APDS9960(bus)



try:
    
    #Prepare tkinter instance:
    tk = Tk()
    w = Canvas(tk, width=500, height=500)
    w.pack()

    #Initialize RGB color samples for tkinter display:
    iSample = 0
    iR = 255
    iG = 255
    iB = 255
    #Set RGB sample color shift interval:
    ia = 10
    
    
    apds.enableLightSensor()
    
    
    printMessage("Initialization complete.")
    printMessage("=============================")
    
    sDataRecord = "YYYYMMDD_HHMMSS\t"
    sDataRecord = sDataRecord + "ARaw\t"
    sDataRecord = sDataRecord + "RRaw\t"
    sDataRecord = sDataRecord + "GRaw\t"
    sDataRecord = sDataRecord + "BRaw\t"
    sDataRecord = sDataRecord + "RSpl\t"
    sDataRecord = sDataRecord + "GSpl\t"
    sDataRecord = sDataRecord + "BSpl\t"
    sDataRecord = sDataRecord + "RCal\t"
    sDataRecord = sDataRecord + "GCal\t"
    sDataRecord = sDataRecord + "BCal\t"
    sDataRecord = sDataRecord + "RErr\t"
    sDataRecord = sDataRecord + "GErr\t"
    sDataRecord = sDataRecord + "BErr\t"
    
    printMessage(sDataRecord)
    
    while True:
        
        #Set the color sample on the tkinter window.
        #Change assignment of iSample to change the
        #  color being tested.
        iB = iSample
        tk_rgb = "#%02x%02x%02x" % (iR, iG, iB)
        w.create_rectangle(0, 0, 500, 500, fill=tk_rgb)
        tk.update()
        
        #Apply our loop sleep here. This will handle both
        #  the loop sleep requirement and give a moment
        #  for the tk window to complete the update of its color.
        sleep(.5)
        
        #Read light values:
        vala = apds.readAmbientLight()
        valr = apds.readRedLight()
        valg = apds.readGreenLight()
        valb = apds.readBlueLight()
        
        #Use equations to check data:
        #Prevent illegal value for natural log:
        valr = max(1,valr)
        valg = max(1,valg)
        valb = max(1,valb)
        #Apply experimentally-derived constants
        f1R = 186.66 * math.log(valr) - 691.33
        f1G = 173.74 * math.log(valg) - 669.32
        f1B = 399.15 * math.log(valb) - 1804.4
        f1R = min(f1R, 255)
        f1G = min(f1G, 255)
        f1B = min(f1B, 255)
        
        #Prevent DBZ:
        iR = max(1, iR)
        iG = max(1, iG)
        iB = max(1, iB)
        RError = abs(1 - (f1R / iR))
        GError = abs(1 - (f1G / iG))
        BError = abs(1 - (f1B / iB))
        
        sDataRecord = datetime.now().strftime('%Y%m%d_%H%M%S') + "\t"
            
        #Record raw light values:
        sDataRecord = sDataRecord + str(vala) + "\t"
        sDataRecord = sDataRecord + str(valr) + "\t"
        sDataRecord = sDataRecord + str(valg) + "\t"
        sDataRecord = sDataRecord + str(valb) + "\t"
        sDataRecord = sDataRecord + str(iR) + "\t"
        sDataRecord = sDataRecord + str(iG) + "\t"
        sDataRecord = sDataRecord + str(iB) + "\t"
        sDataRecord = sDataRecord + format(f1R,'.2f') + "\t"
        sDataRecord = sDataRecord + format(f1G,'.2f') + "\t"
        sDataRecord = sDataRecord + format(f1B,'.2f') + "\t"
        sDataRecord = sDataRecord + format(RError,'.2f') + "\t"
        sDataRecord = sDataRecord + format(GError,'.2f') + "\t"
        sDataRecord = sDataRecord + format(BError,'.2f')
        
        #Print a data record for this run:
        printMessage(sDataRecord)
        
        #Calculate the new color sample value
        iSample += ia
        if ((iSample >= 250) or (iSample <= 0)):
            ia *= -1
    
        
    #End loop while true.
except Exception as e:
    printMessage("Exception occurred: " + str(e))
except KeyboardInterrupt: #Ctrl-C causes KeyboardInterrupt to be raised.
    pass  #Do nothing. A statement is required here, syntactically.
finally:
#    GPIO.cleanup()
    printMessage("Exiting program.")
    fLogFile.close()
    

