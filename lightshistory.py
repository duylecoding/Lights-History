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

    def show_match_history(self):
      for i in range(0, 10):
        if(random.randint(0,1) == 0):
            self.show_win()
        else:
            self.show_loss()
      self.show()
  
if __name__ == "__main__":
    host = "na1.api.riotgames.com"

    bt = BlinkyTape(serial.tools.list_ports.comports()[0].device)
    bt.show_match_history()
    bt.close()

    