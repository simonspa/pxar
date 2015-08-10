#!/usr/bin/env python2
"""
Simple Example Python Script Using the Pxar API.
"""


# ==============================================
# IMPORTS
# ==============================================
# region imports
from PyPxarCore import Pixel, PixelConfig, PyPxarCore, PyRegisterDictionary, PyProbeDictionary
from numpy import zeros
from pxar_helpers import *  # arity decorator, PxarStartup, PxarConfigFile, PxarParametersFile and others

# Try to import ROOT:
gui_available = True
try:
    import ROOT
except ImportError:
    gui_available = False
    pass
if gui_available:
    from ROOT import PyConfig
    PyConfig.IgnoreCommandLineOptions = True
    from pxar_gui import PxarGui
    from pxar_plotter import Plotter

import math
import cmd  # for command interface and parsing
import os   # for file system cmds
import sys
from time import time, sleep


# set up the DAC and probe dictionaries
dacdict = PyRegisterDictionary()
probedict = PyProbeDictionary()
# endregion


class PxarCoreCmd(cmd.Cmd):
    """Simple command processor for the pxar core API."""

    # ==============================================
    # GLOBAL FUNCTIONS
    # ==============================================
    # region Globals
    def __init__(self, api, gui, conf_dir):
        cmd.Cmd.__init__(self)
        self.fullOutput = False
        self.prompt = "pxarCore =>> "
        self.intro = "Welcome to the pxar core console!"  # defaults to None
        self.api = api
        self.dir = conf_dir
        self.window = None
        if gui and gui_available:
            self.window = PxarGui(ROOT.gClient.GetRoot(), 800, 800)
        elif gui and not gui_available:
            print "No GUI available (missing ROOT library)"

    def plot_eventdisplay(self, data):
        pixels = list()
        # Multiple events:
        if isinstance(data, list):
            if not self.window:
                for evt in data:
                    print evt
                return
            for evt in data:
                for px in evt.pixels:
                    pixels.append(px)
        else:
            if not self.window:
                print data
                return
            for px in data.pixels:
                pixels.append(px)
        self.plot_map(pixels, 'Event Display', True)

    def plot_map(self, data, name, count=False):
        if not self.window:
            print data
            return

        # Find number of ROCs present:
        module = False
        for px in data:
            if px.roc > 0:
                module = True
                break
        # Prepare new numpy matrix:
        d = zeros((417 if module else 53, 161 if module else 81))
        for px in data:
            xoffset = 52 * (px.roc % 8) if module else 0
            yoffset = 80 * int(px.roc / 8) if module else 0
            # Flip the ROCs upside down:
            y = (px.row + yoffset) if (px.roc < 8) else (2 * yoffset - px.row - 1)
            # Reverse order of the upper ROC row:
            x = (px.column + xoffset) if (px.roc < 8) else (415 - xoffset - px.column)
            d[x + 1][y + 1] += 1 if count else px.value

        plot = Plotter.create_th2(d, 0, 417 if module else 53, 0, 161 if module else 81, name, 'pixels x', 'pixels y',
                                  name)
        self.window.histos.append(plot)
        self.window.update()

    def plot_1d(self, data, name, dacname, min_val, max_val):
        if not self.window:
            print_data(self.fullOutput, data, (max_val - min_val) / len(data))
            return

        # Prepare new numpy matrix:
        d = zeros(len(data))
        for idac, dac in enumerate(data):
            if dac:
                d[idac] = dac[0].value

        plot = Plotter.create_th1(d, min_val, max_val, name, dacname, name)
        self.window.histos.append(plot)
        self.window.update()

    def plot_2d(self, data, name, dac1, step1, min1, max1, dac2, step2, min2, max2):
        if not self.window:
            for idac, dac in enumerate(data):
                dac1 = min1 + (idac / ((max2 - min2) / step2 + 1)) * step1
                dac2 = min2 + (idac % ((max2 - min2) / step2 + 1)) * step2
                s = "DACs " + str(dac1) + ":" + str(dac2) + " - "
                for px in dac:
                    s += str(px)
                print s
            return

        # Prepare new numpy matrix:
        bins1 = (max1 - min1) / step1 + 1
        bins2 = (max2 - min2) / step2 + 1
        d = zeros((bins1, bins2))

        for idac, dac in enumerate(data):
            if dac:
                bin1 = (idac / ((max2 - min2) / step2 + 1))
                bin2 = (idac % ((max2 - min2) / step2 + 1))
                d[bin1][bin2] = dac[0].value

        plot = Plotter.create_th2(d, min1, max1, min2, max2, name, dac1, dac2, name)
        self.window.histos.append(plot)
        self.window.update()

    def do_gui(self):
        """Open the ROOT results browser"""
        if not gui_available:
            print "No GUI available (missing ROOT library)"
            return
        if self.window:
            return
        self.window = PxarGui(ROOT.gClient.GetRoot(), 800, 800)

    def daq_converted_raw(self, verbose=False):
        self.api.daqStart()
        self.api.daqTrigger(1, 500)
        event = self.converted_raw_event(verbose)
        self.api.daqStop()
        return event

    def converted_raw_event(self, verbose=False):
        event = []
        try:
            event = self.api.daqGetRawEvent()
        except RuntimeError:
            pass
        if verbose:
            print "raw Event:\t\t", event
        count = 0
        for i in event:
            i &= 0x0fff
            if i & 0x0800:
                i -= 4096
            event[count] = i
            count += 1
        if verbose:
            print "converted Event:\t", event
        return event

    def translate_levels(self):
        event = self.converted_raw_event()
        rocs = 0
        for i in event:
            if i < event[0] * 3 / 4:
                rocs += 1
        hits = (len(event) - rocs * 3) / 6
        if hits == 0:
            print 'there was not a single pixel hit'
        addresses = []
        for hit in range(hits):
            levels = []
            for level in range(3, 8):
                y = self.translate_level(event[level + 6 * hit], event)
                levels.append(y)
            addresses.append(self.get_addresses(levels))
            addresses[hit].append(event[8 + 6 * hit])
            print 'Hit:', "{0:2d}".format(hit), addresses[hit]
        return addresses

    def get_levels(self, convert_header=False):
        event = self.converted_raw_event()
        if len(event) == 0:
            raise Exception('Empty Event: %s'%event)
        rocs = 0
        ub = event[0]
        for i in event:
            if i < ub * 3 / 4:
                rocs += 1
        hits = (len(event) - rocs * 3) / 6
        for hit in range(hits):
            for level in range(3, 8):
                event[level + 6 * hit] = self.translate_level(event[level + 6 * hit], event)
        for i in range(len(event)):
            if convert_header and event[i] < ub * 3 / 4:
                event[i], event[i + 1] = self.translate_level(event[i], event, i), self.translate_level(event[i + 1], event, i)
        return event

    def address_level_scan(self):
        self.api.daqStart()
        self.api.daqTrigger(1000, 500)  # choose here how many triggers you want to send (crucial for the time it takes)
        plotdata = zeros(1024)
        try:

            while True:
                pos = -3
                dat = self.api.daqGetRawEvent()
                for i in dat:
                    # REMOVE HEADER
                    i &= 0x0fff
                    # Remove PH from hits:
                    if pos == 5:
                        pos = 0
                        continue
                    # convert negatives
                    if i & 0x0800:
                        i -= 4096
                    plotdata[500 + i] += 1
                    pos += 1
        except RuntimeError:
            pass
        self.api.daqStop()
        return plotdata

    def set_clock(self, value):
        # sets all the delays to the right value if you want to change clk
        self.api.setTestboardDelays({"clk": value})
        self.api.setTestboardDelays({"ctr": value})
        self.api.setTestboardDelays({"sda": value + 11})
        self.api.setTestboardDelays({"tin": value + 2})

    def get_address_levels(self):
        event = self.daq_converted_raw(verbose=False)
        length = len(event)
        n_events = (length - 3) / 6  # number of single events
        addresses = []
        for i in range(5 * n_events):  # fill the list with an many zero as we got addresslevels
            addresses.append(0)
        pos = 0
        address_index = 0
        for eventIndex in range(5 * n_events + n_events):
            if pos == 5:
                pos = 0
                continue
            addresses[address_index] = int(round(float(event[3 + eventIndex]) / 50, 0))
            address_index += 1
            pos += 1
        return addresses

    def get_averaged_level(self, it):
        levels = [0, 0, 0, 0, 0]
        header = [0, 0]
        self.api.daqStart()
        self.api.daqTrigger(30, 500)
        data = []
        for i in range(it):
            data = self.converted_raw_event()
            if len(data) == 3:
                for j in range(2):
                    header[j] += data[j]
            elif len(data) == 9:
                for j in range(5):
                    levels[j] += data[j + 3]
        if len(data) == 3:
            for j in range(2):
                header[j] = round(header[j] / float(it), 1)
            print header
        elif len(data) == 9:
            for j in range(5):
                levels[j] = round(levels[j] / float(it), 1)
            print levels
        self.api.daqStop()

    def rate(self, duration):
        self.api.daqStart()
        t = time()
        t1 = 0
        all_trig = 0
        while t1 < duration:
            trig_time = time()
            triggers = 0
            while triggers < 5:
                try:
                    self.api.daqGetEvent()
                    triggers += 1
                    all_trig += 1
                except RuntimeError:
                    pass
            print '\r{0:02.2f}'.format(triggers / (time() - trig_time)),
            sys.stdout.flush()
            t1 = time() - t
        print "complete rate", '{0:02.2f}'.format(all_trig / (time() - t))
        # print time.time()-t
        self.api.daqStop()

    def enable_pix(self, row=5, col=12, roc=0):
        self.api.testAllPixels(0, roc)
        self.api.maskAllPixels(1, roc)
        self.api.testPixel(row, col, 1, roc)
        self.api.maskPixel(row, col, 0, roc)

    @staticmethod
    def translate_level(level, event, roc=0):
        offset = 7
        y = level - event[roc + 1]
        y += (event[roc + 1] - event[roc + 0] + offset) / 8
        y /= (event[roc + 1] - event[roc + 0] + offset) / 4
        return y + 1

    @staticmethod
    def get_addresses(levels):
        col = levels[0] * 12 + levels[1] * 2 + levels[4] % 2
        row = 80 - (levels[2] * 18 + levels[3] * 3 + levels[4] / 2)
        return [col, row]

    @staticmethod
    def elapsed_time(start):
        print 'elapsed time:', '{0:0.2f}'.format(time() - start), 'seconds'

    @staticmethod
    def code_event(row, col, number):
        vec = []
        for i in range(27):
            vec.append(0)

        # number convertion
        pos = 0
        for i in range(9):
            if number % pow(2, i + 1) != 0:
                number -= pow(2, i)
                vec[-pos - 1] = 1
            if pos == 3:
                pos += 1
            pos += 1

        # row convertion
        row = (80 - row) * 2
        row1 = row % 6
        row2 = (row - row1) % 36
        row3 = row - row1 - row2
        for i in range(3):
            if row1 % pow(2, i + 1) != 0:
                row1 -= pow(2, i)
                vec[-i - 10] = 1
        for i in range(3):
            if row2 % (6 * pow(2, i + 1)) != 0:
                row2 -= 6 * pow(2, i)
                vec[-i - 13] = 1
        for i in range(3):
            if row3 % (36 * pow(2, i + 1)) != 0:
                row3 -= 36 * pow(2, i)
                vec[-i - 16] = 1

        # column convertion
        if col % 2 != 0:
            vec[-10] = 1
            col -= 1
        col1 = col % 12
        col2 = col - col1
        for i in range(3):
            if col1 % (2 * pow(2, i + 1)) != 0:
                col1 -= 2 * pow(2, i)
                vec[-i - 19] = 1
        for i in range(3):
            if col2 % (12 * pow(2, i + 1)) != 0:
                col2 -= 12 * pow(2, i)
                vec[-i - 22] = 1

        # create decimal number
        dec = 0
        length = len(vec)
        for i in vec:
            dec += int(i) * pow(2, length - 1)
            length -= 1
        return dec
    # endregion

    # ==============================================
    # CMD LINE INTERFACE FUNCTIONS
    # ==============================================
    # region interface functions
    @arity(0, 0, [])
    def do_getTBia(self):
        """getTBia: returns analog DTB current"""
        print "Analog Current: ", (self.api.getTBia() * 1000), " mA"

    def complete_getTBia(self):
        # return help for the cmd
        return [self.do_getTBia.__doc__, '']

    @arity(0, 0, [])
    def do_getTBid(self):
        """getTBia: returns analog DTB current"""
        print "Digital Current: ", (self.api.getTBid() * 1000), " mA"

    def complete_getTBid(self):
        # return help for the cmd
        return [self.do_getTBid.__doc__, '']

    @arity(0,1,[int])
    def do_setExternalClock(self, enable=1):
        """setExternalClock [enable]: enables the external DTB clock input, switches off the internal clock. Only switches if external clock is present."""
        if self.api.setExternalClock(enable) is True:
            print "Switched to " + ("external" if enable else "internal") + " clock."
        else:
            print "Could not switch to " + ("external" if enable else "internal") + " clock!"

    def complete_setExternalClock(self):
        # return help for the cmd
        return [self.do_setExternalClock.__doc__, '']

    @arity(2, 2, [str, str])
    def do_SignalProbe(self, probe, name):
        """SignalProbe [probe] [name]: Switches DTB probe output [probe] to signal [name]"""
        self.api.SignalProbe(probe, name)

    def complete_SignalProbe(self, text, line, start_index, end_index):
        probes = ["d1", "d2", "a1", "a2"]
        if len(line.split(" ")) <= 2:  # first argument
            if text:  # started to type
                # list matching entries
                return [pr for pr in probes
                        if pr.startswith(text)]
            else:
                # list all probes
                return probes
        elif len(line.split(" ")) <= 3:  # second argument
            p = "".join(line.split(" ")[1:2])
            if text:  # started to type
                if p.startswith("a"):
                    return [pr for pr in probedict.getAllAnalogNames()
                            if pr.startswith(text)]
                elif p.startswith("d"):
                    return [pr for pr in probedict.getAllDigitalNames()
                            if pr.startswith(text)]
                else:
                    return [self.do_SignalProbe.__doc__, '']
            else:
                # return all signals:
                if p.startswith("a"):
                    return probedict.getAllAnalogNames()
                elif p.startswith("d"):
                    return probedict.getAllDigitalNames()
                else:
                    return [self.do_SignalProbe.__doc__, '']
        else:
            # return help for the cmd
            return [self.do_SignalProbe.__doc__, '']

    @arity(2, 3, [str, int, int])
    def do_setDAC(self, dacname, value, rocID=None):
        """setDAC [DAC name] [value] [ROCID]: Set the DAC to given value for given roc ID"""
        self.api.setDAC(dacname, value, rocID)

    def complete_setDAC(self, text, line, start_index, end_index):
        if text and len(line.split(" ")) <= 2:  # first argument and started to type
            # list matching entries
            return [dac for dac in dacdict.getAllROCNames()
                    if dac.startswith(text)]
        else:
            if len(line.split(" ")) > 2:
                # return help for the cmd
                return [self.do_setDAC.__doc__, '']
            else:
                # return all DACS
                return dacdict.getAllROCNames()

    @arity(1, 1, [str])
    def do_run(self, filename):
        """run [filename]: loads a list of commands to be executed on the pxar cmdline"""
        try:
            f = open(filename)
        except IOError:
            print "Error: cannot open file '" + filename + "'"
        try:
            for line in f:
                if not line.startswith("#") and not line.isspace():
                    print line.replace('\n', ' ').replace('\r', '')
                    self.onecmd(line)
        finally:
            f.close()

    def complete_run(self, text, line, start_index, end_index):
        # tab-completion for the file path:
        try:
            # remove specific delimeters from the readline parser
            # to allow completion of filenames with dashes
            import readline

            delims = readline.get_completer_delims()
            delims = delims.replace('-', '')
            readline.set_completer_delims(delims)
        except ImportError:
            pass
        return get_possible_filename_completions(extract_full_argument(line, end_index))

    @arity(0, 0, [])
    def do_daqStart(self):
        """daqStart: starts a new DAQ session"""
        self.api.daqStart()

    def complete_daqStart(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_daqStart.__doc__, '']

    @arity(0, 0, [])
    def do_daqStop(self):
        """daqStop: stops the running DAQ session"""
        self.api.daqStop()

    def complete_daqStop(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_daqStop.__doc__, '']

    @arity(0, 2, [int, int])
    def do_daqTrigger(self, ntrig=5, period=500):
        """daqTrigger [ntrig] [period = 0]: sends ntrig patterns to the device"""
        self.api.daqTrigger(ntrig, period)

    def complete_daqTrigger(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_daqTrigger.__doc__, '']

    @arity(3, 4, [int, int, int, int])
    def do_testPixel(self, col, row, enable, rocid=None):
        """testPixel [column] [row] [enable] [ROC id]: enable/disable testing of pixel"""
        self.api.testPixel(col, row, enable, rocid)

    def complete_testPixel(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_testPixel.__doc__, '']

    @arity(1, 2, [int, int])
    def do_testAllPixels(self, enable, rocid=None):
        """testAllPixels [enable] [rocid]: enable/disable tesing for all pixels on given ROC"""
        self.api.testAllPixels(enable, rocid)

    def complete_testAllPixels(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_testAllPixels.__doc__, '']

    @arity(3, 4, [int, int, int, int])
    def do_maskPixel(self, col, row, enable, rocid=None):
        """maskPixel [column] [row] [enable] [ROC id]: mask/unmask pixel"""
        self.api.maskPixel(col, row, enable, rocid)

    def complete_maskPixel(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_maskPixel.__doc__, '']

    @arity(1, 2, [int, int])
    def do_maskAllPixels(self, enable, rocid=None):
        """maskAllPixels [enable] [rocid]: mask/unmask all pixels on given ROC"""
        self.api.maskAllPixels(enable, rocid)

    def complete_maskAllPixels(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_maskAllPixels.__doc__, '']

    @arity(0, 2, [int, int])
    def do_getEfficiencyMap(self, flags=0, nTriggers=10):
        """getEfficiencyMap [flags = 0] [nTriggers = 10]: returns the efficiency map"""
        self.window = PxarGui(ROOT.gClient.GetRoot(), 1000, 800)
        data = self.api.getEfficiencyMap(flags, nTriggers)
        self.plot_map(data, "Efficiency")

    def complete_getEfficiencyMap(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_getEfficiencyMap.__doc__, '']

    @arity(0, 6, [str, int, int, int, int, int])
    def do_getPulseheightVsDAC(self, dacname="vcal", dacstep=1, dacmin=0, dacmax=255, flags=0, nTriggers=10):
        """getPulseheightVsDAC [DAC name] [step size] [min] [max] [flags = 0] [nTriggers = 10]: returns the pulseheight over a 1D DAC scan"""
        data = self.api.getPulseheightVsDAC(dacname, dacstep, dacmin, dacmax, flags, nTriggers)
        self.plot_1d(data, "Pulseheight", dacname, dacmin, dacmax)

    def complete_getPulseheightVsDAC(self, text, line, start_index, end_index):
        if text and len(line.split(" ")) <= 2:  # first argument and started to type
            # list matching entries
            return [dac for dac in dacdict.getAllROCNames()
                    if dac.startswith(text)]
        else:
            if len(line.split(" ")) > 2:
                # return help for the cmd
                return [self.do_getPulseheightVsDAC.__doc__, '']
            else:
                # return all DACS
                return dacdict.getAllROCNames()

    @arity(0, 10, [str, int, int, int, str, int, int, int, int, int])
    def do_dacDacScan(self, dac1name="caldel", dac1step=1, dac1min=0, dac1max=255, dac2name="vthrcomp", dac2step=1,
                      dac2min=0, dac2max=255, flags=0, nTriggers=10):
        """getEfficiencyVsDACDAC [DAC1 name] [step size 1] [min 1] [max 1] [DAC2 name] [step size 2] [min 2] [max 2] [flags = 0] [nTriggers = 10]: returns the efficiency over a 2D DAC1-DAC2 scan"""
        self.window = PxarGui(ROOT.gClient.GetRoot(), 1000, 800)
        self.api.testAllPixels(0)
        self.api.testPixel(14, 14, 1)
        data = self.api.getEfficiencyVsDACDAC(dac1name, dac1step, dac1min, dac1max, dac2name, dac2step, dac2min,
                                              dac2max, flags, nTriggers)
        self.plot_2d(data, "DacDacScan", dac1name, dac1step, dac1min, dac1max, dac2name, dac2step, dac2min, dac2max)

    def complete_dacDacScan(self, text, line, start_index, end_index):
        if text and len(line.split(" ")) <= 2:  # first argument and started to type
            # list matching entries
            return [dac for dac in dacdict.getAllROCNames()
                    if dac.startswith(text)]
        elif text and len(line.split(" ")) == 6:
            # list matching entries
            return [dac for dac in dacdict.getAllROCNames()
                    if dac.startswith(text)]
        else:
            if (len(line.split(" ")) > 2 and len(line.split(" ")) < 6) or len(line.split(" ")) > 6:
                # return help for the cmd
                return [self.do_dacDacScan.__doc__, '']
            else:
                # return all DACS
                return dacdict.getAllROCNames()

    @arity(0, 0, [])
    def do_HVon(self):
        """HVon: switch High voltage for sensor bias on"""
        self.api.HVon()

    def complete_HVon(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_HVon.__doc__, '']

    @arity(0, 0, [])
    def do_HVoff(self):
        """HVoff: switch High voltage for sensor bias off"""
        self.api.HVoff()

    def complete_HVoff(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_HVoff.__doc__, '']

    @arity(1, 1, [str])
    def do_daqTriggerSource(self, source):
        """daqTriggerSource: select the trigger source to be used for the DAQ session"""
        if self.api.daqTriggerSource(source):
            print "Trigger source \"" + source + "\" selected."
        else:
            print "DAQ returns faulty state."

    def complete_daqTriggerSource(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_daqTriggerSource.__doc__, '']

    @arity(0, 1, [int])
    def do_daqGetEvent(self, convert=1):
        """daqGetEvent [convert]: read one converted event from the event buffer, for convert = 0 it will print the addresslevels"""
        try:
            data = self.api.daqGetEvent()
            print data
        except RuntimeError:
            pass

    def complete_daqGetEvent(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_daqGetRawEvent.__doc__, '']

    @arity(0, 1, [int])
    def do_daqGetRawEvent(self, convert=1):
        """daqGetRawEvent [convert]: read one converted event from the event buffer, for convert = 0 it will print the addresslevels"""
        if convert == 1:
            data = self.converted_raw_event()
            print data
        elif convert == 2:
            data = self.get_levels(True)
            print data
        elif convert == 0:
            data = self.api.daqGetRawEvent()
            print data
        elif convert == 3:
            data = self.converted_raw_event()
            print "UB", data[0], "\tlength", len(data)

    def complete_daqGetRawEvent(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_daqGetRawEvent.__doc__, '']

    @arity(0, 0, [])
    def do_daqGetEventBuffer(self):
        """daqGetEventBuffer: read all decoded events from the DTB buffer"""
        data = []
        try:
            data = self.api.daqGetEventBuffer()
            print data[0]
            for i in data:
                print i
                # self.plot_eventdisplay(data)
        except RuntimeError:
            pass

    def complete_daqGetEventBuffer(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_daqGetEventBuffer.__doc__, '']

    @arity(0, 0, [])
    def do_daqStatus(self):
        """daqStatus: reports status of the running DAQ session"""
        if self.api.daqStatus():
            print "DAQ session is fine"
        else:
            print "DAQ session returns faulty state"

    def complete_daqStatus(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_daqStatus.__doc__, '']
    # endregion

    # ==============================================
    # ADDITIONAL TEST FUNCTIONS FOR CLI
    # ==============================================

    # ==============================================
    # region Test Board Delays
    @arity(2, 2, [str, int])
    def do_set_tb_delay(self, dacname, value):
        """setTBdelays [delay] [value]: sets a single test board delay to a certain value"""
        print "set TB DACs: ", dacname, value
        self.api.setTestboardDelays({dacname: value})

    def complete_set_tb_delay(self):
        # return help for the cmd
        return [self.do_set_tb_delay.__doc__, '']

    @arity(0, 2, [int, int])
    def do_set_tin_tout(self, tin=14, tout=8):
        """setTinTout [tin] [tout]: sets tindelay to value tin and toutdelay to tout"""
        print "set tindelay to: ", tin
        print "set toutdelay to: ", tout
        self.api.setTestboardDelays({"tindelay": tin, "toutdelay": tout})

    def complete_set_tin_tout(self):
        # return help for the cmd
        return [self.do_set_tin_tout.__doc__, '']

    @arity(1, 1, [int])
    def do_set_clock_delays(self, value):
        """SetClockDelays [value of clk and ctr]: sets the two TB delays clk and ctr """
        print "TB delays clk and ctr set to: ", value
        self.set_clock(value)

    def complete_set_clock_delays(self):
        # return help for the cmd
        return [self.do_set_clock_delays.__doc__, '']

    @arity(0, 2, [int, int])
    def do_find_clk_delay(self, n_rocs=1, min_val=0, max_val=25):
        """find the best clock delay setting """
        # variable declarations
        cols = [0, 2, 4, 6, 8, 10]
        rows = [44, 41, 38, 35, 32, 29]  # special pixel setting for splitting
        n_triggers = 100
        n_levels = len(cols)
        clk_x = []
        levels_y = []
        mean_value = []
        spread_black = []
        header = [0, 0]

        # find the address levels
        print "get level splitting: "
        for roc in range(n_rocs):
            self.api.maskAllPixels(1, roc)
            self.api.testAllPixels(0, roc)
            levels_y.append([])
            mean_value.append([])
            spread_black.append([])
            for i in range(len(cols)):
                levels_y[roc].append([])
                mean_value[roc].append(0)
                self.api.testPixel(cols[i], rows[i], 1, roc)
                self.api.maskPixel(cols[i], rows[i], 0, roc)
            # active pixel for black level spread
            self.api.testPixel(15, 59, 1, roc)
            self.api.maskPixel(15, 59, 0, roc)

            for clk in range(min_val, max_val):
                # clear mean values
                for i in range(n_levels):
                    mean_value[roc][i] = 0
                if not roc:
                    clk_x.append(clk)
                self.set_clock(clk)
                self.api.daqStart()
                self.api.daqTrigger(n_triggers, 500)
                sum_spread = 0
                for k in range(n_triggers):
                    event = self.converted_raw_event()
                    # black level spread
                    spread_j = 0
                    for j in range(5):
                        try:
                            spread_j += abs(event[1 + roc * 3] - event[3 + roc * 3 + n_levels * 6 + j])
                        except IndexError:
                            spread_j = 99
                            break
                    sum_spread += spread_j / 5
                    # level split
                    stop_loop = False
                    for j in range(len(cols)):
                        try:
                            mean_value[roc][j] += event[5 + roc * 3 + j * 6]
                        except IndexError:
                            mean_value[roc][j] = 0
                            stop_loop = True
                            break
                    if stop_loop:
                        break
                spread_black[roc].append(sum_spread / float(n_triggers))
                for i in range(n_levels):
                    levels_y[roc][i].append(mean_value[roc][i] / float(n_triggers))
                print '\rclk-delay:', "{0:2d}".format(clk), 'black lvl spread: ', "{0:2.2f}".format(
                    spread_black[roc][clk]),
                sys.stdout.flush()
                self.api.daqStop()
            self.api.maskAllPixels(1, roc)
            self.api.testAllPixels(0, roc)
        print

        # find the best phase
        spread = []
        for i in range(len(levels_y[0][0])):
            sum_level = 0
            sum_spread = 0
            for j in range(n_levels):
                sum_level += levels_y[0][j][i]
            for j in range(n_levels):
                if levels_y[0][j][i] != 0:
                    sum_spread += abs(sum_level / n_levels - levels_y[0][j][i])
                else:
                    sum_spread = 99 * n_levels
                    break
            spread.append(sum_spread / n_levels)
        best_clk = 99
        min_spread = 99
        for i in range(len(spread)):
            if spread[i] < min_spread:
                min_spread = spread[i]
                best_clk = clk_x[i]
        print
        print 'best clk: ', best_clk
        print 'black level spread: ', best_clk, spread_black[0][best_clk], best_clk + 1, spread_black[0][best_clk + 1],
        print best_clk - 1, spread_black[0][best_clk - 1]
        self.set_clock(best_clk)

        # get an averaged header for the lvl margins
        self.api.daqStart()
        self.api.daqTrigger(n_triggers, 500)
        for i in range(n_triggers):
            event = self.converted_raw_event()
            header[0] += event[0]
            header[1] += event[1]
        self.api.daqStop()
        header[0] /= n_triggers
        header[1] /= n_triggers

        # save the data to file (optional)
        f = open('levels_header.txt', 'w')
        f.write(str(header[0]) + "\n" + str(header[1]))
        f.close()
        file_name = []
        for i_roc in range(n_rocs):
            file_name.append('levels_roc' + str(i_roc) + '.txt')
            f = open(file_name[i_roc], 'w')
            for i in range(n_levels):
                for j in levels_y[i_roc][i]:
                    f.write(str(j) + ' ')
                f.write("\n")
            for i in clk_x:
                f.write(str(i) + ' ')
            f.close()
        print 'saved the levels to file(s)'
        for name in file_name:
            print name

        # plot address levels
        self.enable_pix(5, 12)
        self.window = PxarGui(ROOT.gClient.GetRoot(), 800, 800)
        plotdata = self.address_level_scan()
        plot = Plotter.create_th1(plotdata, -512, +512, "Address Levels", "ADC", "#")
        self.window.histos.append(plot)
        self.window.update()

    def complete_find_clk_delay(self):
        # return help for the cmd
        return [self.do_find_clk_delay.__doc__, '']

    @arity(0, 2, [int, int])
    def do_vary_clk(self, min_val=0, max_val=25):
        """varies the clk settings and all other correlated delays accordingly"""
        self.enable_pix(5, 12)
        for clk in range(min_val, max_val):
            self.set_clock(clk)
            self.api.daqStart()
            self.api.daqTrigger(1, 500)
            event = self.converted_raw_event()
            print clk, event
            self.api.daqStop()
        print

    def complete_vary_clk(self):
        # return help for the cmd
        return [self.do_vary_clk.__doc__, '']

    @arity(0, 3, [str, int, int])
    def do_scan_tb_delay(self, delay="all", min_val=0, max_val=20):
        """vary_tb_delay [delay] [min] [max]: scans one test board delay and leaves the others constant"""
        self.enable_pix(5, 12)
        for value in range(min_val, max_val):
            if delay == 'all':
                self.set_clock(value)
            else:
                self.api.setTestboardDelays({delay: value})
            self.api.daqStart()
            self.api.daqTrigger(1, 500)
            sleep(0.1)
            event = self.converted_raw_event()
            print value, event
            self.api.daqStop()

    def complete_scan_tb_delay(self):
        # return help for the cmd
        return [self.do_scan_tb_delay.__doc__, '']
    # endregion

    # ==============================================
    # region Read Out
    @arity(0, 0)
    def do_get_event(self):
        """get_event: plot the hits"""
        self.translate_levels()

    @arity(0, 0)
    def do_daqRawEvent(self):
        """analogLevelScan: plots the raw and converted event"""
        self.api.daqStart()
        self.api.daqTrigger(1, 500)
        rawEvent = []
        try:
            rawEvent = self.api.daqGetRawEvent()
        except RuntimeError:
            pass
        print "raw Event:\t\t", "[",
        for event in rawEvent:
            print '{0:5d}'.format(event),
        print "]"
        nCount = 0
        for i in rawEvent:
            i = i & 0x0fff
            if i & 0x0800:
                i -= 4096
            rawEvent[nCount] = i
            nCount += 1
        print "converted Event:\t", "[",
        for event in rawEvent:
            print '{0:5d}'.format(event),
        print "]"
        self.api.daqStop()

    def complete_daqRawEvent(self):
        # return help for the cmd
        return [self.do_daqRawEvent.__doc__, '']

    @arity(0, 0, [])
    def do_daqEvent(self):
        """analogLevelScan: plots the event"""
        self.api.daqStart()
        self.api.daqTrigger(1, 500)
        data = []
        try:
            data = self.api.daqGetEvent()
        except RuntimeError:
            pass
        print len(data)
        if len(data.pixels) == 0:
            print "[]"
        else:
            for event in data.pixels:
                print event
        self.api.daqStop()

    def complete_daqEvent(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_daqEvent.__doc__, '']
    # endregion

    # ==============================================
    # region Miscellaneous
    @arity(0, 0, [])
    def do_analogLevelScan(self):
        """analogLevelScan: scan the ADC levels of an analog ROC\nTo see all six address levels it is sufficient to activate Pixel 5 12"""
        self.window = PxarGui(ROOT.gClient.GetRoot(), 800, 800)
        plotdata = self.address_level_scan()
        x = 0
        for i in range(1024):
            if plotdata[i] != 0:
                if i - x != 1:
                    print "\n"
                print i - 500, " ", plotdata[i]
                x = i
        print '[',
        for i in range(1024):
            print '%d,' % plotdata[i],
        print ']'
        plot = Plotter.create_th1(plotdata, -512, +512, "Address Levels", "ADC", "#")
        self.window.histos.append(plot)
        self.window.update()

    def complete_analogLevelScan(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_analogLevelScan.__doc__, '']

    @arity(0, 0, [])
    def do_enableAllPixel(self):
        """enableAllPixel: enables and unmasks all Pixels"""
        self.api.maskAllPixels(0)
        self.api.testAllPixels(1)

    def complete_enableAllPixel(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_enableAllPixel.__doc__, '']

    @arity(0, 3, [int, int, int])
    def do_enableOnePixel(self, row=14, column=14, roc=0):
        """enableOnePixel [row] [column] : enables one Pixel (default 14/14); masks and disables the rest"""
        self.api.testAllPixels(0, roc)
        self.api.maskAllPixels(1, roc)
        print "--> disable and mask all Pixels (" + str(self.api.getNEnabledPixels(0)) + ", " + str(
            self.api.getNMaskedPixels(0)) + ")"
        self.api.testPixel(row, column, 1, roc)
        self.api.maskPixel(row, column, 0, roc)
        print "--> enable and unmask Pixel " + str(row) + "/" + str(column) + " (" + str(
            self.api.getNEnabledPixels(0)) + ", " + str(self.api.getNMaskedPixels(0)) + ")"

    def complete_enableOnePixel(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_enableOnePixel.__doc__, '']

    @arity(1, 3, [int, int, int])
    def do_xEnableBlock(self, blocksize, row=3, col=3):
        """xEnableBlock [blocksize] [row] [col] : masks all Pixel; starting from row and col (default 3/3) unmasks block of size blocksize  """
        self.api.maskAllPixels(1)
        print "--> all Pixels masked (" + str(self.api.getNMaskedPixels(0)) + ")"
        for i in range(3, blocksize + 3):
            for j in range(3, blocksize + 3):
                self.api.maskPixel(i, j, 0)
        print "--> unmask Block 3/3 to " + str(blocksize + 3) + "/" + str(blocksize + 3) + " (" + str(
            self.api.getNMaskedPixels(0)) + " Pixel)"

    def complete_xEnableBlock(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_xEnableBlock.__doc__, '']

    @arity(2, 2, [int, int])
    def do_enablePixel(self, row, column):
        """enablePixel [row] [column] : enables and unmasks a Pixel """
        self.api.testPixel(row, column, 1)
        self.api.maskPixel(row, column, 0)
        print "--> enable and unmask Pixel " + str(row) + "/" + str(column) + " (" + str(
            self.api.getNEnabledPixels(0)) + ", " + str(self.api.getNMaskedPixels(0)) + ")"

    def complete_enablePixel(self):
        # return help for the cmd
        return [self.do_enablePixel.__doc__, '']

    @arity(1, 6, [int, int, int, int, int, int])
    def do_enableRow(self, row, start=0, stop=51, maxrow=0, step_col=1, step_row=1):
        """enableRow [row1] [col1] [col2] [row2] [stepcol] [steprow] : enables and unmasks a row from start to stop  """
        if maxrow == 0:
            maxrow = row
        for rows in range(row, maxrow + 1, step_row):
            for col in range(start, stop + 1, step_col):
                self.api.testPixel(col, rows, 1)
                self.api.maskPixel(col, rows, 0)
        print "--> enable and unmask row", row, "from col", start, "to", stop, '(' + str(
            self.api.getNEnabledPixels(0)) + ", " + str(self.api.getNMaskedPixels(0)) + ")"

    def complete_enableRow(self):
        # return help for the cmd
        return [self.do_enableRow.__doc__, '']

    @arity(0, 0, [])
    def do_PixelActive(self):
        """PixelActive : shows how many Pixels are acitve and how many masked"""
        if self.api.getNEnabledPixels() == 1:
            print "1", "\tPixel active"
        else:
            print self.api.getNEnabledPixels(), "\tPixels active"
        print self.api.getNMaskedPixels(), "\tPixels masked"

    def complete_PixelActive(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_PixelActive.__doc__, '']

    @arity(0, 0, [])
    def do_findAnalogueTBDelays(self):
        """findAnalogueTBDelays: configures tindelay and toutdelay"""
        best_tin = 10    # default value if algorithm should fail
        best_tout = 20   # default value if algorithm should fail

        # find tindelay
        print "\nscan tindelay:\ntindelay\ttoutdelay\trawEvent[0]"
        for tin in range(5, 20):
            self.api.setTestboardDelays({"tindelay": tin, "toutdelay": 20})
            event = self.daq_converted_raw()
            print str(tin) + "\t\t20\t\t" + str(event[0])
            if (event[0] < -100):  # triggers for UB, the first one should always be UB
                best_tin = tin
                break

        # find toutdelay
        print "\nscan toutdelay:\ntindelay\ttoutdelay\trawEvent[-1]"
        for i in range(20,-1,-1):
            self.api.setTestboardDelays({"tindelay": best_tin, "toutdelay": i})
            event = self.daq_converted_raw()
            print str(best_tin) + "\t\t" + str(i) + "\t\t" + str(event[-1])
            if event[-1] > 20:  # triggers for PH, the last one should always be a pos PH
                best_tout = i
                break

        print "set tindelay to:  ", best_tin
        print "set toutdelay to: ", best_tout

    def complete_FindTBDelays(self):
        # return help for the cmd
        return [self.do_findAnalogueTBDelays.__doc__, '']

    @arity(0, 2, [int, int])
    def do_findDelays(self, start=10, end=16):
        """findDelays: configures tindelay and toutdelay"""
        self.api.setDAC("wbc", 114)
        self.api.daqTriggerSource("extern")
        for tin in range(start, end):
            self.api.setTestboardDelays({"tindelay": 14, "toutdelay": tin})
            self.api.daqStart()
            sleep(0.1)
            print tin,
            try:
                data = self.get_levels()
            except:
                print 'Cannot read data'
                continue
            
            print len(data), data
            self.api.daqStop()

    def complete_findDelays(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_findDelays.__doc__, '']

    @arity(0, 2, [int, int])
    def do_scanVana(self, begin=110, end=160):
        """ScanVana: finds the best setting for vana so that the analogue current is nearly 24"""
        for vana in range(begin, end):
            self.api.setDAC("vana", vana)
            sleep(0.4)
            current = self.api.getTBia() * 1000
            print vana, current
            if (current < 24.5 and current > 23.5):
                break
        print "\nset vana to ", vana

    def complete_scanVana(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_scanVana.__doc__, '']

    @arity(2, 2, [int, int])
    def do_varyClk(self, start, end):
        """varyClk [start] [end]: plots addresslevelscans for clk delay settings between [start] and [end] and varies all other delays accordingly"""
        self.enable_pix(5, 12)
        for value in range(start, end + 1):
            print "prints the histo for clk = " + str(value) + "..."
            self.set_clock(value)
            self.window = PxarGui(ROOT.gClient.GetRoot(), 800, 800)
            plotdata = self.address_level_scan()
            plot = Plotter.create_th1(plotdata, -512, +512, "Address Levels for clk = " + str(value), "ADC", "#")
            self.window.histos.append(plot)
            self.window.update()

    def complete_varyClk(self):
        # return help for the cmd
        return [self.do_varyClk.__doc__, '']

    #    @arity(2,2,[str, int])
    #    def do_DacScan(self, )

    @arity(0, 0, [])
    def do_maddressDecoder(self, verbose=False):
        """do_maddressDecoder: decodes the address of the activated pixel"""
        addresses = self.get_address_levels()
        print addresses
        nAddresses = len(addresses) / 5
        print "There are", nAddresses, "pixel activated"
        matrix = []
        for row in range(80):
            matrix.append([])
            for col in range(52):
                matrix[row].append(0)
        for j in range(10):
            addresses = self.get_address_levels()
            for i in range(len(addresses)):  # norm the lowest level to zero
                addresses[i] += 1
            print str(j + 1) + ". measurement"
            for i in range(nAddresses):
                column = (addresses[i * 5]) * 2 * 6 + (addresses[i * 5 + 1]) * 2 * 1
                if addresses[i * 5 + 4] % 2 != 0:
                    column += 1
                row = 80 - ((addresses[i * 5 + 2]) * 3 * 6 + (addresses[i * 5 + 3]) * 3 * 1)
                if addresses[i * 5 + 4] == 2 or addresses[i * 5 + 4] == 3:
                    row -= 1
                elif addresses[i * 5 + 4] > 3:
                    row -= 2
                # print "address of the "+str(i+1)+". pixel: ", column, row
                matrix[row][column] += 1
        if verbose:
            matrix.append([])
            for i in range(52):
                matrix[80].append(i)
            for i in range(80):
                matrix[i].insert(0, 79 - i)
            matrix[80].insert(0, 99)
            for i in range(81):
                for j in range(53):
                    if matrix[80 - i][j] != 0:
                        print '\033[91m' + '{0:02d}'.format(matrix[i][j]) + '\033[0m',
                    else:
                        print '{0:02d}'.format(matrix[i][j]),
                print ""
        else:

            data = []
            for row in range(len(matrix)):
                for col in range(len(matrix[row])):
                    if matrix[row][col] > 0:
                        px = Pixel()
                        value = self.code_event(row, col, matrix[row][col])
                        px = Pixel(value, 0)
                        data.append(px)
            for i in data:
                print i
            self.window = PxarGui(ROOT.gClient.GetRoot(), 1000, 800)
            self.plot_map(data, "maddressDecoding")

    def complete_maddressDecoder(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_maddressDecoder.__doc__, '']

    @arity(2, 2, [int, int])
    def do_addressDecoding(self, start, end):
        """do_addressDecoding: prints and saves the values of the addresses from the specific pixels"""
        f = open('addresses', 'w')
        print "column\trow\taddresslevels"
        for row in range(start, end + 1):
            for column in range(1):
                self.api.maskAllPixels(1)
                self.api.testAllPixels(0)
                self.api.maskPixel(column, row, 0)
                self.api.testPixel(column, row, 1)
                addresses = self.get_address_levels()
                print '{0:02d}'.format(column) + "\t" + '{0:02d}'.format(row) + "\t" + str(addresses)
                f.write(str('{0:02d}'.format(column)) + ';' + str('{0:02d}'.format(row)) + '; ' + str(addresses) + '\n')
        f.close

    def complete_addressDecoding(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_addressDecoding.__doc__, '']

    @arity(1, 1, [int])
    def do_pixelTest(self, x):
        self.api.daqStart()
        self.api.daqTrigger(1, 500)
        rawEvent = self.api.daqGetRawEvent()
        sumEvent = []
        for i in range(len(rawEvent)):
            sumEvent.append(0)
        for i in range(x):
            self.api.daqTrigger(1, 500)
            rawEvent = self.api.daqGetRawEvent()
            nCount = 0
            for i in rawEvent:
                i = i & 0x0fff
                if i & 0x0800:
                    i -= 4096
                rawEvent[nCount] = i
                nCount += 1
            for i in range(len(rawEvent)):
                sumEvent[i] += rawEvent[i]
        for i in range(len(rawEvent)):
            sumEvent[i] = int(round(float(sumEvent[i]) / x, 0))
        print sumEvent
        self.api.daqStop()

    def complete_pixelTest(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.pixelTest.__doc__, '']

    @arity(0, 1, [int])
    def do_test(self, n_trigger=10000):
        self.api.setDAC("wbc", 126, 3)
        self.api.setTestboardDelays({"tindelay": 23, "toutdelay": 3})
        self.api.daqTriggerSource("extern")
        self.api.daqStart()
        sleep(0.1)

        # creating the matrix
        matrix = []
        for row in range(80):
            matrix.append([])
            for col in range(52):
                matrix[row].append(0)
                # n_trigger = 10000
        print 'Start Test with {0} Trigger'.format(n_trigger)
        for i in range(n_trigger):
            if i % 100 == 0:
                print '{0:5.2f}%\r'.format(i * 100. / n_trigger),
                sys.stdout.flush()
            event = self.get_levels()
            #            print event, self.convertedRaw()
            length = len(event)
            nEvent = (length - 3) / 6  # number of single events
            addresses = []
            for i in range(5 * nEvent):  # fill the list with an many zero as we got addresslevels
                addresses.append(0)
            pos = 0
            addressIndex = 0
            for eventIndex in range(5 * nEvent + nEvent):
                if pos == 5:
                    pos = 0
                    continue
                addresses[addressIndex] = event[3 + eventIndex]
                addressIndex += 1
                pos += 1

            nAddresses = len(addresses) / 5
            #            print "There are", nAddresses, "pixel activated"
            column = 0
            row = 0

            for i in range(nAddresses):
                column = (addresses[i * 5]) * 2 * 6 + (addresses[i * 5 + 1]) * 2 * 1
                if addresses[i * 5 + 4] % 2 != 0:
                    column += 1
                row = 80 - ((addresses[i * 5 + 2]) * 3 * 6 + (addresses[i * 5 + 3]) * 3 * 1)
                if addresses[i * 5 + 4] == 2 or addresses[i * 5 + 4] == 3:
                    row -= 1
                elif addresses[i * 5 + 4] > 3:
                    row -= 2

                # print "address of the "+str(i+1)+". pixel: ", column, row
                matrix[row][column] += 1
        verbose = False
        if verbose:
            matrix.append([])
            for i in range(52):
                matrix[80].append(i)
            for i in range(80):
                matrix[i].insert(0, 79 - i)
            matrix[80].insert(0, 99)
            for i in range(81):
                for j in range(53):
                    if matrix[80 - i][j] != 0:
                        print '\033[91m' + '{0:02d}'.format(matrix[i][j]) + '\033[0m',
                    else:
                        print '{0:02d}'.format(matrix[i][j]),
                print ""
        else:

            data = []
            for row in range(len(matrix)):
                for col in range(len(matrix[row])):
                    if matrix[row][col] > 0:
                        # px = Pixel()
                        value = self.code_event(row, col, matrix[row][col])
                        px = Pixel(value, 0)
                        data.append(px)
                        #            for i in data:
                        #                print i
            self.window = PxarGui(ROOT.gClient.GetRoot(), 1000, 800)
            self.plot_map(data, "maddressDecoding")

            # time.sleep(0.1)
            # self.api.daqGetEventBuffer()
            #            data = []
            #            try:
            #                data = self.api.daqGetEventBuffer()
            #                for i in range(len(data)):wbc
            #                    print wbc, data[i]
            #            except RuntimeError:
            #                pass

    def complete_test(self):
        # return help for the cmd
        return [self.do_test.__doc__, '']

    @arity(0, 3, [int, int, int])
    def do_wbcScan(self, min_wbc=90, max_triggers=50, max_wbc=130):
        """do_wbcScan [minimal WBC] [number of events] [maximal WBC]: \n
        sets wbc from minWBC until it finds the wbc which has more than 90% filled events or it reaches maxWBC \n
        (default [90] [100] [130])"""

        self.api.daqTriggerSource("extern")
        wbc_scan = []
        print "wbc \tyield"

        # loop over wbc
        for wbc in range(min_wbc, max_wbc):
            self.api.setDAC("wbc", wbc)
            self.api.daqStart()
            hits = 0
            triggers = 0

            # loop until you find nTriggers
            while triggers < max_triggers:
                try:
                    data = self.api.daqGetEvent()
                    if len(data.pixels) > 0:
                        hits += 1
                    triggers += 1
                except RuntimeError:
                    pass

            hit_yield = 100 * hits / max_triggers
            wbc_scan.append(hit_yield)
            print '{0:03d}'.format(wbc), "\t", '{0:3.0f}%'.format(hit_yield)

            # stopping criterion
            if wbc > 3 + min_wbc:
                if wbc_scan[-4] > 90:
                    print "Set DAC wbc to", wbc - 3
                    self.api.setDAC("wbc", wbc - 3)
                    break

            # Clear the buffer:
            try:
                self.api.daqGetEventBuffer()
            except RuntimeError:
                pass

        self.api.daqStop()
        self.window = PxarGui(ROOT.gClient.GetRoot(), 1000, 800)
        plot = Plotter.create_tgraph(wbc_scan, "wbc scan", "wbc", "evt/trig [%]", min_wbc)
        self.window.histos.append(plot)
        self.window.update()

    def complete_wbcScan(self):
        # return help for the cmd
        return [self.do_wbcScan.__doc__, '']

    @arity(0, 0, [])
    def do_readMaskFile(self):
        """ do_readMaskFile: reads in the defaultMaskFile and masks accordingly"""
        maskfile = self.dir + 'defaultMaskFile.dat'
        f = open(maskfile)
        mask = []
        for l in f.readlines():
            if l[0] != '#' and l[0] != ' ' and len(l) > 1:
                mask.append(l.split())
        f.close()
        for line in mask:
            if line[0] == 'roc':
                n_rocs = int(line[1])
                print "masking ROC:", n_rocs
                self.api.maskAllPixels(1, n_rocs)
            elif line[0] == 'pix':
                n_rocs = int(line[1])
                col = int(line[2])
                row = int(line[3])
                print "masking Pixel:\t", '{0:02d}'.format(col), '{0:02d}'.format(row), "\tof ROC", n_rocs
                self.api.maskPixel(col, row, 1, n_rocs)
            elif line[0] == 'col':
                n_rocs = int(line[1])
                min_col = int(line[2])
                if len(line) <= 3:
                    print "masking col:\t", min_col, "\tof ROC", n_rocs
                    for row in range(80):
                        self.api.maskPixel(min_col, row, 1, n_rocs)
                if len(line) > 3:
                    max_col = int(line[3])
                    print "masking col:\t", str(min_col) + '-' + str(max_col), "\tof ROC", n_rocs
                    for col in range(min_col, max_col + 1):
                        for row in range(80):
                            self.api.maskPixel(col, row, 1, n_rocs)
            elif line[0] == 'row':
                n_rocs = int(line[1])
                min_row = int(line[2])
                if len(line) <= 3:
                    print "masking row:\t", min_row, "\tof ROC", n_rocs
                    for col in range(52):
                        self.api.maskPixel(col, min_row, 1, n_rocs)
                if len(line) > 3:
                    max_row = int(line[3])
                    print "masking row:\t", str(min_row) + '-' + str(max_row), "\tof ROC", n_rocs
                    for row in range(min_row, max_row + 1):
                        for col in range(52):
                            self.api.maskPixel(col, row, 1, n_rocs)

    def complete_readMaskFile(self):
        # return help for the cmd
        return [self.do_readMaskFile.__doc__, '']


    @arity(1, 3, [str, int, int])
    def do_check_tbsettings(self, name, min_value=0, max_value=20):
        """ do_checkTBsettings [setting] [min] [max]: default: [0,20]"""

        self.api.testAllPixels(0)
        self.api.testPixel(15, 59, 1)
        t = time()
        for delay in range(min_value, max_value):
            self.api.setTestboardDelays({name: delay})
            sleep(1)
            i = 0
            self.api.setDAC("vana", 70 + i)
            i += 1
            #            self.api.daqStart()
            #            self.api.daqTrigger(21,500)
            sleep(1)
            # sumData = [0, 0, 0]
            # levels = [0, 0, 0, 0, 0]
            #            for i in range (20):
            #                data = self.convertedRaw()
            #                if len(data)>2:
            #                    for j in range(2):
            #                        sumData[j] += data[j]
            #                if len(data)>7:
            #                    for j in range(5):
            #                        levels[j] += data[j+3]
            #
            print name, delay,  # len(data),"\t",
            #            for i in range(2):
            #                print '{0:4.0f}'.format(sumData[i]/float(20)),
            #            print "\t",
            #            for i in range(5):
            #                print '{0:3.0f}'.format(levels[i]/float(20)),
            #            print
            print self.api.getTBia() * 1000
        # self.api.daqStop()
        print "test took: ", round(time() - t, 2), "s"

    def complete_check_tbsettings(self):
        # return help for the cmd
        return [self.do_check_tbsettings.__doc__, '']

    @arity(0, 2, [int, int])
    def do_level_check(self, it=20):
        """ do_checkTBsettings [minWBC] [nTrigger]: sets the values of wbc
            from minWBC until it finds the wbc which has more than 90% filled events or it reaches 200 (default minWBC 90)"""

        print "header\t",
        self.get_averaged_level(it)

        print "-1\t",
        self.api.testAllPixels(0)
        self.api.testPixel(0, 79, 1)
        self.get_averaged_level(it)

        print "0\t",
        self.api.testAllPixels(0)
        self.api.testPixel(15, 59, 1)
        self.get_averaged_level(it)

        print "1\t",
        self.api.testAllPixels(0)
        self.api.testPixel(28, 37, 1)
        self.get_averaged_level(it)

        print "2\t",
        self.api.testAllPixels(0)
        self.api.testPixel(43, 16, 1)
        self.get_averaged_level(it)

        print "03033\t",
        self.api.testAllPixels(0)
        self.api.testPixel(20, 48, 1)
        self.get_averaged_level(it)

        print "04044\t",
        self.api.testAllPixels(0)
        self.api.testPixel(23, 45, 1)
        self.get_averaged_level(it)

    def complete_do_levelCheck(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_do_levelCheck.__doc__, '']
    # endregion

    @arity(0, 2, [int, float])
    def do_trigger_loop(self, rate=10, duration=1):
        """ do_triggerLoop [rate] [duration]: sends triggers with rate for duration"""
        self.api.daqStart()
        triggers = int(60 * duration) * rate
        print "number of triggers:", triggers
        for i in range(triggers):
            self.api.daqTrigger(1, 500)
            sleep(float(1) / rate)
            #            print self.convertedRaw()
            #            print "", '\r{0:4.2f}%'.format(100*(float(i)/nTrig)), "\r",
            sec = (triggers - i) / float(rate) % 60
            min_val = (triggers - i) / rate / 60
            print "", '\r{0:02d}:'.format(min_val), '\b{0:02d}:'.format(int(sec)), '\b{0:02.0f}'.format(
                100 * (sec - int(sec))),
            sys.stdout.flush()
        print
        self.api.daqStop()

    def complete_trigger_loop(self):
        return [self.do_trigger_loop.__doc__, '']

    @arity(0, 1, [int])
    def do_hit_map(self, max_triggers=1000):
        """ do_hitMap [maxTriggers]: collects a certain amount triggers and plots a hitmap ... hopefully^^"""

        windowsize = 100
        t = time()
        self.api.daqStart()

        # check if module is True
        module = True
        while True:
            try:
                data = self.api.daqGetEvent()
                #if data.pixels[0].roc == 0:
                    #module = False
                break
            except RuntimeError:
                pass

        d = zeros((417 if module else 53, 161 if module else 81))
        triggers = 0
        t1 = time()
        before = None
        mean = None
        t2 = time()
        while triggers < max_triggers:
            print "\r#events:", '{0:06d}'.format(triggers),
            if triggers < windowsize:
                mean = triggers / (time() - t1)
                print 'rate: {0:03.0f} Hz'.format(mean),
                if triggers == 90:
                    t2 = time()
            elif triggers > before and triggers % 10 == 0:
                mean = float(windowsize - 5) / windowsize * mean + float(windowsize - 95) / windowsize * 10 / (
                    time() - t2)
                print 'rate: {0:03.0f} Hz'.format(mean),
                t2 = time()
            sys.stdout.flush()
            before = triggers
            try:
                data = self.api.daqGetEvent()
                #                if len(data.pixels)>0:
                #                    nTriggers += 1
                #                    for px in data.pixels:
                if len(data.pixels) > 1:
                    triggers += 1
                    for i in range(len(data.pixels) - 1):
                        px = data.pixels[i]
                        xoffset = 52 * (px.roc % 8) if module else 0
                        yoffset = 80 * int(px.roc / 8) if module else 0
                        # Flip the ROCs upside down:
                        y = (px.row + yoffset) if (px.roc < 8) else (2 * yoffset - px.row - 1)
                        # Reverse order of the upper ROC row:
                        x = (px.column + xoffset) if (px.roc < 8) else (415 - xoffset - px.column)
                        d[x + 1][y + 1] += 1 if True else px.value
            except RuntimeError:
                pass
        self.api.daqStop()

        print "test took: ", round(time() - t, 2), "s"
        self.window = PxarGui(ROOT.gClient.GetRoot(), 1000, 800)
        plot = Plotter.create_th2(d, 0, 417 if module else 53, 0, 161 if module else 81, "hitmap", 'pixels x',
                                  'pixels y', "hitmap")
        self.window.histos.append(plot)
        self.window.update()

    def complete_hit_map(self):
        # return help for the cmd
        return [self.do_hit_map.__doc__, '']

    @arity(0, 2, [int, str])
    def do_setup(self, wbc=126, source="extern"):
        self.api.setDAC("wbc", wbc)
        self.api.daqTriggerSource(source)

    def complete_setup(self):
        # return help for the cmd
        return [self.do_setup.__doc__, '']

    @arity(0, 1, [int])
    def do_rate(self, duration=30):
        self.rate(duration)

    def complete_rate(self):
        # return help for the cmd
        return [self.do_rate.__doc__, '']

    @arity(0, 3, [str, int, int])
    def do_ph_vs_vcal(self, fit="gaus", row=14, column=14, average=10):
        start_time = time()
        self.api.testAllPixels(0)
        self.api.maskAllPixels(1)
        print "--> disable and mask all Pixels (" + str(self.api.getNEnabledPixels(0)) + ", " + str(
            self.api.getNMaskedPixels(0)) + ")"
        self.api.testPixel(row, column, 1)
        self.api.maskPixel(row, column, 0)
        print "--> enable and unmask Pixel " + str(row) + "/" + str(column) + " (" + str(
            self.api.getNEnabledPixels(0)) + ", " + str(self.api.getNMaskedPixels(0)) + ")"
        self.api.daqStart()
        sys.stdout.flush()
        low_range = [50, 100, 150, 200, 250]
        high_range = [30, 50, 70, 90, 200]
        points = []
        for i in low_range:
            points.append(i / 7)
        for i in high_range:
            points.append(i)
        ph_y = []
        vcal_x = []
        for vcal in points:
            self.api.setDAC("vcal", vcal)
            sum_ph = 0
            for i in range(average):
                self.api.daqTrigger(1, 500)
                data = self.converted_raw_event()
                if len(data) < 8:
                    sum_ph = 0
                    break
                sum_ph += (data[8] if len(data) == 9 else 0)
            sum_ph /= average
            ph_y.append(sum_ph)
            vcal_x.append(vcal)
        print vcal_x
        print ph_y
        self.api.daqStop()

        # plot ph vs vcal
        self.window = PxarGui(ROOT.gClient.GetRoot(), 1000, 800)
        plot = Plotter.create_tgraph(ph_y, "ph scan", "ph", "vcal", vcal_x)
        plot.SetMarkerSize(0.5)
        plot.SetMarkerStyle(20)
        # f1 = ROOT.TH1.pol1
        plot.Fit(fit)
        self.window.histos.append(plot)
        self.window.update()
        self.elapsed_time(start_time)

    def complete_ph_vs_vcal(self):
        # return help for the cmd
        return [self.do_ph_vs_vcal.__doc__, '']

    @arity(0, 1, [int])
    def do_raw_rate(self, trigger=100):
        sum1 = 0
        sum2 = 0
        for trig in range(trigger):
            data = self.converted_raw_event()
            if len(data) > 3:
                sum1 += 1
            if len(data) > 9:
                sum2 += 1
        print 100 * float(sum1) / trigger, '%'
        print 100 * float(sum2) / trigger, '%'

    def complete_raw_rate(self):
        # return help for the cmd
        return [self.do_raw_rate.__doc__, '']

    @arity(0, 0, [])
    def do_probes(self):
        self.api.SignalProbe("a1", "sdata1")
        self.api.SignalProbe("a2", "tout")
        self.api.SignalProbe("d1", "tin")
        self.api.SignalProbe("d2", "ctr")

    def complete_probes(self):
        # return help for the cmd
        return [self.do_probes.__doc__, '']

    @arity(0, 2, [int, bool])
    def do_check_events(self, trigger=100, doprint=False):

        empty = 0
        trig = 0
        while trig < trigger:
            try:
                data = self.converted_raw_event()
                if len(data) == 3:
                    empty += 1
                trig += 1
                if doprint:
                    print "UB", data[0], "\tlength", len(data)
            except RuntimeError:
                pass
        print 'empty events: {0:03.0f}%'.format(100 * float(empty) / trigger), str(empty) + "/" + str(trigger)

    def complete_check_events(self):
        # return help for the cmd
        return [self.do_check_events.__doc__, '']

    @arity(0, 2, [int, bool])
    def do_check_stack(self, trigger=100):
        stack = 0
        trig = 0
        while trig < trigger:
            data = self.converted_raw_event()
            if len(data) > 1:
                if data[-1] > 1:
                    stack += 1
                    print data[-1]
                trig += 1
                print '\r{0:05d}'.format(trig),
                sys.stdout.flush()
        print 'stacks larger than 2: {0:3.1f}%'.format(100 * float(stack) / trigger), str(stack) + "/" + str(trigger)

    def complete_check_stack(self):
        # return help for the cmd
        return [self.do_check_stack.__doc__, '']

    @arity(0, 2, [int, bool])
    def do_measure_ph(self, max_trigger=20):

        protons = 0
        pions = 0
        trigger = 0
        while trigger < max_trigger:
            #            try:
            #                data = self.api.daqGetEvent()
            #                if len(data.pixels) == 1:
            #                    print data.pixels[0]
            #                    trigger += 1
            #            except RuntimeError:
            #                pass
            data = self.converted_raw_event()
            if 23 > len(data) > 16:
                if data[10] < -80:
                    pions += data[10]
                    trigger += 1
        trigger = 0
        while trigger < max_trigger:
            data = self.converted_raw_event()
            if 23 > len(data) > 16:
                if data[10] > -80:
                    protons += data[10]
                    trigger += 1
        print protons / max_trigger
        print pions / max_trigger

    def complete_measure_ph(self):
        # return help for the cmd
        return [self.do_measure_ph.__doc__, '']

    @arity(0, 1, [int])
    def do_find_phscale(self, step=10):
        """ None """
        self.enable_pix(15, 59)
        triggers = 1000
        spread = []
        roc = 0
        self.api.daqStart()
        for dac, i in zip(range(20, 255, step), range(255)):
            self.api.setDAC('phscale', dac)
            self.api.daqTrigger(triggers, 500)
            spread.append([0])
            event = None
            for k in range(triggers):
                event = self.converted_raw_event()
                spread_j = 0
                for j in range(5):
                    try:
                        spread_j += abs(event[1 + roc * 3] - event[3 + roc * 6 + j])
                    except IndexError:
                        spread_j = 99
                        break
                spread[i][0] += spread_j / 5
            spread[i][0] /= float(triggers)
            spread[i].append(dac)
            print dac, "{0:2.1f}".format(spread[i][0]), event
        self.api.daqStop()
        # find best phscale
        min_phscale = 100
        best_phscale = 120
        for i in spread:
            if i[0] < min_phscale:
                min_phscale = i[0]
                best_phscale = i[1]
        print 'set phscale to:', best_phscale
        self.api.setDAC('phscale', best_phscale)

    def complete_find_phscale(self):
        # return help for the cmd
        return [self.do_find_phscale.__doc__, '']

    @arity(0, 1, [int])
    def do_averaged_levels(self, averaging=1000):
        """ None """
        self.enable_pix(5, 12)
        self.api.daqStart()
        self.api.daqTrigger(averaging, 500)
        averaged_event = [[0], [0]]
        for i in range(8):
            averaged_event[0].append(0)
            averaged_event[1].append(0)
        sleep(0.1)
        for i in range(averaging):
            event = self.converted_raw_event()
            for j in range(9):
                averaged_event[0][j] += event[j]
        self.api.daqStop()
        self.api.maskAllPixels(1, 0)
        self.api.testAllPixels(0, 0)
        self.enable_pix(5, 12, 1)
        self.api.daqStart()
        self.api.daqTrigger(averaging, 500)
        for i in range(averaging):
            event = self.converted_raw_event()
            for j in range(3, 12):
                averaged_event[1][j - 3] += event[j]
        self.api.daqStop()
        for i in range(9):
            averaged_event[0][i] /= averaging
            averaged_event[1][i] /= averaging
        print averaged_event[0]
        print averaged_event[1]

    def complete_averaged_levels(self):
        # return help for the cmd
        return [self.do_averaged_levels.__doc__, '']

    @arity(0, 1, [int])
    def do_adjust_black(self, rocs=4, avg=100):
        """ None """
        self.api.maskAllPixels(1)
        self.api.testAllPixels(0)
        self.api.testPixel(15, 59, 1)
        self.api.maskPixel(15, 59, 0)
        self.api.daqStart()
        self.api.daqTrigger(avg, 500)
        black_dev = []
        black_dev2=[]
        black_real=[]
        for roc in range(rocs):
            black_dev.append([])
            black_dev2.append([])
            black_real.append([])

            for adr in range(5):
                black_dev[roc].append(0)
                black_dev2[roc].append(0)
                black_real[roc].append(0)
        for i in range(avg):
            event = self.converted_raw_event()
            for roc in range(rocs):
                for adr in range(5):
                    val = float((event[1] - event[3 + adr + roc * 9]))
                    black_dev[roc][adr] += val
                    black_dev2[roc][adr] += val*val
        for roc in range(rocs):
            print roc,":",
            for i in range(len(black_dev[roc])):
                mean =  black_dev[roc][i] / avg
                mean2 =  black_dev2[roc][i]/ avg- mean* mean
                mean2 = math.sqrt(mean2)
                print mean, # "+/-",mean2,"\t",
            print
        # for r in black_real[roc]:
        #     print r,
        # print

        self.api.daqStop()

    def complete_do_adjust_black(self):
        # return help for the cmd
        return [self.do_do_adjust_black.__doc__, '']

    @staticmethod
    def do_quit(q=1):
        """quit: terminates the application"""
        sys.exit(q)

    # shortcuts
    do_q = do_quit
    do_a = do_analogLevelScan
    do_sd = do_set_tin_tout
    do_dre = do_daqRawEvent
    do_de = do_daqEvent
    do_sc = do_set_clock_delays
    do_vc = do_varyClk
    do_arm1 = do_enableOnePixel
    do_arm = do_enablePixel
    do_armAll = do_enableAllPixel
    do_raw = do_daqGetRawEvent
    do_ds = do_daqStart
    do_dt = do_daqTrigger
    do_buf = do_daqGetEventBuffer
    do_stat = do_daqStatus
    do_stop = do_daqStop
    do_wbc = do_setup
    do_status = do_daqStatus
    do_event = do_daqGetEvent


def main(argv=None):
    prog_name = ""
    if argv is None:
        argv = sys.argv
        prog_name = os.path.basename(argv.pop(0))

    # command line argument parsing
    import argparse

    parser = argparse.ArgumentParser(prog=prog_name, description="A Simple Command Line Interface to the pxar API.")
    parser.add_argument('--dir', '-d', metavar="DIR", help="The digit rectory with all required config files.")
    parser.add_argument('--gui', '-g', action="store_true", help="The output verbosity set in the pxar API.")
    parser.add_argument('--run', '-r', metavar="FILE",
                        help="Load a cmdline script to be executed before entering the prompt.")
    parser.add_argument('--verbosity', '-v', metavar="LEVEL", default="INFO",
                        help="The output verbosity set in the pxar API.")
    args = parser.parse_args(argv)

    print '\n================================================='
    print '# Extended pXarCore Command Line Interface'
    print '=================================================\n'

    api = PxarStartup(args.dir, args.verbosity)

    # start command line
    prompt = PxarCoreCmd(api, args.gui, args.dir)

    # run the startup script if requested
    if args.run:
        prompt.do_run(args.run)
    # start user interaction
    prompt.cmdloop()


if __name__ == "__main__":
    sys.exit(main())
