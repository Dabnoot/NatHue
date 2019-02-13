#APDS Test Program
#Digital ambient light sense (ALS), and
#Color sense (RGBC)

import urllib.request

from datetime import datetime

from apds9960.const import *     #Import APDS constants
from apds9960 import APDS9960    #Import APDS code

import smbus    #System Management Bus, a subset of the I2C protocol
from time import sleep

#Import tkinter to support the drawing of a screen
# to display RGB samples:
from tkinter import *

#Begin imports related to OLED display:
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106
#End imports related to OLED display.


def printMessage(sMessage):
    global fLogFile
    print(sMessage)
    fLogFile.write(sMessage + "\n")

sLogFileName = datetime.now().strftime('HueSenseLog_%Y%m%d_%H%M%S.log')
sLogFilePath = "/home/pi/NatHue/Logs/"
print("Openning log file ", sLogFilePath + sLogFileName)
fLogFile = open(sLogFilePath + sLogFileName,'w')
printMessage("HueSense version 1.\n")

#====Begin OLED Configuration=======
# I2C interface and address
serial = i2c(port=1, address=0x3C)
# OLED Device
device = sh1106(serial)
#====End OLED Configuration=========


# The IP address of the Hue bridge and a list of lights you want to use
bridgeip = '192.168.1.203'  # <<<<<<<<<<<
printMessage("Bridge IP hard-coded as: " + bridgeip)

OLEDScreen = canvas(device)

def ClearScreen():
    global OLEDScreen
    OLEDScreen.__enter__()
    OLEDScreen.draw.rectangle(device.bounding_box, outline="white", fill="black")
    OLEDScreen.__exit__(None,None,None)

def WriteToScreen(sText, iLine, sOrientation):
    global OLEDScreen
    #Use 'enter' and 'exit' instead of 'with' in order to preserve
    # the screen contents.
    OLEDScreen.__enter__()
    #Determine the pixel position for the line:
    y = (iLine - 1) * 10
    #Determine the pixel x-position for start of the line:
    iSidePad = 3
    iLetterWidth = 6
    if(sOrientation == "Left"):
        x = iSidePad
    elif(sOrientation == "Center"):
        x = 128 - (iSidePad * 2)
        x = x - (len(sText) * iLetterWidth)
        x = x / 2
        x = x + iSidePad
    #Write the text to the OLED device:
    OLEDScreen.draw.text((x, y), sText, fill="white")
    OLEDScreen.__exit__(None,None,None)

