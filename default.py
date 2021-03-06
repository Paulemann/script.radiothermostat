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

# Custom Settings
ipThermostat1       = __addon__.getSetting('ipAddress1') or '1.1.1.1'
nameThermostat1     = __addon__.getSetting('name1') or 'Thermostat 1'
ipThermostat2       = __addon__.getSetting('ipAddress2') or '1.1.1.2'
nameThermostat2     = __addon__.getSetting('name2') or 'Thermostat 2'
tempCelsius         = bool(__addon__.getSetting('tempCelsius') == 'true') # True
colorMode           = bool(__addon__.getSetting('colorMode') == 'true') # True
autoRefreshTime     = int(__addon__.getSetting('refreshTime')) # 30

# Time delay between thermostat update and read in seconds
delayTime           = 2
doTest              = True


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
# e.g. houseThermostat = Thermostat('192.168.1.230', 'House Thermostat')
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
        if doTest:
            self.temp   = '22' + strDegreeCelsius
            self.mode   = strHeat
            self.fan    = strOn
            self.state  = strHeating
            self.hold   = strOn
            self.target = '22' + strDegreeCelsius

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

        self.control = [{}, {}]

        # Create the thermostats and initalize values
        self.thermostat = [
                           Thermostat(ipThermostat1, nameThermostat1),
                           Thermostat(ipThermostat2, nameThermostat2)
                          ]

        # Call the base class' constructor.
        super(MyAddon, self).__init__(title)

        xbmc.executebuiltin('ActivateWindow(busydialognocancel)')

        # Set width, height and the grid parameters: 23 rows, 21 columns
        self.setGeometry(950, 483, 23, 21)

        # Call set controls method
        self.setControls()

        # Call set navigation method.
        self.setNavigation()

        # Connect Backspace button to close our addon.
        self.connect(pyxbmct.ACTION_NAV_BACK, self.close)

        for i in range(2):
            self.setPendingChanges(i, False)
            self.getValues(i, reload=False)

        xbmc.executebuiltin('Dialog.Close(busydialognocancel)')


    def setControls(self):
        """Set up UI controls"""

        for i, control in enumerate(self.control):
            # Title in row 2, column 1 spanning over all 9 columns
            control['title']       = pyxbmct.Label(self.thermostat[i].name, alignment=ALIGN_CENTER_X|ALIGN_CENTER_Y, font=BIG_FONT, textColor=BLUE)
            control['modeOff']     = pyxbmct.RadioButton(strOff, textOffsetX=3, noFocusTexture=__transparent__)
            control['modeHeat']    = pyxbmct.RadioButton(strHeat, textOffsetX=3, noFocusTexture=__transparent__)
            control['modeCool']    = pyxbmct.RadioButton(strCool, textOffsetX=3, noFocusTexture=__transparent__)
            control['modeAuto']    = pyxbmct.RadioButton(strAuto, textOffsetX=3, noFocusTexture=__transparent__)
            control['temp']        = pyxbmct.Button(strNV, textOffsetX=0, noFocusTexture=__transparent__, alignment=ALIGN_RIGHT|ALIGN_CENTER_Y, font=LARGE_FONT, textColor=TColor[self.thermostat[i].state])
            control['state']       = pyxbmct.Label(strNV, font=SMALL_FONT, alignment=ALIGN_RIGHT|ALIGN_CENTER_Y)
            control['targetLabel'] = pyxbmct.Button(strNV, textOffsetX=0, noFocusTexture=__transparent__, alignment=ALIGN_LEFT|ALIGN_CENTER_Y, font=SMALL_FONT, textColor=tColor[self.thermostat[i].mode])
            control['target']      = pyxbmct.Button(strNV, textOffsetX=0, noFocusTexture=__transparent__, alignment=ALIGN_RIGHT|ALIGN_CENTER_Y, textColor=tColor[self.thermostat[i].mode])
            control['targetUp']    = pyxbmct.Button(strArrowUp, textOffsetX=0, alignment=ALIGN_CENTER_X|ALIGN_CENTER_Y)
            control['targetDn']    = pyxbmct.Button(strArrowDn, textOffsetX=0, alignment=ALIGN_CENTER_X|ALIGN_CENTER_Y)
            control['fan']         = pyxbmct.Button(strFan, textOffsetX=3, alignment=ALIGN_LEFT|ALIGN_CENTER_Y)
            control['hold']        = pyxbmct.RadioButton(strHold, textOffsetX=3, noFocusTexture=__transparent__)
            control['reload']      = pyxbmct.Button(strReload)
            control['apply']       = pyxbmct.Button(strSet)

            self.placeControl(control['title'], 2, 1 + i * 10, rowspan=2, columnspan=9)

            # Define inividual labels for each value that must be updated
            # Columns 1 & 2: TMode States
            self.placeControl(control['modeOff'], 6, 1 + i * 10, rowspan=2, columnspan=2)
            self.placeControl(control['modeHeat'], 8, 1 + i * 10, rowspan=2, columnspan=2)
            self.placeControl(control['modeCool'], 10, 1 + i * 10, rowspan=2, columnspan=2)
            self.placeControl(control['modeAuto'], 12, 1 + i * 10, rowspan=2, columnspan=2)

            # Columns 3 to 5: Temperature and TState
            self.placeControl(control['temp'], 6, 3 + i * 10, rowspan=3, columnspan=3)
            self.placeControl(control['state'], 9, 3 + i * 10, rowspan=1, columnspan=3)

            # Columns 7 to 9: Fan, Hold and Target Temperature
            self.placeControl(control['targetLabel'], 6, 7 + i * 10, rowspan=1, columnspan=2)
            self.placeControl(control['target'], 7, 7 + i * 10, rowspan=2, columnspan=2)
            self.placeControl(control['targetUp'], 6, 9 + i * 10, rowspan=2)
            self.placeControl(control['targetDn'], 8, 9 + i * 10, rowspan=2)

            self.placeControl(control['fan'], 10, 7 + i * 10, rowspan=2, columnspan=3)
            self.placeControl(control['hold'], 12, 7 + i * 10, rowspan=2, columnspan=3)

            # Reload and set buttons in row 16, columns 2 to 4 and 6 to 8
            self.placeControl(control['reload'], 16, 2 + i * 10, rowspan=2, columnspan=3)
            self.placeControl(control['apply'], 16, 6 + i * 10, rowspan=2, columnspan=3)

            # Connect the buttons
            self.connect(control['fan'], (lambda: self.setFan(0)) if i == 0 else (lambda: self.setFan(1)))
            self.connect(control['hold'], (lambda: self.setHold(0)) if i == 0 else (lambda: self.setHold(1)))
            self.connect(control['modeOff'], (lambda: self.setMode(0, strOff)) if i == 0 else (lambda: self.setMode(1, strOff)))
            self.connect(control['modeHeat'], (lambda: self.setMode(0, strHeat)) if i == 0 else (lambda: self.setMode(1, strHeat)))
            self.connect(control['modeCool'], (lambda: self.setMode(0, strCool)) if i == 0 else (lambda: self.setMode(1, strCool)))
            self.connect(control['modeAuto'], (lambda: self.setMode(0, strAuto)) if i == 0 else (lambda: self.setMode(1, strAuto)))
            self.connect(control['targetUp'], (lambda: self.setTargetUp(0)) if i == 0 else (lambda: self.setTargetUp(1)))
            self.connect(control['targetDn'], (lambda: self.setTargetDn(0)) if i == 0 else (lambda: self.setTargetDn(1)))
            self.connect(control['reload'], (lambda: self.reloadValues(0)) if i == 0 else (lambda: self.reloadValues(1)))
            self.connect(control['apply'], (lambda: self.applyValues(0)) if i == 0 else (lambda: self.applyValues(1)))

        # Vertical Line
        vLine =pyxbmct.Image(__verticalLine__, aspectRatio=1)
        self.placeControl(vLine, 5, 10, rowspan=13)

        # Close button
        self.buttonClose = pyxbmct.Button(strClose)
        self.placeControl(self.buttonClose, 20, 9, rowspan=2, columnspan=3)

        # Connect the close button
        self.connect(self.buttonClose, self.stop)


    def setNavigation(self):
        """Set up keyboard/remote navigation between controls."""

        for i in range(2):
            self.control[i]['modeOff'].controlDown(self.control[i]['modeHeat'])
            self.control[i]['modeOff'].controlRight(self.control[i]['targetUp'])
            self.control[i]['modeHeat'].controlUp(self.control[i]['modeOff'])
            self.control[i]['modeHeat'].controlDown(self.control[i]['modeCool'])
            self.control[i]['modeHeat'].controlRight(self.control[i]['targetDn'])
            self.control[i]['modeCool'].controlUp(self.control[i]['modeHeat'])
            self.control[i]['modeCool'].controlDown(self.control[i]['modeAuto'])
            self.control[i]['modeCool'].controlRight(self.control[i]['fan'])
            self.control[i]['modeAuto'].controlUp(self.control[i]['modeCool'])
            self.control[i]['modeAuto'].controlDown(self.control[i]['reload'])
            self.control[i]['modeAuto'].controlRight(self.control[i]['hold'])

            self.control[i]['fan'].controlUp(self.control[i]['targetDn'])
            self.control[i]['fan'].controlLeft(self.control[i]['modeCool'])
            self.control[i]['fan'].controlDown(self.control[i]['hold'])

            self.control[i]['hold'].controlLeft(self.control[i]['modeAuto'])
            self.control[i]['hold'].controlUp(self.control[i]['fan'])
            self.control[i]['hold'].controlDown(self.control[i]['apply'])

            self.control[i]['targetUp'].controlDown(self.control[i]['targetDn'])
            self.control[i]['targetUp'].controlLeft(self.control[i]['modeOff'])
            self.control[i]['targetDn'].controlUp(self.control[i]['targetUp'])
            self.control[i]['targetDn'].controlDown(self.control[i]['fan'])
            self.control[i]['targetDn'].controlLeft(self.control[i]['modeHeat'])

            self.control[i]['reload'].controlUp(self.control[i]['modeAuto'])
            self.control[i]['reload'].controlRight(self.control[i]['apply'])
            self.control[i]['reload'].controlDown(self.buttonClose)

            self.control[i]['apply'].controlUp(self.control[i]['hold'])
            self.control[i]['apply'].controlLeft(self.control[i]['reload'])
            self.control[i]['apply'].controlDown(self.buttonClose)

            if i == 1:
                self.control[i]['modeOff'].controlLeft(self.control[i - 1]['targetUp'])
                self.control[i]['modeHeat'].controlLeft(self.control[i - 1]['targetDn'])
                self.control[i]['modeCool'].controlLeft(self.control[i - 1]['fan'])
                self.control[i]['modeAuto'].controlLeft(self.control[i - 1]['hold'])
                self.control[i]['reload'].controlLeft(self.control[i - 1]['apply'])

                self.control[i - 1]['targetUp'].controlRight(self.control[i]['modeOff'])
                self.control[i - 1]['targetDn'].controlRight(self.control[i]['modeHeat'])
                self.control[i - 1]['fan'].controlRight(self.control[i]['modeCool'])
                self.control[i - 1]['hold'].controlRight(self.control[i]['modeAuto'])
                self.control[i - 1]['apply'].controlRight(self.control[i]['reload'])

        self.buttonClose.controlUp(self.control[0]['reload'])

        # Set initial focus
        self.setFocus(self.buttonClose)


    def autoRefresh(self, refreshTime, stop):
        while True:
            waitTime = int(refreshTime)
            for i in range(waitTime):
                if stop():
                    return
                xbmc.sleep(1000)
            for index in range(2):
                Thread(target=self.getValues, args=(index,)).start()


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


    def setPendingChanges(self, index, flag):
        control = self.control[index]

        control['pendingChanges'] = flag
        #control['apply'].setLabel(control['apply'].getLabel(), textColor=WHITE if flag else GREY)
        control['apply'].setEnabled(flag)


    def setFan(self, index):
        # Calulate position of options menu from currently selected element
        # and open options menu
        control = self.control[index]

        dialog = SelectOptions(optionsFan,
                               control['fan'].getX(),
                               control['fan'].getY() + self.control[0]['fan'].getHeight() + 1,
                               width=control['fan'].getWidth(),
                               height=control['fan'].getHeight(),
                               returnLabel=True)
        value = dialog.start()
        del dialog

        if value:
            self.setPendingChanges(index, True)
            control['fan'].setLabel(label2=str(value))


    def setHold(self, index):
        self.setPendingChanges(index, True)


    def setMode(self, index, mode):
        control = self.control[index]

        self.setPendingChanges(index, True)

        control['modeOff'].setSelected(mode == strOff)
        control['modeHeat'].setSelected(mode == strHeat)
        control['modeCool'].setSelected(mode == strCool)
        control['modeAuto'].setSelected(mode == strAuto)

        control['targetLabel'].setLabel(mode if mode == strCool or mode == strHeat else ' ', textColor=tColor[mode])
        control['target'].setLabel(control['target'].getLabel(), textColor=tColor[mode])


    def setTargetUp(self, index):
        control = self.control[index]

        current = control['target'].getLabel()

        if current and current != strNV:
            self.setPendingChanges(index, True)
            current = current[:-len(strDegreeCelsius)]
            new = str(float(current) + 0.5)
            control['target'].setLabel(new + strDegreeCelsius)


    def setTargetDn(self, index):
        control = self.control[index]

        current = control['target'].getLabel()

        if current and current != strNV:
            self.setPendingChanges(index, True)
            current = current[:-len(strDegreeCelsius)]
            new = str(float(current) - 0.5)
            control['target'].setLabel(new + strDegreeCelsius)


    def applyValues(self, index):
        control = self.control[index]
        thermostat = self.thermostat[index]

        if not control['pendingChanges']:
            return

        updateFan = control['fan'].getLabel2().strip()
        if updateFan == strNV:
            updateFan = None

        updateHold = strOn if control['hold'].isSelected() else strOff

        updateMode = None
        if control['modeOff'].isSelected():
            updateMode = strOff
        elif control['modeHeat'].isSelected():
            updateMode = strHeat
        elif control['modeCool'].isSelected():
            updateMode = strCool
        elif control['modeAuto'].isSelected():
            updateMode = strAuto

        updateTarget = control['target'].getLabel()
        if updateTarget == strNV:
            updateTarget = None

        xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
        success = thermostat.update(fan=updateFan, mode=updateMode, hold=updateHold, target=updateTarget)
        self.setPendingChanges(index, False) # self.setPendingChanges(control, not success)
        xbmc.executebuiltin('Dialog.Close(busydialognocancel)')

        self.getValues(index, reload=False)


    def reloadValues(self, index):
        self.setPendingChanges(index, False)
        self.getValues(index)


    def getValues(self, index, reload=True):
        control = self.control[index]
        thermostat = self.thermostat[index]

        if reload:
            xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
            thermostat.read()
            xbmc.executebuiltin('Dialog.Close(busydialognocancel)')

        control['temp'].setLabel(thermostat.temp, textColor=TColor[thermostat.state])
        control['state'].setLabel(strState.format(thermostat.state))

        if control['pendingChanges']:
            return

        control['modeOff'].setSelected(thermostat.mode == strOff)
        control['modeHeat'].setSelected(thermostat.mode == strHeat)
        control['modeCool'].setSelected(thermostat.mode == strCool)
        control['modeAuto'].setSelected(thermostat.mode == strAuto)
        control['fan'].setLabel(label2=thermostat.fan)
        control['hold'].setSelected(thermostat.hold == strOn)
        control['targetLabel'].setLabel(thermostat.mode if thermostat.mode == strCool or thermostat.mode == strHeat else ' ', textColor=tColor[thermostat.mode])
        control['target'].setLabel(thermostat.target, textColor=tColor[thermostat.mode])


if __name__ == '__main__':
    if not xbmcvfs.exists(__settings__):
        xbmc.executebuiltin('Addon.OpenSettings(' + __addon_id__ + ')')

    myaddon = MyAddon(__addon_name__)
    myaddon.start(autoRefreshTime)
    del myaddon
