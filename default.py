#!/usr/bin/python
# -*- coding: utf-8 -*-

# Import the modules
import xbmc, xbmcaddon, xbmcgui, xbmcvfs
import pyxbmct
from threading import Thread
import json, sys, requests, os


# Addon variables
__addon__         = xbmcaddon.Addon()
__addon_id__      = __addon__.getAddonInfo('id')
__addon_path__    = __addon__.getAddonInfo('path')
__addon_name__    = __addon__.getAddonInfo('name')
__profile__       = __addon__.getAddonInfo('profile')
__localize__      = __addon__.getLocalizedString
__panel__         = os.path.join(__addon_path__, 'resources', 'media', 'ContentPanel.png')
__textureFO__     = os.path.join(__addon_path__, 'resources', 'media', 'KeyboardKey.png')
__textureNF__     = os.path.join(__addon_path__, 'resources', 'media', 'KeyboardKeyNF.png')
__transparent__   = os.path.join(__addon_path__, 'resources', 'media', 'Transparent.png')
__verticalLine__  = os.path.join(__addon_path__, 'resources', 'media', 'VerticalLine.png')
__settings__      = os.path.join(__profile__, 'settings.xml')
__skindir__       = xbmc.getSkinDir()


# Set INFO value for loggging according to kodi version (python2.7 or python3)
if sys.version_info.major < 3:
    INFO = xbmc.LOGNOTICE
else:
    INFO = xbmc.LOGINFO

# Action codes to capture
ACTION_PREVIOUS_MENU = 10
ACTION_STOP          = 13
ACTION_NAV_BACK      = 92
ACTION_BACKSPACE     = 110

# Font colors
BLUE  = '0xFF7ACAFE'
RED   = '0xFFFF0000'
BLACK = '0xFF000000'
WHITE = '0xFFFFFFFF'
GREY  = '0xAAFFFFFF'

# Fonts in different sizes
if __skindir__ == 'skin.estuary':
    SMALL_FONT   = 'font10'
    REGULAR_FONT = 'font13'
    BIG_FONT     = 'font45'
    LARGE_FONT   = 'font_clock' #'font60'
elif __skindir__ == 'skin.eminence.2':
    SMALL_FONT   = 'Font-NumEpisodes'
    REGULAR_FONT = 'Font-OSD'
    BIG_FONT     = 'Font-MusicVis-Info'
    LARGE_FONT   = 'lyr2b' # 'Font-MusicVis-Title'

# Text alignment
ALIGN_LEFT      = 0x00000000
ALIGN_RIGHT     = 0x00000001
ALIGN_CENTER_X  = 0x00000002
ALIGN_CENTER_Y  = 0x00000004
ALIGN_TRUNCATED = 0x00000008
ALIGN_JUSTIFIED = 0x00000010


# Strings
strAuto             = __localize__(35000) # 'Auto'
strAutoCirculate    = __localize__(35001) # 'Auto/Circulate'
strOff              = __localize__(35002) # 'Off'
strOn               = __localize__(35003) # 'On'
strHeat             = __localize__(35004) # 'Heat'
strCool             = __localize__(35005) # 'Cool'
strHeating          = __localize__(35006) # 'Heating'
strCooling          = __localize__(35007) # 'Cooling'
strNV               = __localize__(35008) # 'N/A'
strTemperature      = __localize__(35009) # 'Temperature:'
strFan              = __localize__(35010) # 'Fan:'
strState            = __localize__(35011) # 'Status: {}'
strMode             = __localize__(35012) # 'Mode:'
strTarget           = __localize__(35013) # 'Target:'
strClose            = __localize__(35014) # 'Exit'
strSet              = __localize__(35015) # 'Apply' or 'Commit'
strReload           = __localize__(35016) # 'Reload'
strHold             = __localize__(35017) # 'Hold:'
strDegreeCelsius    = '°C'.decode('utf-8')
strFahrenheit       = '°F'.decode('utf-8')
strArrowUp          = u'\u25B2'
strArrowDn          = u'\u25BC'
strPadding          = ' '

# Custom Settings
ipHouseThermostat    = __addon__.getSetting('ipAddress1') or '1.1.1.1'
nameHouseThermostat  = __addon__.getSetting('name1') or 'Thermostat 1'
ipGarageThermostat   = __addon__.getSetting('ipAddress2') or '1.1.1.2'
nameGarageThermostat = __addon__.getSetting('name2') or 'Thermostat 2'
tempCelsius          = bool(__addon__.getSetting('tempCelsius') == 'true') # True
colorMode            = bool(__addon__.getSetting('colorMode') == 'true') # True
autoRefreshTime      = int(__addon__.getSetting('refreshTime')) # 30

# Time delay between thermostat update and read in seconds
delayTime            = 2


