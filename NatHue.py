#APDS Test Program
#Digital ambient light sense (ALS), and
#Color sense (RGBC)

import urllib.request 

from datetime import datetime

from apds9960.const import *     #Import APDS constants
from apds9960 import APDS9960    #Import APDS code

# pip3 install phue for the Phillips Hue system
from phue import Bridge


#Begin imports related to OLED display:
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
#End imports related to OLED display.

#Bring in GPIO in order to read the button presses:
try:
    import RPi.GPIO as GPIO      #Attempt to import GPIO
except RunTimeError:
    print("Error importing RPi.GPIO. Try using 'sudo' to run script.")
GPIO.setmode(GPIO.BCM)
GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


import smbus    #System Management Bus, a subset of the I2C protocol
from time import sleep

def printMessage(sMessage):
    global fLogFile
    print(sMessage)
    fLogFile.write(sMessage + "\r\n")

sLogFileName = datetime.now().strftime('NatHueLog_%Y%m%d_%H%M%S.log')
sLogFilePath = "/home/pi/NatHue/Logs/"
print("Openning log file ", sLogFilePath + sLogFileName)
fLogFile = open(sLogFilePath + sLogFileName,'w')
printMessage("NatHue version 12.\n")

#===============================================================
#Begin other configuration related to OLED display
# Raspberry Pi pin configuration:
RST = None     # on the PiOLED this pin isnt used
# Note the following are only used with SPI:
DC = 23
SPI_PORT = 0
SPI_DEVICE = 0
# 128x32 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)
# Initialize library.
disp.begin()

# Clear display.
disp.clear()
disp.display()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0,0,width,height), outline=0, fill=0)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height-padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

# Load default font.
font = ImageFont.load_default()
#End other configuration related to OLED display
#===============================================================

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
    brHueBridge = Bridge(bridgeip)
    printMessage("Connection with Phillips Hue bridge established.")
except:
    printMessage("Unable to create connection with Phillips Hue bridge.")

# IMPORTANT: If running for the first time:
#    Uncomment the brHueBridge.connect() line
#    Press button on the Phillips Hue bridge
#    Run the code
# This will save your connection details in /home/pi/.python_hue
# Delete that file if you change bridges
#brHueBridge.connect()

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
    
    if(fC > 1): #If the value is on the 255 range, normalize.
        fC = fC / 255
    
    if(fC > 0.04045):
        fCR = pow((fC + 0.055) / (1.0 + 0.055), 2.4)
    else:
        fCR = (fC / 12.92)   
    return fCR
    
    #Removing gamma correction for now:
    #return fC

#==========================================
#Begin configuration for buttons:
bUp = False
bDown = False
bSelect = False

def ButtonUp(dummy):
    global bUp
    bUp = True
    print("Up")

def ButtonDown(dummy):
    global bDown
    bDown = True
    print("Down")

def ButtonSelect(dummy):
    global bSelect
    bSelect = True
    print("Select")

GPIO.add_event_detect(24, GPIO.RISING)
GPIO.add_event_detect(23, GPIO.RISING)
GPIO.add_event_detect(22, GPIO.RISING)

GPIO.add_event_callback(24, ButtonUp)
GPIO.add_event_callback(23, ButtonDown)
GPIO.add_event_callback(22, ButtonSelect)

#End configuration for buttons.
#==========================================

#Define a multi-position toggle variable to assist with color tuning:
sScreenPage = "-"

RCSL_Pow = 0.5
RCSL_Const = 0.05#0.029

