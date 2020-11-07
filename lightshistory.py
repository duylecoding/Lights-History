"""BlinkyTape Python communication library.
  This code assumes stock serialLoop() in the firmware.
  Commands are issued in 3-byte blocks, with pixel data
  encoded in RGB triplets in range 0-254, sent sequentially
  and a triplet ending with a 255 causes the accumulated pixel
  data to display (a show command).
  Note that with the stock firmware changing the maximum brightness
  over serial communication is impossible.
"""

import serial
import serial.tools.list_ports
import random
import time

# For Python3 support- always run strings through a bytes converter
import sys
if sys.version_info < (3,):
    def encode(x):
        return x
else:
    import codecs

    def encode(x):
        return codecs.latin_1_encode(x)[0]


class BlinkyTape(object):
    def __init__(self, port, ledCount=60, buffered=True):
        """Creates a BlinkyTape object and opens the port.
        Parameters:
          port
            Required, port name as accepted by PySerial library:
            http://pyserial.sourceforge.net/pyserial_api.html#serial.Serial
            It is the same port name that is used in Arduino IDE.
            Ex.: COM5 (Windows), /dev/ttyACM0 (Linux).
          ledCount
            Optional, total number of LEDs to work with,
            defaults to 60 LEDs. The limit is enforced and an
            attempt to send more pixel data will throw an exception.
          buffered
            Optional, enabled by default. If enabled, will buffer
            pixel data until a show command is issued. If disabled,
            the data will be sent in byte triplets as expected by firmware,
            with immediate flush of the serial buffers (slower).
        """
        self.port = port
        self.ledCount = ledCount
        self.position = 0
        self.buffered = buffered
        self.buf = ""
        self.serial = serial.Serial(port, 115200)
        self.show()  # Flush any incomplete data

    def send_list(self, colors):
        if len(colors) > self.ledCount:
            raise RuntimeError("Attempting to set pixel outside range!")
        for r, g, b in colors:
            self.sendPixel(r, g, b)
        self.show()

    def send_list(self, colors):
        data = ""
        for r, g, b in colors:
            data += chr(r) + chr(g) + chr(b)

        data = data.replace(chr(255), chr(254))

        self.serial.write(encode(data))
        self.show()

    def sendData(self, data):
        data = data.replace(chr(255), chr(254))
        self.serial.write(encode(data))
        self.show()

    def sendPixel(self, r, g, b):
        """Sends the next pixel data triplet in RGB format.
        Values are clamped to 0-254 automatically.
        Throws a RuntimeException if [ledCount] pixels are already set.
        """
        data = ""
        data = chr(r) + chr(g) + chr(b)
        data = data.replace(chr(255), chr(254))

        if self.position < self.ledCount:
            if self.buffered:
                self.buf += data
            else:
                self.serial.write(encode(data))
                self.serial.flush()
            self.position += 1
        else:
            raise RuntimeError("Attempting to set pixel outside range!")

    def show(self):
        """Sends the command(s) to display all accumulated pixel data.
        Resets the next pixel position to 0, flushes the serial buffer,
        and discards any accumulated responses from BlinkyTape.
        """
        control = chr(255)
        if self.buffered:
            # Fix an OS X specific bug where sending more than 383 bytes of data at once
            # hangs the BlinkyTape controller. Why this is???
            # TODO: Test me on other platforms
            CHUNK_SIZE = 300

            self.buf += control
            for i in range(0, len(self.buf), CHUNK_SIZE):
                self.serial.write(encode(self.buf[i:i+CHUNK_SIZE]))
                self.serial.flush()

            self.buf = ""
        else:
            self.serial.write(encode(control))
        self.serial.flush()
        self.serial.flushInput()  # Clear responses from BlinkyTape, if any
        self.position = 0

    def displayColor(self, r, g, b):
        """Fills [ledCount] pixels with RGB color and shows it."""
        for i in range(0, self.ledCount):
            self.sendPixel(r, g, b)
        self.show()

    def resetToBootloader(self):
        """Initiates a reset on BlinkyTape.
        Note that it will be disconnected.
        """
        self.serial.setBaudrate(1200)
        self.close()

    def close(self):
        """Safely closes the serial port."""
        self.serial.close()

    def clear(self):
      for i in range(0, self.ledCount):
            self.sendPixel(255, 255, 255)
      self.show()
    
    def show_win(self):
        for j in range(0, 5):
            self.sendPixel(10, 61, 245) # blue
        self.sendPixel(255, 255, 255)

    def show_loss(self):
        for j in range(0, 5):
            self.sendPixel(224, 88, 186) #pink
        self.sendPixel(255, 255, 255)

    def show_match_history(self, winLoss):
      for i in range(0, len(winLoss)):
        if(winLoss[i] == True):
            self.show_win()
        else:
            self.show_loss()
      self.show()

def myprint(msg):
    print("\x1b[33;21m{}\x1b[0m".format(msg))
  
if __name__ == "__main__":
    import requests

    host = "https://na1.api.riotgames.com"
    key = "RGAPI-4e2016ed-9cf1-404c-9d43-92607af6d491"

    accountInfo = requests.get(host + "/lol/summoner/v4/summoners/by-name/Sexiest?api_key="+key).json()
    myprint(accountInfo)
    accountId = accountInfo['accountId']
    last10Matches = requests.get(host + "/lol/match/v4/matchlists/by-account/" + accountId + "?queue=420&endIndex=10&beginIndex=0&api_key="+key).json()
    #https://na1.api.riotgames.com/lol/match/v4/timelines/by-match/3650425155?api_key=RGAPI-4e2016ed-9cf1-404c-9d43-92607af6d491
    matches = last10Matches['matches']
    matchIds = list(map(lambda x: x['gameId'], matches))
    winLoss = []

    #3651483111, 3651414773
    for x in range(0, len(matchIds)):
        match = requests.get(host + "/lol/match/v4/matches/" + str(matchIds[x]) + "?api_key=" + key).json()
        #match = requests.get(host + "/lol/match/v4/matches/" + "3651483111" + "?api_key=" + key).json()
        participantIdentities = match['participantIdentities']
        sexiest = next((x for x in participantIdentities if x['player']['summonerName'] == 'Sexiest'), [])
        participantId = sexiest['participantId']
        participants = match['participants']
        teamId = next((x for x in participants if x['participantId'] == participantId), [])['teamId']
        teams = match['teams']
        sexiestTeam = next((x for x in teams if x['teamId'] == teamId), [])
        win = sexiestTeam['win'] == 'Win'
        winLoss.append(win)

    bt = BlinkyTape(serial.tools.list_ports.comports()[0].device)
    bt.show_match_history(winLoss)
    bt.close()

    