# List of dictionaries with label and value for each option
#optionsFan  = [{'label': strAuto, 'value': 0}, {'label': strAutoCirculate, 'value': 1}, {'label': strOn, 'value': 2}]
optionsFan  = [{'label': strOff, 'value': 0}, {'label': strAuto, 'value': 1}, {'label': strOn, 'value': 2}]
optionsHold = [{'label': strOff, 'value': 0}, {'label': strOn, 'value': 1}]
optionsMode = [{'label': strOff, 'value': 0}, {'label': strHeat, 'value': 1}, {'label': strCool, 'value': 2}, {'label': strAuto, 'value': 3}]

if colorMode:
    tColor = {strOff: GREY, strHeat: RED, strCool: BLUE, strAuto: WHITE, strNV: GREY}
    TColor = {strOff: GREY, strHeating: RED, strCooling: BLUE, strNV: GREY}
else:
    tColor = {strOff: WHITE, strHeat: WHITE, strCool: WHITE, strAuto: WHITE, strNV: WHITE}
    TColor = {strOff: WHITE, strHeating: WHITE, strCooling: WHITE, strNV: WHITE}


def log(message, loglevel=INFO):
    xbmc.log(msg='[{}] {}'.format(__addon_id__, message), level=loglevel)


def convertTemp(temp):
    if tempCelsius:
        result = float(temp) * 9/5 + 32.0
        return round(result * 2.0) / 2.0
    else:
        return float(temp)


def getTemp(temp):
    if tempCelsius:
        result = (float(temp) - 32.0) * 5/9
        return str(round(result * 2.0) / 2.0) + strDegreeCelsius
    else:
        return str(temp) + strFahrenheit


def getTMode(number):
    number = int(number)
    if number == 0:
        return strOff
    elif number == 1:
        return strHeat
    elif number == 2:
        return strCool
    elif number == 3:
        return strAuto


def getTState(number):
    number = int(number)
    if number == 0:
        return strOff
    elif number == 1:
        return strHeating
    elif number == 2:
        return strCooling


def getFMode(number):
    number = int(number)
    if number == 0:
        return strOff
    elif number == 1:
        return strOn


def getHold(number):
    number = int(number)
    if number == 0:
        return strOff
    elif number == 1:
        return strOn


def LabelToValue(label, optionList):
    value = None

    for option in optionList:
        if option['label'] == label:
             value = int(option['value'])
             break

    return value


# Create a class for thermostats
# A class is an abstract model of your device or funtion.
# You can create instances from a class which represent
# individual devices or functions with specific properties/parameters
# e.g. houeseThermostat = Thermostat('192.168.1.230', 'House Thermostat')
class Thermostat():

    def __init__(self, ip, name):
        self.name = name
        self.url  = 'http://{}/tstat'.format(ip)
        # Utils

        # Do an initial read
        self.read()


    def read(self):
        success = False

        # Inialize the parameters with defaults
        # Add further value with 'self.value = strNV'
        self.temp   = strNV
        self.mode   = strNV
        self.fan    = strNV
        self.state  = strNV
        self.hold   = strNV
        self.target = strNV
        # For testing
        #self.temp   = '22' + strDegreeCelsius
        #self.mode   = strHeat
        #self.fan    = strOn
        #self.state  = strHeating
        #self.hold   = strOn
        #self.target = '22' + strDegreeCelsius

        # Send a GET request
        try:
            response = requests.get(self.url)
        except requests.exceptions.RequestException:
            response = None

        # Process the response - if valid
        if response and response.ok:
            #response data in json format
            try:
                rspJson = response.json()
            except ValueError:
                sucess = False
            else:
                # Overwrite default values with real values
                # Add futher value with self.value = function( rspJson['name'] )
                self.temp   = getTemp(rspJson['temp'])
                self.mode   = getTMode(rspJson['tmode'])
                self.fan    = getFMode(rspJson['fstate'])
                self.state  = getTState(rspJson['tstate'])
                self.hold   = getHold(rspJson['hold'])
                if 't_heat' in rspJson:
                    self.target = getTemp(rspJson['t_heat'])
                elif 't_cool' in rspJson:
                    self.target = getTemp(rspJson['t_cool'])
                success = True

        return success


    # Update individual or a combination of parameters
    def update(self, fan=None, mode=None, hold=None, target=None):
        success = False
        data = {}

        if fan and fan != self.fan:
            data['fmode'] = LabelToValue(fan, optionsFan)

        if mode and mode != self.mode and (not target or target == self.target):
            data['tmode'] = LabelToValue(mode, optionsMode)

        if hold and hold != self.hold:
            data['hold'] = LabelToValue(hold, optionsHold)

        if target and target != self.target:
            if (not mode and self.mode == strHeat) or mode == strHeat:
                data['t_heat'] = convertTemp(target[:-len(strDegreeCelsius if tempCelsius else strFahrenheit)])
            elif (not mode and self.mode == strCool) or mode == strCool:
                data['t_cool'] = convertTemp(target[:-len(strDegreeCelsius if tempCelsius else strFahrenheit)])

        if data:
            log('Sending data {} to URL {}'.format(data, self.url))
            try:
                response = requests.post(self.url, json=data)
            except requests.exceptions.RequestException:
                response = None

            if response and response.ok:
                try:
                    rspJson = response.json()
                except ValueError:
                    success = False
                else:
                    log('Response: {}'.format(response.text))
                    if 'success' in rspJson:
                        xbmc.sleep(delayTime * 1000)
                        success = self.read()

        return success


