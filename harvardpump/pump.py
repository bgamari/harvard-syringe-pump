#!/usr/bin/python

import serial
import logging

logging.basicConfig(level=logging.DEBUG)

class Model22(object):
        prompts = {
                ':': 'stopped',
                '>': 'running',
                '<': 'reverse',
                '*': 'stalled' }
        ranges = [ 'uL/min', 'mL/min', 'uL/hr' , 'mL/hr' ]

        def __init__(self, port=0):
                #self.port = serial.Serial(port, baudrate=9600, bytesize=8, parity='N',
                #                          stopbits=2, xonxoff=False, rtscts=False,
                #                          timeout=0.1)
                self.port = serial.Serial(port, baudrate=9600, stopbits=2)

        def _write(self, cmd):
                logging.debug('write: %s' % cmd)
                self.port.write("%s\r" % cmd)

        def _read_reply(self):
                s = ''
                for i in range(5): # Try reading up to 5 characters for prompt
                        s = self.port.read(1)
                        logging.debug("read: %s" % s)
                        if Model22.prompts.has_key(s):
                                return Model22.prompts[s]
                        elif s == 'O' or s == '?':
                                break # Error occurred

                s += self.port.readline()
                logging.info('oops: %s' % s)
                if s.startswith("OOR"):
                        raise RuntimeError("Out of range")
                elif s.startswith("?"):
                        raise RuntimeError("Unrecognized command")
                else:
                        raise RuntimeError("Unrecognized response: %s" % s)

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
                print self.port.read(2) # Read CR/LF
                rng = self.port.read(2)
                if '?' in rng: return None
                rng += self.port.read(2)
                self.port.read(2) # Read CR/LF
                self._read_reply()
                return ranges[rng]

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

        def set_direction(self, dir):
                status = self.get_status()
                if status == 'running' and dir == -1 or \
                   status == 'reverse' and dir == +1 or \
                   status == 'stalled':
                        self.reverse()

        def set_target_volume(self, value):
                """ Set the target volume """
                self._write("MLT %f" % value)
                self._read_reply()


class Model44(object):
        prompts = {
                ':': 'stopped',
                '>': 'running',
                '<': 'reverse',
                '/': 'paused',
                '*': 'stopped',
                '^': 'wait', # dispense trigger wait
                }
        ranges = [ 'uL/min', 'mL/min', 'uL/hr' , 'mL/hr' ]

        def __init__(self, port=0):
                self.port = serial.Serial(port, baudrate=9600, stopbits=2)
                self.last_status = 'stopped'

        def _write(self, cmd):
                logging.debug('write: %s' % cmd)
                self.port.write("%s\r" % cmd)

        def _read_reply(self):
                s = self.port.read(1)
                if s != '\n':
                        raise RuntimeError('Expected LF, saw "%s"' % s.encode('string_escape'))
                
                reply = None
                prompt = None
                s = ''
                for i in range(50):
                        s += self.port.read(1)
                        if s[-1] == '\r':
                                reply = s
                        if len(s) >= 2 and s[-2].isdigit() and s[-1] in Model44.prompts:
                                prompt = Model44.prompts[s[-1]]
                                break

                logging.debug("read: %s" % s.encode('string_escape'))
                if prompt == None:
                        raise RuntimeError('Expected prompt, got "%s"' % s.encode('string_escape'))
                else:
                        self.last_status = prompt
                return reply

        def _read_value(self):
                s = self._read_reply()
                return float(s.strip())

        def _format_float(self, n):
                if n > 1e6: raise ArgumentError('Number too large')
                return ('%06f' % n)[:6]

        def get_status(self):
                """ Get status of pump """
                return self.last_status

        def set_diameter(self, value):
                """ Set diameter of syringe in millimeters """
                self._write("DIA " + self._format_float(value))
                return self._read_reply()

        def get_version(self):
                self._write('VER')
                version = self._read_reply()
                return version

        def __value_func(cmd):
                def f(self):
                        self._write(cmd)
                        return self._read_value()
                return f
        
        def get_flow_rate(self):
                units = { 'ml/mn': 'mL/min',
                          'ul/mn': 'mL/min',
                          'ml/hr': 'mL/hr',
                          'ul/hr': 'uL/hr',
                        }
                self._write('RAT')
                s = self._read_reply()
                value, unit = s.split()
                return float(value), units[unit]

        get_diameter = __value_func('DIA')
        get_target_volume = __value_func('TGT')
        get_volume_accum = __value_func('DEL')

        def __command_func(cmd):
                def f(self):
                        self._write(cmd)
                        self._read_reply()
                return f

        start = __command_func('RUN')
        stop = __command_func('STP')
        clear_volume_accum = __command_func('CLD')
        clear_target = __command_func('TGT 0')
        reverse = __command_func('DIR REV')

        def set_direction(self, dir):
                d = 'INF' if dir > 0 else 'REF'
                self._write('DIR %s' % d)
                self._read_reply()

        def set_flow_rate(self, value, range):
                """ Set flow rate in given range """
                ranges = {
                        'uL/min': 'UM',
                        'mL/min': 'MM',
                        'uL/hr' : 'UH',
                        'mL/hr' : 'MH' }
                
                if not ranges.has_key(range):
                        raise Exception("Invalid range")
                self._write("RAT %s %s" % (self._format_float(value), ranges[range]))
                self._read_reply()

        def set_target_volume(self, value):
                """ Set the target volume """
                self._write("TGT " + self._format_float(value))
                self._read_reply()

        def set_pump_mode(self):
                self._write('MOD PMP')
                self._read_reply()

        def set_volume_mode(self):
                self._write('MOD VOL')
                self._read_reply()

        def get_mode(self):
                self._write('MOD')
                mode = self._read_reply()
                return mode.lower().strip()
