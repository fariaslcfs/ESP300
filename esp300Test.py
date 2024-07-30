#!/usr/bin/python3

import time
import pyvisa

rm = pyvisa.ResourceManager()
gpib_device = rm.open_resource('GPIB0::5::INSTR')  # Ajuste o endereço conforme necessário
#gpib_device.query('1PA0')
#tiem.sleep(1)
#gpib_device.query('1WS')
#time.sleep(1)
#gpib_device.query('1TS')
#time.sleep(1)
print(gpib_device.query('VE'))
