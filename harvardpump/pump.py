#!/usr/bin/python

import serial
import logging

#logging.basicConfig(level=logging.DEBUG)

class Pump:
        prompts = {
                ':': 'stopped',
                '>': 'running',
                '<': 'reverse',
                '*': 'stalled' }
        ranges = [ 'uL/min', 'mL/min', 'uL/hr' , 'mL/hr' ]

        def __init__(self, port=0):
                self.port = serial.Serial(port, baudrate=9600, bytesize=8, parity='N',
                                          stopbits=2, xonxoff=False, rtscts=False,
                                          timeout=0.1)

        def _write(self, cmd):
                logging.debug('write: %s' % cmd)
                self.port.write("%s\r" % cmd)

        def _read_reply(self):
                s = ''
                for i in range(5): # Try reading up to 5 characters for prompt
                        s = self.port.read(1)
                        logging.debug("read: %s" % s)
                        if Pump.prompts.has_key(s):
                                return Pump.prompts[s]
                        elif s == 'O' or s == '?':
                                break # Error occurred

                s += self.port.readline()
                logging.info('oops: %s' % s)
                self._read_reply()
                if s.startswith("OOR"):
                        raise Exception("Out of range")
                elif s.startswith("?"):
                        raise Exception("Unrecognized command")
                else:
                        raise Exception("Uh oh. Something unknown went wrong")

        def _read_value(self):
                s = self.port.read(8)
                self._read_reply()
                return float(s)

        def get_status(self):
                """ Get status of pump """
                self._write("")
                return self._read_reply()

        def set_diameter(self, value):
                """ Set diameter of syringe in millimeters """
                self._write("MMD %f" % value)
                return self._read_reply()

        def __value_func(cmd):
                def f(self):
                        self._write(cmd)
                        return self._read_value()
                return f
        
        get_diameter = __value_func('DIA')
        get_flow_rate = __value_func('RAT')
        get_volume_accum = __value_func('VOL')
        get_version = __value_func('VER')
        get_target_volume = __value_func('TAR')

        def get_range(self):
                ranges = {
                        'ML/H': 'mL/hr',
                        'ML/M': 'mL/min',
                        'UL/H': 'uL/hr',
                        'UL/M': 'uL/min' }
                self._write("RNG")
                self.port.read(2) # Read CR/LF
                range = self.port.read(4)
                self.port.read(2) # Read CR/LF
                self._read_reply()
                return ranges[range]


        def __command_func(cmd):
                def f(self):
                        self._write(cmd)
                        self._read_reply()
                return f

        start = __command_func('RUN')
        stop = __command_func('STP')
        clear_volume_accum = __command_func('CLV')
        clear_target = __command_func('CLT')
        reverse = __command_func('REV')

        def set_flow_rate(self, value, range):
                """ Set flow rate in given range """
                ranges = {
                        'uL/min': 'ULM',
                        'mL/min': 'MLM',
                        'uL/hr' : 'ULH',
                        'mL/hr' : 'MLH' }
                
                if not ranges.has_key(range):
                        raise Exception("Invalid range")
                self._write("%s %f" % (ranges[range], value))
                self._read_reply()

        def set_target_volume(self, value):
                """ Set the target volume """
                self._write("MLT %f" % value)
                self._read_reply()