def RawColorSenseLinearize(fval):
    #This function is to linearize what is believed to be
    #  non-linear light sensing by the APDS9960
    global RCSL_Pow
    global RCSL_Const
    RCSLReturn = (fval**RCSL_Pow)/RCSL_Const
    return RCSLReturn

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
    #sDataRecord = sDataRecord + "MaxDlt\t"
    #sDataRecord = sDataRecord + "A%Dlt\t"
    #sDataRecord = sDataRecord + "R%Dlt\t"
    #sDataRecord = sDataRecord + "G%Dlt\t"
    #sDataRecord = sDataRecord + "B%Dlt\t"
    sDataRecord = sDataRecord + "ARaw\t"
    sDataRecord = sDataRecord + "RRaw\t"
    sDataRecord = sDataRecord + "GRaw\t"
    sDataRecord = sDataRecord + "BRaw\t"
    #sDataRecord = sDataRecord + "RRCL\t"
    #sDataRecord = sDataRecord + "GRCL\t"
    #sDataRecord = sDataRecord + "BRCL\t"
    #sDataRecord = sDataRecord + "R%\t"
    #sDataRecord = sDataRecord + "G%\t"
    #sDataRecord = sDataRecord + "B%\t"
    sDataRecord = sDataRecord + "Bri\t"
    sDataRecord = sDataRecord + "R  \t"
    sDataRecord = sDataRecord + "G  \t"
    sDataRecord = sDataRecord + "B  \t"
    sDataRecord = sDataRecord + "X  \t"
    sDataRecord = sDataRecord + "Y  \t"
    sDataRecord = sDataRecord + "Z  \t"
    
    printMessage(sDataRecord)
    
    #Create values to "tune" the light sensor
    fTuneR = 1.0
    fTuneG = 1.0
    fTuneB = 1.0
    
    while True:
        i = i + 1
        
        #Processing 'Select' button press:
        if(bSelect):
            if(sScreenPage == "-"):
                sScreenPage = "R"
            elif(sScreenPage == "R"):
                sScreenPage ="G"
            elif(sScreenPage == "G"):
                sScreenPage = "B"
            elif(sScreenPage == "B"):
                sScreenPage = "RCSL_Pow"
            elif(sScreenPage == "RCSL_Pow"):
                sScreenPage = "RCSL_Const"
            elif(sScreenPage == "RCSL_Const"):
                sScreenPage = "-"
            bSelect = False
            print(sScreenPage + " selected.")
            LightChange = 1
        
        if(bUp):
            if(sScreenPage == "R"):
                fTuneR = fTuneR + 0.01
            elif(sScreenPage == "G"):
                fTuneG = fTuneG + 0.01
            elif(sScreenPage == "B"):
                fTuneB = fTuneB + 0.01
            elif(sScreenPage == "RCSL_Pow"):
                RCSL_Pow = RCSL_Pow + 0.01
                if(RCSL_Pow >= 1.0):
                    RCSL_Pow = 1.0
            elif(sScreenPage == "RCSL_Const"):
                RCSL_Const = RCSL_Const + 0.001
            bUp = False
            print("Increasing")
            LightChange = 1 #Set flag to process the light change.
        
        if(bDown):
            if(sScreenPage == "R"):
                fTuneR = fTuneR - 0.01
            elif(sScreenPage == "G"):
                fTuneG = fTuneG - 0.01
            elif(sScreenPage == "B"):
                fTuneB = fTuneB - 0.01
            elif(sScreenPage == "RCSL_Pow"):
                RCSL_Pow = RCSL_Pow - 0.01
                if(RCSL_Pow <= 0.0):
                    RCSL_Pow = 0.0
            elif(sScreenPage == "RCSL_Const"):
                RCSL_Const = RCSL_Const - 0.001
                if(RCSL_Const <= 0.0):  #DBZ protection
                    RCSL_Const = 0.001
            bDown = False
            print("Decreasing")
            LightChange = 1 #Set flag to process the light change.
        
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
            #Add "timestamp" to data record
            sDataRecord = datetime.now().strftime('%Y%m%d_%H%M%S') + "\t"
            #Add "%change that has triggered this light update" to data record
            #sDataRecord = sDataRecord + format(fMaxDelta, '6.2f') + "\t"
            
            
        #If any light values have changed, perform calcs and display results:
        if LightChange == 1:
            
            #Add "%change" to data record
            #sDataRecord = sDataRecord + format(fDeltaA,'5.2f') + "\t"
            #sDataRecord = sDataRecord + format(fDeltaR,'5.2f') + "\t"
            #sDataRecord = sDataRecord + format(fDeltaG,'5.2f') + "\t"
            #sDataRecord = sDataRecord + format(fDeltaB,'5.2f') + "\t"
            
            #Add "raw light values" to data record
            
            sDataRecord = sDataRecord + format(vala,'4d') + "\t"
            sDataRecord = sDataRecord + format(valr,'4d') + "\t"
            sDataRecord = sDataRecord + format(valg,'4d') + "\t"
            sDataRecord = sDataRecord + format(valb,'4d') + "\t"
            
            #Calculate linearized color values
            #The APDS9960 appears to exaggerate colors in very bright illumination.
            RCSLvalr = int(RawColorSenseLinearize(valr))
            RCSLvalg = int(RawColorSenseLinearize(valg))
            RCSLvalb = int(RawColorSenseLinearize(valb))
            #sDataRecord = sDataRecord + str(RCSLvalr) + "\t"
            #sDataRecord = sDataRecord + str(RCSLvalg) + "\t"
            #sDataRecord = sDataRecord + str(RCSLvalb) + "\t"
            
            #valr = RCSLvalr
            #valg = RCSLvalg
            #valb = RCSLvalb
            
            
            #Calculate RGB percentages:
            RGBTotal = valr + valg + valb
            RGBTotal = (valr + valg + valb)/3
            if(RGBTotal == 0):
                nRGBTotal = 1
            else:
                nRGBTotal = RGBTotal
            valpctr = min(valr / nRGBTotal,1.0) * 100
            valpctg = min(valg / nRGBTotal,1.0) * 100
            valpctb = min(valb / nRGBTotal,1.0) * 100
            
            #Add "RGB percentages" to data record
            #sDataRecord = sDataRecord + format(valpctr,'.2f') + "\t"
            #sDataRecord = sDataRecord + format(valpctg,'.2f') + "\t"
            #sDataRecord = sDataRecord + format(valpctb,'.2f') + "\t"
            
            #Calculate a brightness:
            #printMessage("Brightness calculation:")
            #printMessage("-----------------------")
            iFullBrightness = 230
            #Full brightness value is arbitrary.
            #Normal room ~ 230. Bright flashlight is 20,000.
            iBri = int((vala / iFullBrightness) * 255)
            if(iBri > 255):
                iBri = 255
            #Add "brightness sent to Philips Hue" to data record
            sDataRecord = sDataRecord + str(iBri) + "\t"
            
            #======= BEGIN SETTING LIGHT VALUES =======
            
            f1R = (valpctr / 100) * 255
            f1G = (valpctg / 100) * 255
            f1B = (valpctb / 100) * 255
            
            #Add "RGB used in color calculations"  to data record
            sDataRecord = sDataRecord + format(f1R,'.2f') + "\t"
            sDataRecord = sDataRecord + format(f1G,'.2f') + "\t"
            sDataRecord = sDataRecord + format(f1B,'.2f') + "\t"
            
            #Apply gamma correction to make color more vivid:
            if(True):
                f1Rgc = GammaCorrection(f1R)
                f1Ggc = GammaCorrection(f1G)
                f1Bgc = GammaCorrection(f1B)
            else:
                f1Rgc = f1R/255
                f1Ggc = f1G/255
                f1Bgc = f1B/255
            
            #Target color detected at lamp is 254, 245, 141
            #f1Rgc = 0
            #f1Ggc = 255
            #f1Bgc = 255
            #iBri = 255
            
            ColorMatchRGB_D50 =  [[0.5093439, 0.3209071, 0.1339691],
                              [0.2748840, 0.6581315, 0.0669845],
                              [0.0242545, 0.1087821, 0.6921735]]
            NTSC_RGB_D50 = [[ 0.6343706,  0.1852204,  0.1446290],
                       [ 0.3109496,  0.5915984,  0.0974520],
                       [-0.0011817,  0.0555518,  0.7708399]]
            
            NTSC_RGB_C =[[0.6068909,  0.1735011,  0.2003480],
                        [0.2989164,  0.5865990,  0.1144845],
                        [0.0000000,  0.0660957,  1.1162243]]
            
            sRGB_D50 =[[0.4360747,  0.3850649,  0.1430804],
                   [0.2225045,  0.7168786,  0.0606169],
                   [0.0139322,  0.0971045,  0.7141733]]
            
            PAL_SECAM_RGB_D65 = [[0.4306190,  0.3415419,  0.1783091],
                                 [0.2220379,  0.7066384,  0.0713236],
                                 [0.0201853,  0.1295504,  0.9390944]]
            
            CIE_RGB_D50 = [[ 0.4868870,  0.3062984,  0.1710347],
                           [ 0.1746583,  0.8247541,  0.0005877],
                           [-0.0012563,  0.0169832,  0.8094831]]
            
            XYZ = CIE_RGB_D50
            
            a=XYZ[0][0]
            bb=XYZ[0][1]
            c=XYZ[0][2]
             
            d=XYZ[1][0]
            e=XYZ[1][1]
            f=XYZ[1][2]
             
            g=XYZ[2][0]
            h=XYZ[2][1]
            i=XYZ[2][2]
            
            #Calculate XYZ values:
            f1X = f1Rgc * a + f1Ggc * bb + f1Bgc * c
            f1Y = f1Ggc * d + f1Ggc * e + f1Bgc * f
            f1Z = f1Bgc * g + f1Ggc * h + f1Bgc * i
            
            #Add "X,Y, and Z values" to data record
            sDataRecord = sDataRecord + format(f1X,'.5f') + "\t"
            sDataRecord = sDataRecord + format(f1Y,'.5f') + "\t"
            sDataRecord = sDataRecord + format(f1Z,'.5f') + "\t"
            
            #Calculate the xy values from the XYZ values
            f1Tot = f1X + f1Y + f1Z
            if(f1Tot == 0):
                f1Tot = 1
            f2X = f1X / (f1Tot)
            f2Y = f1Y / (f1Tot)
            
            
            #brHueBridge.set_light('Dining room accent 1', {'on': True, 'bri': 255, 'xy': [f2X, f2Y], 'transitiontime': 0})
            brHueBridge.set_light('Dining room accent 1', {'on': True, 'bri': iBri, 'xy': [f2X, f2Y], 'transitiontime': 10})
            
            #======= END SETTING LIGHT VALUES =======
            
            #Record the new light values as old light values:
            ovala = vala
            ovalr = valr
            ovalg = valg
            ovalb = valb
            
            #Print a data record for this run:
            printMessage(sDataRecord)
            
            # Display image on OLED.
            # Draw a black filled box to clear the image.
            draw.rectangle((0,0,width,height), outline=0, fill=0)
            
            draw.text((x, top),       "Running...",  font=font, fill=255)
            
            if(sScreenPage == "-"):
                draw.text((x, top+8),     "Red: " + format(f1R,'.2f') + format(fTuneR-1,'+.2f'), font=font, fill=255)
                draw.text((x, top+16),    "Grn: " + format(f1G,'.2f') + format(fTuneG-1,'+.2f') ,  font=font, fill=255)
                draw.text((x, top+25),    "Blu: " + format(f1B,'.2f') + format(fTuneB-1,'+.2f') ,  font=font, fill=255)
            elif(sScreenPage == "R"):
                draw.text((x, top+8),     "Red tuning: " + format(fTuneR,'.2f') + "%", font=font, fill=255)
            elif(sScreenPage == "G"):
                draw.text((x, top+8),     "Grn tuning: " + format(fTuneG,'.2f') + "%", font=font, fill=255)
            elif(sScreenPage == "B"):
                draw.text((x, top+8),     "Blu tuning: " + format(fTuneB,'.2f') + "%", font=font, fill=255)
            elif(sScreenPage == "RCSL_Pow"):
                draw.text((x, top+8),     "RCSL_Pow: " + format(RCSL_Pow,'.2f') + "%", font=font, fill=255)
            elif(sScreenPage == "RCSL_Const"):
                draw.text((x, top+8),     "RCSL_Const: " + format(RCSL_Const,'.3f') + "%", font=font, fill=255)
            disp.image(image)
            disp.display()
            
            
            
            
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
    GPIO.cleanup()
    printMessage("Exiting program.")
    fLogFile.close()
    
    
    
    