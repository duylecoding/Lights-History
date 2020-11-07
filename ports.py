import serial.tools.list_ports
print([comport.device for comport in serial.tools.list_ports.comports()])
print(serial.tools.list_ports.comports()[0].device)