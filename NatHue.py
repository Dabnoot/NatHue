#APDS Test Program
#Digital ambient light sense (ALS), and
#Color sense (RGBC)

import urllib.request

from datetime import datetime

from apds9960.const import *     #Import APDS constants
from apds9960 import APDS9960    #Import APDS code

# pip3 install phue for the Phillips Hue system
from phue import Bridge

#try:
#    import RPi.GPIO as GPIO      #Attempt to import GPIO
#except RunTimeError:
#    print("Error importing RPi.GPIO. Try using 'sudo' to run script.")
    
import smbus    #System Management Bus, a subset of the I2C protocol
from time import sleep

def printMessage(sMessage):
    global fLogFile
    print(sMessage)
    fLogFile.write(sMessage + "\n")

sLogFileName = datetime.now().strftime('NatHueLog_%Y%m%d_%H%M%S.log')
sLogFilePath = "/home/pi/NatHue/Logs/"
print("Openning log file ", sLogFilePath + sLogFileName)
fLogFile = open(sLogFilePath + sLogFileName,'w')
printMessage("NatHue version 10.\n")

# The IP address of the Hue bridge and a list of lights you want to use
bridgeip = '192.168.1.203'  # <<<<<<<<<<<
lights = ['Dining room accent 1']  # <<<<<<<<<<<

printMessage("Bridge ip hard-coded as: " + bridgeip)
printMessage("Hard-coded lights controlled: " + lights[0])

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
#  before continuing and attempting to connect to the
#  Phillips Hue bridge:
wait_for_network_connection()

# Connect to the Phillips Hue bridge
try:
    b = Bridge(bridgeip)
    printMessage("Connection with Phillips Hue bridge established.")
except:
    printMessage("Unable to create connection with Phillips Hue bridge.")

# IMPORTANT: If running for the first time:
#    Uncomment the b.connect() line
#    Press button on the Phillips Hue bridge
#    Run the code
# This will save your connection details in /home/pi/.python_hue
# Delete that file if you change bridges
#b.connect()

port = 1
bus = smbus.SMBus(port)
apds = APDS9960(bus)

#def intH(channel):
#    print("INTERRUPT")

#GPIO.setmode(GPIO.BOARD) #Set pin numbering system relative to RPi board
#GPIO.setup(7, GPIO.IN)   #Set pin 7 as an input pin.


def GammaCorrection(fC):
    #From https://gist.github.com/popcorn245/30afa0f98eea1c2fd34d
    #fCR = (fC > 0.04045) ? pow((fC + 0.055) / (1.0f + 0.055), 2.4) : (fC / 12.92);
    
    if(fC > 0.04045):
        fCR = pow((fC + 0.055) / (1.0 + 0.055), 2.4)
    else:
        fCR = (fC / 12.92)   
    return fCR
    
    #Removing gamma correction for now:
    #return fC
    