class SelectOptions(xbmcgui.WindowDialog):

    def __init__(self, optionList, x, y, width=None, height=None, returnLabel=False):
        self.optionList  = optionList
        self.returnLabel = returnLabel

        self.select = None
        self.button = []

        try:
            maxlen = max(len(option['label']) for option in optionList)
        except KeyError:
            return

        rows = len(self.optionList)

        self.btnX      = x
        self.btnY      = y
        self.btnWidth  = width or maxlen * 16
        self.btnHeight = height or 28

        self.addControl(xbmcgui.ControlImage(self.btnX, self.btnY, self.btnWidth, rows * self.btnHeight, __panel__))

        self.setControls()
        self.setNavigation()


    def setControls(self):
        for i, option in enumerate(self.optionList):
            self.button.append(xbmcgui.ControlButton(self.btnX, self.btnY + i * self.btnHeight,
                                                     self.btnWidth, self.btnHeight,
                                                     option['label'],
                                                     focusTexture = __textureFO__, noFocusTexture = __textureNF__,
                                                     alignment = ALIGN_CENTER_X|ALIGN_CENTER_Y,
                                                     font = REGULAR_FONT, textColor = WHITE, focusedColor = WHITE))
            self.addControl(self.button[-1])


    def setNavigation(self):
        numOptions = len(self.optionList)
        for i in range(numOptions):
            if i > 0:
                self.button[i].controlUp(self.button[i - 1])
            if i < numOptions - 1:
                self.button[i].controlDown(self.button[i + 1])


    def start(self):
        self.setFocus(self.button[0])
        self.doModal()

        return self.select


    def onControl(self, control):
        label = control.getLabel()
        self.select = label if self.returnLabel else LabelToValue(label, self.optionList)

        self.close()