WriteToScreen("12345678901234567890",1,"Center")
WriteToScreen("12345678901234567890",2,"Center")
WriteToScreen("12345678901234567890",3,"Center")
WriteToScreen("12345678901234567890",4,"Center")
WriteToScreen("12345678901234567890",5,"Center")
WriteToScreen("12345678901234567890",6,"Center")

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
    iR = 0
    iG = 255
    iB = 255
    #Set RGB sample color shift interval:
    ia = 10
    
    
    apds.enableLightSensor()
    
    #Declare variables:
    ovala = 1         #Old value ambient light
    ovalr = 1         #Old value red light
    ovalg = 1         #Old value green light
    ovalb = 1         #Old value blue light
    valpctr = 0.1
    valpctg = 0.1
    valpctb = 0.1
    LightChange = -1   #A flag for if we have new data to print to the screen
    
    fDeltaTrigger = 2.00
    printMessage("Light trigger detection on illumination change of " + str(fDeltaTrigger) + "%.")
    
    printMessage("Initialization complete.")
    printMessage("=============================")
    
    i = 0
    
    sDataRecord = "YYYYMMDD_HHMMSS\t"
    sDataRecord = sDataRecord + "ARaw\t"
    sDataRecord = sDataRecord + "RRaw\t"
    sDataRecord = sDataRecord + "GRaw\t"
    sDataRecord = sDataRecord + "BRaw\t"
    sDataRecord = sDataRecord + "RSpl\t"
    sDataRecord = sDataRecord + "GSpl\t"
    sDataRecord = sDataRecord + "BSpl\t"
    
    printMessage(sDataRecord)
    
    while True:
        
        #Set the color sample on the tkinter window:
        tk_rgb = "#%02x%02x%02x" % (iR, iG, iB)
        w.create_rectangle(0, 0, 500, 500, fill=tk_rgb)
        tk.update()
        iR += ia
        if ((iR >= 250) or (iR <= 0)):
            ia *= -1
        
        
        
        i = i + 1
        #Read light values:
        vala = apds.readAmbientLight()
        valr = apds.readRedLight()
        valg = apds.readGreenLight()
        valb = apds.readBlueLight()
        
        fDeltaA = 0.0
        fDeltaR = 0.0
        fDeltaG = 0.0
        fDeltaB = 0.0
        
        if(ovala > 0 and
            ovalr > 0 and
            ovalg > 0 and
            ovalb > 0):
            fDeltaA = abs(1 - (vala/ovala)) * 100
            fDeltaR = abs(1 - (valr/ovalr)) * 100
            fDeltaG = abs(1 - (valg/ovalg)) * 100
            fDeltaB = abs(1 - (valb/ovalb)) * 100
        else:
            #In the event of a 0, set old values to current values.
            #  This allows recovery of the system with divide-by-zero
            #  protections in place.
            ovala = vala
            ovalr = valr
            ovalg = valg
            ovalb = valb
        
        #Get the max changed light:
        fMaxDelta = fDeltaA
        if(fDeltaR > fMaxDelta):
            fMaxDelta = fDeltaR
        if(fDeltaG > fMaxDelta):
            fMaxDelta = fDeltaG
        if(fDeltaB > fMaxDelta):
            fMaxDelta = fDeltaB
        
        #If the light has changed more that a specified percentage,
        #  set the LightChange flag:
        if (fMaxDelta > fDeltaTrigger):
            LightChange = 1
            sDataRecord = datetime.now().strftime('%Y%m%d_%H%M%S') + "\t"
            
        #If any light values have changed, perform calcs and display results:
        if LightChange == 1:
                        
            #Record raw light values:
            sDataRecord = sDataRecord + str(vala) + "\t"
            sDataRecord = sDataRecord + str(valr) + "\t"
            sDataRecord = sDataRecord + str(valg) + "\t"
            sDataRecord = sDataRecord + str(valb) + "\t"
            sDataRecord = sDataRecord + str(iR) + "\t"
            sDataRecord = sDataRecord + str(iG) + "\t"
            sDataRecord = sDataRecord + str(iB) + "\t"
            
            iTot = max(valr + valg + valb,1)
            fPctR = valr / iTot
            fPctG = valg / iTot
            fPctB = valb / iTot
            
            #Record the new light values as old light values:
            ovala = vala
            ovalr = valr
            ovalg = valg
            ovalb = valb
            
            #Print a data record for this run:
            printMessage(sDataRecord)
            
            # Display image on OLED.
            with canvas(device) as draw:
                draw.text((3, 0), "Running...", fill="white")
                draw.text((3, 10), "Amb: " + str(vala), fill="white")
                draw.text((3, 20), "Red: " + str(valr), fill="white")
                draw.text((3, 30), "Grn: " + str(valg), fill="white")
                draw.text((3, 40), "Blu: " + str(valb), fill="white")
            #WriteToScreen("Running...",1,"Left")
            #WriteToScreen("Red: " + str(valr),2,"Left")
            #WriteToScreen("Grn: " + str(valg),3,"Left")
            #WriteToScreen("Blu: " + str(valb),4,"Left")
            #Reset out print flag:
            LightChange = -1
        
        #End if LightChange.
        sleep(.5)
    #End loop while true.
except Exception as e:
    printMessage("Exception occurred: " + str(e))
except KeyboardInterrupt: #Ctrl-C causes KeyboardInterrupt to be raised.
    pass  #Do nothing. A statement is required here, syntactically.
finally:
#    GPIO.cleanup()
    printMessage("Exiting program.")
    fLogFile.close()
    