try:

    
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
    printMessage("Light set to change on illumination change of " + str(fDeltaTrigger) + "%.")
    
    printMessage("Initialization complete.")
    printMessage("=============================")
    
    sleep(1)
    i = 0
    
    sDataRecord = "YYYYMMDD_HHMMSS\t"
    sDataRecord = sDataRecord + "LtDelta\t"
    sDataRecord = sDataRecord + "A%Delta\t"
    sDataRecord = sDataRecord + "R%Delta\t"
    sDataRecord = sDataRecord + "G%Delta\t"
    sDataRecord = sDataRecord + "B%Delta\t"
    sDataRecord = sDataRecord + "ARaw\t"
    sDataRecord = sDataRecord + "RRaw\t"
    sDataRecord = sDataRecord + "GRaw\t"
    sDataRecord = sDataRecord + "BRaw\t"
    sDataRecord = sDataRecord + "R%\t"
    sDataRecord = sDataRecord + "G%\t"
    sDataRecord = sDataRecord + "B%\t"
    sDataRecord = sDataRecord + "T%\t"
    sDataRecord = sDataRecord + "Bri\t"
    sDataRecord = sDataRecord + "RSet\t"
    sDataRecord = sDataRecord + "GSet\t"
    sDataRecord = sDataRecord + "BSet\t"
    
    printMessage(sDataRecord)
    
    while True:
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
            #printMessage("Max % change (" + str(fMaxDelta) + ") greater than threshold ("
            #    + str(fDeltaTrigger) + "). Flag set to apply light change.")
            sDataRecord = sDataRecord + format(fMaxDelta, '5.2f') + "\t"
            
        #If any light values have changed, perform calcs and display results:
        if LightChange == 1:
            
            #Check to see if any light values have changed:
            #printMessage("\n")
            #printMessage("==================================")
            #printMessage("===== Begin Light Monitoring =====")
            
            #printMessage("(A) Percent change: " + str(fDeltaA))
            #printMessage("(R) Percent change: " + str(fDeltaR))
            #printMessage("(G) Percent change: " + str(fDeltaG))
            #printMessage("(B) Percent change: " + str(fDeltaB))
            
            #printMessage("====== End Light Monitoring ======")
            #printMessage("==================================")
            #printMessage("\n")            
            sDataRecord = sDataRecord + format(fDeltaA,'5.2f') + "\t"
            sDataRecord = sDataRecord + format(fDeltaR,'5.2f') + "\t"
            sDataRecord = sDataRecord + format(fDeltaG,'5.2f') + "\t"
            sDataRecord = sDataRecord + format(fDeltaB,'5.2f') + "\t"
            
            #Display raw light values:
            #printMessage("===========================")
            #printMessage("Raw light readings:")
            #printMessage("---------------------")
            #printMessage("Ambient = {}".format(vala))
            #printMessage("    Red = {}".format(valr))
            #printMessage("  Green = {}".format(valg))
            #printMessage("   Blue = {}".format(valb))
            sDataRecord = sDataRecord + str(vala) + "\t"
            sDataRecord = sDataRecord + str(valr) + "\t"
            sDataRecord = sDataRecord + str(valg) + "\t"
            sDataRecord = sDataRecord + str(valb) + "\t"
            
            #Calculate RGB percentages:
            RGBTotal = valr + valg + valb
            if(RGBTotal == 0):
                nRGBTotal = 1
            else:
                nRGBTotal = RGBTotal
            valpctr = valr / nRGBTotal * 100
            valpctg = valg / nRGBTotal * 100
            valpctb = valb / nRGBTotal * 100
            
            
            #Print the RGB percentages to one decimal place:
            #printMessage("Percent calculations:")
            #printMessage("---------------------")
            #printMessage("  red = {0:.1f}%".format(valpctr))
            #printMessage("green = {0:.1f}%".format(valpctg))
            #printMessage(" blue = {0:.1f}%".format(valpctb))
            #printMessage("total = {0:.1f}%".format(valpctr + valpctg + valpctb))
            sDataRecord = sDataRecord + format(valpctr,'.2f') + "\t"
            sDataRecord = sDataRecord + format(valpctg,'.2f') + "\t"
            sDataRecord = sDataRecord + format(valpctb,'.2f') + "\t"
            sDataRecord = sDataRecord + format(valpctr + valpctg + valpctb,'.2f') + "\t"
            
            
            #Calculate a brightness:
            #printMessage("Brightness calculation:")
            #printMessage("-----------------------")
            iFullBrightness = 230
            #Full brightness value is arbitrary.
            #Normal room ~ 230. Bright flashlight is 20,000.
            iBri = int((vala / iFullBrightness) * 255)
            if(iBri > 255):
                iBri = 255
            #printMessage("Brightness = " + str(iBri))
            sDataRecord = sDataRecord + str(iBri) + "\t"
            
            #======= BEGIN SETTING LIGHT VALUES =======
            
            f1R = (valpctr / 100) * 255
            f1G = (valpctg / 100) * 255
            f1B = (valpctb / 100) * 255
            
            #printMessage("Setting RGB:" +
            #             " R:" + str(f1R) +
            #             " G:" + str(f1G) +
            #             " B:" + str(f1B))
            sDataRecord = sDataRecord + format(f1R,'.2f') + "\t"
            sDataRecord = sDataRecord + format(f1G,'.2f') + "\t"
            sDataRecord = sDataRecord + format(f1B,'.2f') + "\t"
            
            #Apply gamma correction to make color more vivid:
            if(True):
                fyR = GammaCorrection(f1R)
                fyG = GammaCorrection(f1G)
                fyB = GammaCorrection(f1B)
                f1R = fyR
                f1G = fyG
                f1B = fyB
            
            #Calculate XYZ values using the wide RGB D65 formula:
            f1X = f1R * 0.649926 + f1G * 0.103455 + f1B * 0.197109
            f1Y = f1R * 0.234327 + f1G * 0.743075 + f1B * 0.022598
            f1Z = f1R * 0.000000 + f1G * 0.053077 + f1B * 1.035763
            
            #Calculate the xy values from the XYZ values
            f1Tot = f1X + f1Y + f1Z
            if(f1Tot == 0):
                f1Tot = 1
            f2X = f1X / (f1Tot)
            f2Y = f1Y / (f1Tot)
            
        
            #b.set_light('Dining room accent 1', {'on': True, 'bri': 255, 'xy': [f2X, f2Y], 'transitiontime': 0})
            b.set_light('Dining room accent 1', {'on': True, 'bri': iBri, 'xy': [f2X, f2Y], 'transitiontime': 10})
            
            #======= END SETTING LIGHT VALUES =======
            
            #Record the new light values as old light values:
            ovala = vala
            ovalr = valr
            ovalg = valg
            ovalb = valb
            
            #Print a data record for this run:
            printMessage(sDataRecord)
            
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
    