# Create a class for our UI
class MyAddon(pyxbmct.AddonDialogWindow):

    def __init__(self, title=''):
        """Class constructor"""
        # Call the base class' constructor.
        super(MyAddon, self).__init__(title)

        xbmc.executebuiltin('ActivateWindow(busydialognocancel)')

        # Create the thermostats and initalize values
        self.houseThermostat = Thermostat(ipHouseThermostat, nameHouseThermostat)
        self.garageThermostat = Thermostat(ipGarageThermostat, nameGarageThermostat)

        # Set width, height and the grid parameters: 23 rows, 21 columns
        self.setGeometry(950, 483, 23, 21)

        # Call set controls method
        self.setControls()

        # Call set navigation method.
        self.setNavigation()

        # Connect Backspace button to close our addon.
        self.connect(pyxbmct.ACTION_NAV_BACK, self.close)

        self.setHousePendingChanges(False)
        self.getHouseValues(reload=False)

        self.setGaragePendingChanges(False)
        self.getGarageValues(reload=False)

        xbmc.executebuiltin('Dialog.Close(busydialognocancel)')


    def setControls(self):
        """Set up UI controls"""
        # House Controls:

        # Title in row 2, column 1 spanning over all 9 columns
        title = pyxbmct.Label(self.houseThermostat.name, alignment=ALIGN_CENTER_X|ALIGN_CENTER_Y, font=BIG_FONT, textColor=BLUE)
        self.placeControl(title, 2, 1, rowspan=2, columnspan=9)

        # Define inividual labels for each value that must be updated
        # Columns 1 & 2: TMode States
        self.houseModeOff = pyxbmct.RadioButton(strOff, textOffsetX=0, noFocusTexture=__transparent__)
        self.placeControl(self.houseModeOff, 6, 1, rowspan=2, columnspan=2)
        self.houseModeHeat = pyxbmct.RadioButton(strHeat, textOffsetX=0, noFocusTexture=__transparent__)
        self.placeControl(self.houseModeHeat, 8, 1, rowspan=2, columnspan=2)
        self.houseModeCool = pyxbmct.RadioButton(strCool, textOffsetX=0, noFocusTexture=__transparent__)
        self.placeControl(self.houseModeCool, 10, 1, rowspan=2, columnspan=2)
        self.houseModeAuto = pyxbmct.RadioButton(strAuto, textOffsetX=0, noFocusTexture=__transparent__)
        self.placeControl(self.houseModeAuto, 12, 1, rowspan=2, columnspan=2)

        # Columns 3 to 5: Temperature and TState
        self.houseTemp = pyxbmct.Button(strNV, textOffsetX=0, noFocusTexture=__transparent__, alignment=ALIGN_RIGHT|ALIGN_CENTER_Y, font=LARGE_FONT, textColor=TColor[self.houseThermostat.state])
        self.placeControl(self.houseTemp, 6, 3, rowspan=3, columnspan=3)
        self.houseState = pyxbmct.Label(strNV, font=SMALL_FONT, alignment=ALIGN_RIGHT|ALIGN_CENTER_Y)
        self.placeControl(self.houseState, 9, 3, rowspan=1, columnspan=3)

        # Columns 7 to 9: Fan, Hold and Target Temperature
        self.houseTargetLabel = pyxbmct.Button(strNV, textOffsetX=0, noFocusTexture=__transparent__, alignment=ALIGN_LEFT|ALIGN_CENTER_Y, font=SMALL_FONT, textColor=tColor[self.houseThermostat.mode])
        self.placeControl(self.houseTargetLabel, 6, 7, rowspan=1, columnspan=2)
        self.houseTarget = pyxbmct.Button(strNV, textOffsetX=0, noFocusTexture=__transparent__, alignment=ALIGN_RIGHT|ALIGN_CENTER_Y, textColor=tColor[self.houseThermostat.mode])
        self.placeControl(self.houseTarget, 7, 7, rowspan=2, columnspan=2)

        self.houseTargetUp = pyxbmct.Button(strArrowUp, textOffsetX=0, alignment=ALIGN_CENTER_X|ALIGN_CENTER_Y)
        self.placeControl(self.houseTargetUp, 6, 9, rowspan=2)
        self.houseTargetDn = pyxbmct.Button(strArrowDn, textOffsetX=0, alignment=ALIGN_CENTER_X|ALIGN_CENTER_Y)
        self.placeControl(self.houseTargetDn, 8, 9, rowspan=2)

        self.houseFan = pyxbmct.Button(strPadding + strFan, textOffsetX=0, alignment=ALIGN_LEFT|ALIGN_CENTER_Y)
        self.placeControl(self.houseFan, 10, 7, rowspan=2, columnspan=3)

        self.houseHold = pyxbmct.RadioButton(strPadding + strHold, textOffsetX=0, noFocusTexture=__transparent__)
        self.placeControl(self.houseHold, 12, 7, rowspan=2, columnspan=3)

        # Reload and set buttons in row 16, columns 2 to 4 and 6 to 8
        self.houseReload = pyxbmct.Button(strReload, textOffsetX=0, alignment=ALIGN_CENTER_X|ALIGN_CENTER_Y)
        self.placeControl(self.houseReload, 16, 2, rowspan=2, columnspan=3)
        self.houseSet = pyxbmct.Button(strSet, textOffsetX=0, alignment=ALIGN_CENTER_X|ALIGN_CENTER_Y) # , textColor=WHITE if self.housePendingChanges else GREY)
        self.placeControl(self.houseSet, 16, 6, rowspan=2, columnspan=3)

        # Vertical Line
        vLine =pyxbmct.Image(__verticalLine__, aspectRatio=1)
        self.placeControl(vLine, 5, 10, rowspan=13)

        # Garage controls:

        # Title in row 2, column 1 spanning over all 9 columns
        title = pyxbmct.Label(self.garageThermostat.name, alignment=ALIGN_CENTER_X|ALIGN_CENTER_Y, font=BIG_FONT, textColor=BLUE)
        self.placeControl(title, 2, 11, rowspan=2, columnspan=9)

        # Define inividual labels for each value that must be updated
        # Columns 11 & 12: TMode States
        self.garageModeOff = pyxbmct.RadioButton(strOff, textOffsetX=0, noFocusTexture=__transparent__)
        self.placeControl(self.garageModeOff, 6, 11, rowspan=2, columnspan=2)
        self.garageModeHeat = pyxbmct.RadioButton(strHeat, textOffsetX=0, noFocusTexture=__transparent__)
        self.placeControl(self.garageModeHeat, 8, 11, rowspan=2, columnspan=2)
        self.garageModeCool = pyxbmct.RadioButton(strCool, textOffsetX=0, noFocusTexture=__transparent__)
        self.placeControl(self.garageModeCool, 10, 11, rowspan=2, columnspan=2)
        self.garageModeAuto = pyxbmct.RadioButton(strAuto, textOffsetX=0, noFocusTexture=__transparent__)
        self.placeControl(self.garageModeAuto, 12, 11, rowspan=2, columnspan=2)

        # Columns 13 to 15: Temperature and TState
        self.garageTemp = pyxbmct.Button(strNV, textOffsetX=0, noFocusTexture=__transparent__, alignment=ALIGN_RIGHT|ALIGN_CENTER_Y, font=LARGE_FONT, textColor=TColor[self.garageThermostat.state])
        self.placeControl(self.garageTemp, 6, 13, rowspan=3, columnspan=3)
        self.garageState = pyxbmct.Label(strNV, font=SMALL_FONT, alignment=ALIGN_RIGHT|ALIGN_CENTER_Y)
        self.placeControl(self.garageState, 9, 13, rowspan=1, columnspan=3)

        # Columns 17 to 19: Fan, Hold and Target Temperature
        self.garageTargetLabel = pyxbmct.Button(strNV, textOffsetX=0, noFocusTexture=__transparent__, alignment=ALIGN_LEFT|ALIGN_CENTER_Y, font=SMALL_FONT, textColor=tColor[self.garageThermostat.mode])
        self.placeControl(self.garageTargetLabel, 6, 17, rowspan=1, columnspan=2)
        self.garageTarget = pyxbmct.Button(strNV, textOffsetX=0, noFocusTexture=__transparent__, alignment=ALIGN_RIGHT|ALIGN_CENTER_Y, textColor=tColor[self.garageThermostat.mode])
        self.placeControl(self.garageTarget, 7, 17, rowspan=2, columnspan=2)

        self.garageTargetUp = pyxbmct.Button(strArrowUp, textOffsetX=0, alignment=ALIGN_CENTER_X|ALIGN_CENTER_Y)
        self.placeControl(self.garageTargetUp, 6, 19, rowspan=2)
        self.garageTargetDn = pyxbmct.Button(strArrowDn, textOffsetX=0, alignment=ALIGN_CENTER_X|ALIGN_CENTER_Y)
        self.placeControl(self.garageTargetDn, 8, 19, rowspan=2)

        self.garageFan = pyxbmct.Button(strPadding + strFan, textOffsetX=0, alignment=ALIGN_LEFT|ALIGN_CENTER_Y)
        self.placeControl(self.garageFan, 10, 17, rowspan=2, columnspan=3)

        self.garageHold = pyxbmct.RadioButton(strPadding + strHold, textOffsetX=0, noFocusTexture=__transparent__)
        self.placeControl(self.garageHold, 12, 17, rowspan=2, columnspan=3)

        # Reload and set buttons in row 16, columns 12 to 14 and 16 to 18
        self.garageReload = pyxbmct.Button(strReload, textOffsetX=0, alignment=ALIGN_CENTER_X|ALIGN_CENTER_Y)
        self.placeControl(self.garageReload, 16, 12, rowspan=2, columnspan=3)
        self.garageSet = pyxbmct.Button(strSet, textOffsetX=0, alignment=ALIGN_CENTER_X|ALIGN_CENTER_Y) # , textColor=WHITE if self.garagePendingChanges else GREY)
        self.placeControl(self.garageSet, 16, 16, rowspan=2, columnspan=3)

        # Close button
        self.buttonClose = pyxbmct.Button(strClose)
        self.placeControl(self.buttonClose, 20, 9, rowspan=2, columnspan=3)

        # Connect the fan buttons
        self.connect(self.houseFan, self.setHouseFan)
        self.connect(self.garageFan, self.setGarageFan)

        # Connect the hold buttons
        self.connect(self.houseHold, self.setHouseHold)
        self.connect(self.garageHold, self.setGarageHold)

        # Connect the mode buttons
        self.connect(self.houseModeOff, lambda: self.setHouseMode(strOff))
        self.connect(self.houseModeHeat, lambda: self.setHouseMode(strHeat))
        self.connect(self.houseModeCool, lambda: self.setHouseMode(strCool))
        self.connect(self.houseModeAuto, lambda: self.setHouseMode(strAuto))
        self.connect(self.garageModeOff, lambda: self.setGarageMode(strOff))
        self.connect(self.garageModeHeat, lambda: self.setGarageMode(strHeat))
        self.connect(self.garageModeCool, lambda: self.setGarageMode(strCool))
        self.connect(self.garageModeAuto, lambda: self.setGarageMode(strAuto))

        # Connect the up buttons
        self.connect(self.houseTargetUp, self.setHouseTargetUp)
        self.connect(self.garageTargetUp, self.setGarageTargetUp)

        # Connect the down buttons
        self.connect(self.houseTargetDn, self.setHouseTargetDn)
        self.connect(self.garageTargetDn, self.setGarageTargetDn)

        # Connect the reload buttons
        self.connect(self.houseReload, self.reloadHouseValues)
        self.connect(self.garageReload, self.reloadGarageValues)

        # Connect the set buttons
        self.connect(self.houseSet, self.updateHouseValues)
        self.connect(self.garageSet, self.updateGarageValues)

        # Connect the close button
        self.connect(self.buttonClose, self.stop)


    def setNavigation(self):
        """Set up keyboard/remote navigation between controls."""

        self.houseModeOff.controlDown(self.houseModeHeat)
        self.houseModeOff.controlRight(self.houseTargetUp)
        self.houseModeHeat.controlUp(self.houseModeOff)
        self.houseModeHeat.controlDown(self.houseModeCool)
        self.houseModeHeat.controlRight(self.houseTargetDn)
        self.houseModeCool.controlUp(self.houseModeHeat)
        self.houseModeCool.controlDown(self.houseModeAuto)
        self.houseModeCool.controlRight(self.houseFan)
        self.houseModeAuto.controlUp(self.houseModeCool)
        self.houseModeAuto.controlDown(self.houseReload)
        self.houseModeAuto.controlRight(self.houseHold)

        self.garageModeOff.controlDown(self.garageModeHeat)
        self.garageModeOff.controlRight(self.garageFan)
        self.garageModeOff.controlLeft(self.houseTargetUp)
        self.garageModeHeat.controlUp(self.garageModeOff)
        self.garageModeHeat.controlDown(self.garageModeCool)
        self.garageModeHeat.controlRight(self.garageTargetDn)
        self.garageModeHeat.controlLeft(self.houseTargetDn)
        self.garageModeCool.controlUp(self.garageModeHeat)
        self.garageModeCool.controlDown(self.garageModeAuto)
        self.garageModeCool.controlRight(self.garageFan)
        self.garageModeCool.controlLeft(self.houseFan)
        self.garageModeAuto.controlUp(self.garageModeCool)
        self.garageModeAuto.controlDown(self.garageReload)
        self.garageModeAuto.controlRight(self.garageHold)
        self.garageModeAuto.controlLeft(self.houseHold)

        self.houseFan.controlUp(self.houseTargetDn)
        self.houseFan.controlLeft(self.houseModeCool)
        self.houseFan.controlRight(self.garageModeCool)
        self.houseFan.controlDown(self.houseHold)
        self.garageFan.controlUp(self.garageTargetDn)
        self.garageFan.controlLeft(self.garageModeCool)
        self.garageFan.controlDown(self.garageHold)

        self.houseHold.controlLeft(self.houseModeAuto)
        self.houseHold.controlRight(self.garageModeAuto)
        self.houseHold.controlUp(self.houseFan)
        self.houseHold.controlDown(self.houseSet)
        self.garageHold.controlLeft(self.garageModeAuto)
        self.garageHold.controlUp(self.garageFan)
        self.garageHold.controlDown(self.garageSet)

        self.houseTargetUp.controlDown(self.houseTargetDn)
        self.houseTargetUp.controlLeft(self.houseModeOff)
        self.houseTargetUp.controlRight(self.garageModeOff)
        self.houseTargetDn.controlUp(self.houseTargetUp)
        self.houseTargetDn.controlDown(self.houseFan)
        self.houseTargetDn.controlLeft(self.houseModeHeat)
        self.houseTargetDn.controlRight(self.garageModeHeat)
        self.garageTargetUp.controlDown(self.garageTargetDn)
        self.garageTargetUp.controlLeft(self.garageModeOff)
        self.garageTargetDn.controlUp(self.garageTargetUp)
        self.garageTargetDn.controlDown(self.garageFan)
        self.garageTargetDn.controlLeft(self.garageModeHeat)

        self.houseReload.controlUp(self.houseModeAuto)
        self.houseReload.controlRight(self.houseSet)
        self.houseReload.controlDown(self.buttonClose)
        self.houseSet.controlUp(self.houseHold)
        self.houseSet.controlLeft(self.houseReload)
        self.houseSet.controlRight(self.garageReload)
        self.houseSet.controlDown(self.buttonClose)
        self.garageReload.controlUp(self.garageModeAuto)
        self.garageReload.controlLeft(self.houseSet)
        self.garageReload.controlRight(self.garageSet)
        self.garageReload.controlDown(self.buttonClose)
        self.garageSet.controlUp(self.garageHold)
        self.garageSet.controlLeft(self.garageReload)
        self.garageSet.controlDown(self.buttonClose)

        self.buttonClose.controlUp(self.houseSet)

        # Set initial focus
        self.setFocus(self.buttonClose)


    def autoRefresh(self, refreshTime, stop):

        while True:
            waitTime = int(refreshTime)
            for i in range(waitTime):
                if stop():
                    return
                xbmc.sleep(1000)
            Thread(target=self.getHouseValues).start()
            Thread(target=self.getGarageValues).start()


    def start(self, refreshTime):
        self.stopFlag = False

        if refreshTime:
            Thread(target=self.autoRefresh, args=(refreshTime, lambda: self.stopFlag)).start()

        self.doModal()
        self.stopFlag = True # is this really required? Or just for safety?


    def onAction(self, action):
        if action in (ACTION_PREVIOUS_MENU, ACTION_STOP, ACTION_BACKSPACE, ACTION_NAV_BACK):
            self.stop()


    def stop(self):
        self.stopFlag = True
        self.close()


    def setHousePendingChanges(self, flag):
        self.housePendingChanges = flag
        #self.houseSet.setLabel(self.houseSet.getLabel(), textColor=WHITE if flag else GREY)
        self.houseSet.setEnabled(flag)


    def setGaragePendingChanges(self, flag):
        self.garagePendingChanges = flag
        #self.garageSet.setLabel(self.garageSet.getLabel(), textColor=WHITE if flag else GREY)
        self.garageSet.setEnabled(flag)


    def setHouseFan(self):
        # Calulate position of options menu from currently selected element
        # and open options menu
        dialog = SelectOptions(optionsFan,
                               self.houseFan.getX(),
                               self.houseFan.getY() + self.houseFan.getHeight() + 1,
                               width=self.houseFan.getWidth(),
                               height=self.houseFan.getHeight(),
                               returnLabel=True)
        value = dialog.start()
        del dialog

        if value:
            self.setHousePendingChanges(True)
            self.houseFan.setLabel(label2=str(value) + strPadding)


    def setGarageFan(self):
        # Calulate position of options menu from currently selected element
        # and open options menu
        dialog = SelectOptions(optionsFan,
                               self.garageFan.getX(),
                               self.garageFan.getY() + self.garageFan.getHeight() + 1,
                               width=self.garageFan.getWidth(),
                               height=self.garageFan.getHeight(),
                               returnLabel=True)
        value = dialog.start()
        del dialog

        if value:
            self.setGaragePendingChanges(True)
            self.garageFan.setLabel(label2=str(value) + strPadding)


    def setHouseHold(self):
        self.setHousePendingChanges(True)


    def setGarageHold(self):
        self.setGaragePendingChanges(True)


    def setHouseMode(self, mode):
        self.setHousePendingChanges(True)

        self.houseModeOff.setSelected(mode == strOff)
        self.houseModeHeat.setSelected(mode == strHeat)
        self.houseModeCool.setSelected(mode == strCool)
        self.houseModeAuto.setSelected(mode == strAuto)

        self.houseTargetLabel.setLabel(mode if mode == strCool or mode == strHeat else ' ', textColor=tColor[mode])
        self.houseTarget.setLabel(self.houseTarget.getLabel(), textColor=tColor[mode])


    def setGarageMode(self, mode):
        self.setGaragePendingChanges(True)

        self.garageModeOff.setSelected(mode == strOff)
        self.garageModeHeat.setSelected(mode == strHeat)
        self.garageModeCool.setSelected(mode == strCool)
        self.garageModeAuto.setSelected(mode == strAuto)

        self.garageTargetLabel.setLabel(mode if mode == strCool or mode == strHeat else ' ', textColor=tColor[mode])
        self.garageTarget.setLabel(self.garageTarget.getLabel(), textColor=tColor[mode])


    def setHouseTargetUp(self):
        current = self.houseTarget.getLabel()

        if current and current != strNV:
            self.setHousePendingChanges(True)
            current = current[:-len(strDegreeCelsius)]
            new = str(float(current) + 0.5)
            self.houseTarget.setLabel(new + strDegreeCelsius)


    def setGarageTargetUp(self):
        current = self.garageTarget.getLabel()

        if current and current != strNV:
            self.setGaragePendingChanges(True)
            current = current[:-len(strDegreeCelsius)]
            new = str(float(current) + 0.5)
            self.garageTarget.setLabel(new + strDegreeCelsius)


    def setHouseTargetDn(self):
        current = self.houseTarget.getLabel()

        if current and current != strNV:
            self.setHousePendingChanges(True)
            current = current[:-len(strDegreeCelsius)]
            new = str(float(current) - 0.5)
            self.houseTarget.setLabel(new + strDegreeCelsius)


    def setGarageTargetDn(self):
        current = self.garageTarget.getLabel()

        if current and current != strNV:
            self.setGaragePendingChanges(True)
            current = current[:-len(strDegreeCelsius)]
            new = str(float(current) - 0.5)
            self.garageTarget.setLabel(new + strDegreeCelsius)


    def updateHouseValues(self):
        if not self.housePendingChanges:
            return

        updateFan = self.houseFan.getLabel2().strip()
        if updateFan == strNV:
            updateFan = None

        updateHold = strOn if self.houseHold.isSelected() else strOff

        updateMode = None
        if self.houseModeOff.isSelected():
            updateMode = strOff
        elif self.houseModeHeat.isSelected():
            updateMode = strHeat
        elif self.houseModeCool.isSelected():
            updateMode = strCool
        elif self.houseModeAuto.isSelected():
            updateMode = strAuto

        updateTarget = self.houseTarget.getLabel()
        if updateTarget == strNV:
            updateTarget = None

        xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
        success = self.houseThermostat.update(fan=updateFan, mode=updateMode, hold=updateHold, target=updateTarget)
        self.setHousePendingChanges(False) # self.setHousePendingChanges(not success)
        xbmc.executebuiltin('Dialog.Close(busydialognocancel)')

        self.getHouseValues(reload=False)


    def updateGarageValues(self):
        if not self.garagePendingChanges:
            return

        updateFan = self.garageFan.getLabel2().strip()
        if updateFan == strNV:
            updateFan = None

        updateHold = strOn if self.garageHold.isSelected() else strOff

        updateMode = None
        if self.garageModeOff.isSelected():
            updateMode = strOff
        elif self.garageModeHeat.isSelected():
            updateMode = strHeat
        elif self.garageModeCool.isSelected():
            updateMode = strCool
        elif self.garageModeAuto.isSelected():
            updateMode = strAuto

        updateTarget = self.garageTarget.getLabel()
        if updateTarget == strNV:
            updateTarget = None

        xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
        success = self.garageThermostat.update(fan=updateFan, mode=updateMode, hold=updateHold, target=updateTarget)
        self.setGaragePendingChanges(False) # self.setGaragePendingChanges(not success)
        xbmc.executebuiltin('Dialog.CLose(busydialognocancel)')

        self.getGarageValues(reload=False)


    def reloadHouseValues(self):
        self.setHousePendingChanges(False)
        self.getHouseValues()


    def reloadGarageValues(self):
        self.setGaragePendingChanges(False)
        self.getGarageValues()


    def getHouseValues(self, reload=True):
        if reload:
            xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
            self.houseThermostat.read()
            xbmc.executebuiltin('Dialog.Close(busydialognocancel)')

        self.houseTemp.setLabel(self.houseThermostat.temp, textColor=TColor[self.houseThermostat.state])
        self.houseState.setLabel(strState.format(self.houseThermostat.state))

        if self.housePendingChanges:
            return

        self.houseModeOff.setSelected(self.houseThermostat.mode == strOff)
        self.houseModeHeat.setSelected(self.houseThermostat.mode == strHeat)
        self.houseModeCool.setSelected(self.houseThermostat.mode == strCool)
        self.houseModeAuto.setSelected(self.houseThermostat.mode == strAuto)
        self.houseFan.setLabel(label2=self.houseThermostat.fan + strPadding)
        self.houseHold.setSelected(self.houseThermostat.hold == strOn)
        self.houseTargetLabel.setLabel(self.houseThermostat.mode if self.houseThermostat.mode == strCool or self.houseThermostat.mode == strHeat else ' ', textColor=tColor[self.houseThermostat.mode])
        self.houseTarget.setLabel(self.houseThermostat.target, textColor=tColor[self.houseThermostat.mode])


    def getGarageValues(self, reload=True):
        if reload:
            xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
            self.garageThermostat.read()
            xbmc.executebuiltin('Dialog.CLose(busydialognocancel)')

        self.garageTemp.setLabel(self.garageThermostat.temp, textColor=TColor[self.garageThermostat.state])
        self.garageState.setLabel(strState.format(self.garageThermostat.state))

        if self.garagePendingChanges:
            return

        self.garageModeOff.setSelected(self.garageThermostat.mode == strOff)
        self.garageModeHeat.setSelected(self.garageThermostat.mode == strHeat)
        self.garageModeCool.setSelected(self.garageThermostat.mode == strCool)
        self.garageModeAuto.setSelected(self.garageThermostat.mode == strAuto)
        self.garageFan.setLabel(label2=self.garageThermostat.fan + strPadding)
        self.garageHold.setSelected(self.garageThermostat.hold == strOn)
        self.garageTargetLabel.setLabel(self.garageThermostat.mode if self.garageThermostat.mode == strCool or self.garageThermostat.mode == strHeat else ' ', textColor=tColor[self.garageThermostat.mode])
        self.garageTarget.setLabel(self.garageThermostat.target, textColor=tColor[self.houseThermostat.mode])


if __name__ == '__main__':
    if not xbmcvfs.exists(__settings__):
        xbmc.executebuiltin('Addon.OpenSettings(' + __addon_id__ + ')')

    myaddon = MyAddon(__addon_name__)
    myaddon.start(autoRefreshTime)
    del myaddon
