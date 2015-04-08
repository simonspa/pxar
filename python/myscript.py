#!/usr/bin/env python2
"""
Simple Example Python Script Using the Pxar API.
"""
import PyPxarCore
from PyPxarCore import Pixel, PixelConfig, PyPxarCore, PyRegisterDictionary, PyProbeDictionary
from numpy import set_printoptions, nan, zeros
from pxar_helpers import * # arity decorator, PxarStartup, PxarConfigFile, PxarParametersFile and others

# Try to import ROOT:
guiAvailable = True
try:
    import ROOT
    ROOT.PyConfig.IgnoreCommandLineOptions = True
    from pxar_gui import PxarGui
    from pxar_plotter import Plotter
except ImportError:
    guiAvailable = False;
    pass

import cmd      # for command interface and parsing
import os       # for file system cmds
import sys
import time


# set up the DAC and probe dictionaries
dacdict = PyRegisterDictionary()
probedict = PyProbeDictionary()


class PxarCoreCmd(cmd.Cmd):
    """Simple command processor for the pxar core API."""

    def __init__(self, api, gui):
        cmd.Cmd.__init__(self)
        self.fullOutput=False
        self.prompt = "pxarCore =>> "
        self.intro  = "Welcome to the pxar core console!"  ## defaults to None
        self.api = api
        self.window = None
        if(gui and guiAvailable):
            self.window = PxarGui(ROOT.gClient.GetRoot(),800,800)
        elif(gui and not guiAvailable):
            print "No GUI available (missing ROOT library)"
    def plot_eventdisplay(self,data):
        pixels = list()
        # Multiple events:
        if(isinstance(data,list)):
            if(not self.window):
                for evt in data:
                    print evt
                return
            for evt in data:
                for px in evt.pixels:
                    pixels.append(px)
        else:
            if(not self.window):
                print data
                return
            for px in data.pixels:
                pixels.append(px)
        self.plot_map(pixels,'Event Display',True)
    def plot_map(self,data,name,count=False):
        if(not self.window):
            print data
            return

        # Find number of ROCs present:
        module = False
        for px in data:
            if px.roc > 0:
                module = True
                break
        # Prepare new numpy matrix:
        d = zeros((416 if module else 52,160 if module else 80))
        for px in data:
            xoffset = 52*(px.roc%8) if module else 0
            yoffset = 80*int(px.roc/8) if module else 0
            # Flip the ROCs upside down:
            y = (px.row + yoffset) if (px.roc < 8) else (2*yoffset - px.row - 1)
            # Reverse order of the upper ROC row:
            x = (px.column + xoffset) if (px.roc < 8) else (415 - xoffset - px.column)
            d[x][y] += 1 if count else px.value

        plot = Plotter.create_th2(d, 0, 415 if module else 51, 0, 159 if module else 79, name, 'pixels x', 'pixels y', name)
        self.window.histos.append(plot)
        self.window.update()
    def plot_1d(self,data,name,dacname,min,max):
        if(not self.window):
            print_data(self.fullOutput,data,(max-min)/len(data))
            return

        # Prepare new numpy matrix:
        d = zeros(len(data))
        for idac, dac in enumerate(data):
            if(dac):
                d[idac] = dac[0].value

        plot = Plotter.create_th1(d, min, max, name, dacname, name)
        self.window.histos.append(plot)
        self.window.update()
    def plot_2d(self,data,name,dac1,step1,min1,max1,dac2,step2,min2,max2):
        if(not self.window):
            for idac, dac in enumerate(data):
                dac1 = min1 + (idac/((max2-min2)/step2+1))*step1
                dac2 = min2 + (idac%((max2-min2)/step2+1))*step2
                s = "DACs " + str(dac1) + ":" + str(dac2) + " - "
                for px in dac:
                    s += str(px)
                print s
            return

        # Prepare new numpy matrix:
        bins1 = (max1-min1)/step1+1
        bins2 = (max2-min2)/step2+1
        d = zeros((bins1,bins2))

        for idac, dac in enumerate(data):
            if(dac):
                bin1 = (idac/((max2-min2)/step2+1))
                bin2 = (idac%((max2-min2)/step2+1))
                d[bin1][bin2] = dac[0].value

        plot = Plotter.create_th2(d, min1, max1, min2, max2, name, dac1, dac2, name)
        self.window.histos.append(plot)
        self.window.update()
    def do_gui(self, line):
        """Open the ROOT results browser"""
        if not guiAvailable:
            print "No GUI available (missing ROOT library)"
            return
        if self.window:
            return
        self.window = PxarGui( ROOT.gClient.GetRoot(), 800, 800 )

    def varyDelays(self,tindelay,toutdelay,verbose=False):
        self.api.setTestboardDelays({"tindelay":tindelay,"toutdelay":toutdelay})
        self.api.daqStart()
        self.api.daqTrigger(1, 500)
        rawEvent = []

        try:
            rawEvent = self.api.daqGetRawEvent()
        except RuntimeError:
            pass

        if verbose: print "raw Event:\t\t",rawEvent
        nCount = 0
        for i in rawEvent:
            i = i & 0x0fff
            if i & 0x0800:
                i -= 4096
            rawEvent[nCount] = i
            nCount += 1
        if verbose: print "converted Event:\t",rawEvent
        self.api.daqStop()
        return rawEvent

    def convertRawEvent(self,verbose=False):

        self.api.daqStart()
        self.api.daqTrigger(1, 500)
        rawEvent = []
        try:
            rawEvent = self.api.daqGetRawEvent()
        except RuntimeError:
            pass
        self.api.daqStop()
        if verbose: print "raw Event:\t\t",rawEvent
        nCount = 0
        for i in rawEvent:
            i = i & 0x0fff
            if i & 0x0800:
                i -= 4096
            rawEvent[nCount] = i
            nCount += 1
        if verbose: print "converted Event:\t",rawEvent
        return rawEvent

    def convertedRaw(self):

        event = []
        try:
            event = self.api.daqGetRawEvent()
        except RuntimeError:
            pass
        nCount = 0
        for i in event:
            i = i & 0x0fff
            if i & 0x0800:
                i -= 4096
            event[nCount] = i
            nCount += 1
        return event

    def addressLevelScan(self):
        self.api.daqStart()
        self.api.daqTrigger(1000,500)   #choose here how many triggers you want to send (crucial for the time it takes)
        plotdata = zeros(1024)
        try:

            while True:
                s = ""
                p = ""
                pos = -3
                dat = self.api.daqGetRawEvent()
                for i in dat:

                    i = i & 0x0fff
                    # Remove PH from hits:
                    if pos == 5:
                        pos = 0
                        continue
                    if i & 0x0800:
                        i -= 4096
                    plotdata[500+i] += 1
                    pos += 1
        except RuntimeError:
            pass
        self.api.daqStop()
        return plotdata

    def setClock(self, value):
        """sets all the delays to the right value if you want to change clk"""
        self.api.setTestboardDelays({"clk":value})
        self.api.setTestboardDelays({"ctr":value})
        self.api.setTestboardDelays({"sda":value+15})
        self.api.setTestboardDelays({"tin":value+5})

    def getAddressLevels(self):

        event       = self.convertRawEvent(verbose=False)
        length      = len(event)
        nEvent      = (length-3)/6          #number of single events
        addresses   = []
        for i in range(5*nEvent):            #fill the list with an many zero as we got addresslevels
            addresses.append(0)
        pos         = 0
        addressIndex= 0
        for eventIndex in range(5*nEvent+nEvent):
            if pos == 5:
                pos = 0
                continue
            addresses[addressIndex] = int(round(float(event[3+eventIndex])/50,0))
            addressIndex    += 1
            pos             += 1
        return addresses

    def codeEvent(self, row, col, number):
        vec = []
        for i in range(27):
            vec.append(0)

        """number convertion"""
        pos = 0
        for i in range (9):
            if number % pow(2,i+1) != 0:
                number -= pow(2,i)
                vec[-pos-1] = 1
            if pos == 3: pos += 1
            pos += 1

        """row convertion"""
        row = (80-row)*2
        row1 = row % 6
        row2 = (row - row1) % 36
        row3 = row - row1 - row2
        for i in range(3):
            if row1 % pow(2,i+1) != 0:
                row1 -= pow(2,i)
                vec[-i-10] = 1
        for i in range(3):
            if row2 % (6*pow(2,i+1)) != 0:
                row2 -= 6*pow(2,i)
                vec[-i-13] = 1
        for i in range(3):
            if row3 % (36*pow(2,i+1)) != 0:
                row3 -= 36*pow(2,i)
                vec[-i-16] = 1

        """column convertion"""
        if col % 2 != 0:
            vec[-10] = 1
            col -= 1
        col1 = col % 12
        col2 = col - col1
        for i in range(3):
            if col1 % (2*pow(2,i+1)) != 0:
                col1 -= 2*pow(2,i)
                vec[-i-19] = 1
        for i in range(3):
            if col2 % (12*pow(2,i+1)) != 0:
                col2 -= 12*pow(2,i)
                vec[-i-22] = 1

        """create decimal number"""
        dec = 0
        length = len(vec)
        for i in vec:
            dec += int(i)*pow(2,length -1)
            length -= 1
        return dec

    def getRawEvent(self):
        data = []
        try:
            data = self.api.daqGetRawEvent()
            nCount = 0
            for i in data:
                i = i & 0x0fff
                if i & 0x0800:
                    i -= 4096
                data[nCount] = int(round(float(i)/50,0))+1
                nCount += 1
        except RuntimeError:
            pass
        return data

#    def varyDAC(self, dacname, dacvalue)


######################################CMDLINEINTERFACE############################################################################

    @arity(0,0,[])
    def do_getTBia(self):
        """getTBia: returns analog DTB current"""
        print "Analog Current: ", (self.api.getTBia()*1000), " mA"
    def complete_getTBia(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_getTBia.__doc__, '']
    @arity(2,2,[str, str])

    def do_SignalProbe(self, probe, name):
        """SignalProbe [probe] [name]: Switches DTB probe output [probe] to signal [name]"""
        self.api.SignalProbe(probe,name)
    def complete_SignalProbe(self, text, line, start_index, end_index):
        probes = ["d1","d2","a1","a2"]
        if len(line.split(" ")) <= 2: # first argument
            if text: # started to type
                # list matching entries
                return [pr for pr in probes
                        if pr.startswith(text)]
            else:
                # list all probes
                return probes
        elif len(line.split(" ")) <= 3: # second argument
            p = "".join(line.split(" ")[1:2])
            if text: # started to type
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

    @arity(2,2,[str, int, int])
    def do_setDAC(self, dacname, value):
        """setDAC [DAC name] [value] [ROCID]: Set the DAC to given value for given roc ID"""
        self.api.setDAC(dacname, value)
    def complete_setDAC(self, text, line, start_index, end_index):
        if text and len(line.split(" ")) <= 2: # first argument and started to type
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

    @arity(0,0,[])
    def do_daqStart(self):
        """daqStart: starts a new DAQ session"""
        self.api.daqStart()
    def complete_daqStart(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_daqStart.__doc__, '']

    @arity(0,0,[])
    def do_daqStop(self):
        """daqStop: stops the running DAQ session"""
        self.api.daqStop()
    def complete_daqStop(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_daqStop.__doc__, '']

    @arity(1,2,[int, int])
    def do_daqTrigger(self, ntrig, period = 0):
        """daqTrigger [ntrig] [period = 0]: sends ntrig patterns to the device"""
        self.api.daqTrigger(ntrig,period)
    def complete_daqTrigger(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_daqTrigger.__doc__, '']

    @arity(3,4,[int, int, int, int])
    def do_testPixel(self, col, row, enable, rocid = None):
        """testPixel [column] [row] [enable] [ROC id]: enable/disable testing of pixel"""
        self.api.testPixel(col,row,enable,rocid)
    def complete_testPixel(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_testPixel.__doc__, '']

    @arity(1,2,[int, int])
    def do_testAllPixels(self, enable, rocid = None):
        """testAllPixels [enable] [rocid]: enable/disable tesing for all pixels on given ROC"""
        self.api.testAllPixels(enable,rocid)
    def complete_testAllPixels(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_testAllPixels.__doc__, '']

    @arity(3,4,[int, int, int, int])
    def do_maskPixel(self, col, row, enable, rocid = None):
        """maskPixel [column] [row] [enable] [ROC id]: mask/unmask pixel"""
        self.api.maskPixel(col,row,enable,rocid)
    def complete_maskPixel(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_maskPixel.__doc__, '']

    @arity(1,2,[int, int])
    def do_maskAllPixels(self, enable, rocid = None):
        """maskAllPixels [enable] [rocid]: mask/unmask all pixels on given ROC"""
        self.api.maskAllPixels(enable,rocid)
    def complete_maskAllPixels(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_maskAllPixels.__doc__, '']

    @arity(0,2,[int, int])
    def do_getEfficiencyMap(self, flags = 0, nTriggers = 10):
        """getEfficiencyMap [flags = 0] [nTriggers = 10]: returns the efficiency map"""
        self.window = PxarGui( ROOT.gClient.GetRoot(), 1000, 800 )
        data = self.api.getEfficiencyMap(flags,nTriggers)
        self.plot_map(data,"Efficiency")
    def complete_getEfficiencyMap(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_getEfficiencyMap.__doc__, '']

    @arity(0,0,[])
    def do_HVon(self):
        """HVon: switch High voltage for sensor bias on"""
        self.api.HVon()
    def complete_HVon(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_HVon.__doc__, '']

    @arity(0,0,[])
    def do_HVoff(self):
        """HVoff: switch High voltage for sensor bias off"""
        self.api.HVoff()
    def complete_HVoff(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_HVoff.__doc__, '']

    @arity(1,1,[str])
    def do_daqTriggerSource(self, source):
        """daqTriggerSource: select the trigger source to be used for the DAQ session"""
        if self.api.daqTriggerSource(source):
            print "Trigger source \"" + source + "\" selected."
        else:
            print "DAQ returns faulty state."
    def complete_daqTriggerSource(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_daqTriggerSource.__doc__, '']

    @arity(0,0,[int])
    def do_daqGetRawEvent(self, convert = 1):
        """daqGetRawEvent [convert]: read one converted event from the event buffer, for convert = 0 it will print the addresslevels"""
        if convert == 1:
            data = self.convertedRaw()
        elif convert == 0:
            data = self.getRawEvent()
        print data

    def complete_daqGetRawEvent(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_daqGetRawEvent.__doc__, '']

    @arity(0,0,[])
    def do_daqGetEventBuffer(self):
        """daqGetEventBuffer: read all decoded events from the DTB buffer"""
        data = []
        try:
            data = self.api.daqGetEventBuffer()
            print data[0]
            for i in data:
                print i.header, i.trailer, i.pixels[0], i.pixels[1]
            #self.plot_eventdisplay(data)
        except RuntimeError:
            pass
    def complete_daqGetEventBuffer(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_daqGetEventBuffer.__doc__, '']

    @arity(0,0,[])
    def do_daqStatus(self):
        """daqStatus: reports status of the running DAQ session"""
        if self.api.daqStatus():
            print "DAQ session is fine"
        else:
            print "DAQ session returns faulty state"
    def complete_daqStatus(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_daqStatus.__doc__, '']

 ######################################TESTFUNCTIONS############################################################################


    @arity(2,2,[str, int])
    def do_setTBdelay(self, dacname, value):
        """setTBdelays: returns analog DTB current"""
        print "set TB DACs: ",dacname,value
        self.api.setTestboardDelays({dacname:value})
    def complete_setTBdelay(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_setTBdelay.__doc__, '']

    @arity(0,2,[int, int])
    def do_setTinTout(self, tin = 14, tout = 8):
        """setTinTout [tin] [tout]: sets tindelay to value tin and toutdelay to tout"""
        print "set tindelay to: ", tin
        print "set toutdelay to: ", tout
        self.api.setTestboardDelays({"tindelay":tin,"toutdelay":tout})
    def complete_setTinTout(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_setTinTout.__doc__, '']

    @arity(1,1,[int])
    def do_setClockDelays(self, value):
        """SetClockDelays [value of clk and ctr]: sets the two TB delays clk and ctr """
        print "TB delays clk and ctr set to: ",value
        self.setClock(value)
    def complete_setClockDelays(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_setClockDelays.__doc__, '']

    @arity(0,0,[])
    def do_daqRawEvent(self):
        """analogLevelScan: scan the ADC levels of an analog ROC"""
        self.api.daqStart()
        self.api.daqTrigger(1,500)
        rawEvent = []
        try:
            rawEvent = self.api.daqGetRawEvent()
        except RuntimeError:
            pass
        print "raw Event:\t\t",rawEvent
        nCount = 0
        for i in rawEvent:
            i = i & 0x0fff
            if i & 0x0800:
                i -= 4096
            rawEvent[nCount] = i
            nCount += 1
        print "converted Event:\t",rawEvent
        self.api.daqStop()
    def complete_daqRawEvent(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_daqRawEvent.__doc__, '']

    @arity(0,0,[])
    def do_daqEvent(self):
        """analogLevelScan: scan the ADC levels of an analog ROC"""
        self.api.daqStart()
        self.api.daqTrigger(1,500)
        #print "##########################################"
        x = self.api.daqGetEvent()
        print x
        self.api.daqStop()
    def complete_daqRawEvent(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_daqEvent.__doc__, '']

    @arity(0,0,[])
    def do_analogLevelScan(self):
        """analogLevelScan: scan the ADC levels of an analog ROC\nTo see all six address levels it is sufficient to activate Pixel 5 12"""
        self.window = PxarGui( ROOT.gClient.GetRoot(), 800, 800 )
        plotdata = self.addressLevelScan()
        x = 0
        for i in range(1024):
            if plotdata[i] !=0:
                if i-x != 1:
                    print "\n"
                print i," ", plotdata[i]
                x = i

        plot = Plotter.create_th1(plotdata, -512, +512, "Address Levels", "ADC", "#")
        self.window.histos.append(plot)
        self.window.update()
    def complete_analogLevelScan(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_analogLevelScan.__doc__, '']

    @arity (0,0,[])
    def do_enableAllPixel(self):
        """enableAllPixel: enables and unmasks all Pixels"""
        self.api.maskAllPixels(0)
        self.api.testAllPixels(1)
    def complete_enableAllPixel(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_enableAllPixel.__doc__, '']

    @arity (2,2,[int, int])
    def do_enableColumn(self, start, end):
        """enableAllPixel: enables and unmasks all Pixels"""
        for i in range(52):
            for j in range(start,end+1):
                self.api.maskPixel(i,j,0)
        print str(4160 - self.api.getNMaskedPixels(0)) + " Pixels unmasked"
    def complete_enableColumn(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_enableColumn.__doc__, '']

    @arity(2,2,[int, int])
    def do_enableFirstPixel(self, row, column):
        """enablePixel [row] [column] : enables the desired Pixel and masks and disables the rest"""
        self.api.maskAllPixels(1)
        print "--> disable and mask all Pixels (" + str(self.api.getNEnabledPixels(0)) + ", " + str(self.api.getNMaskedPixels(0)) + ")"
        self.api.maskPixel(row,column,0)
        print "--> enable and unmask Pixel " + str(row) + "/" + str(column) + " (" + str(self.api.getNEnabledPixels(0)) + ", " + str(self.api.getNMaskedPixels(0)) + ")"
    def complete_enableFirstPixel(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_enableFirstPixel.__doc__, '']

    @arity(1,1,[int])
    def do_xEnableBlock(self, blocksize):
        """enablePixel [row] [column] : enables the desired Pixel and masks and disables the rest"""
        self.api.maskAllPixels(1)
        print "--> all Pixels masked (" + str(self.api.getNMaskedPixels(0)) + ")"
        for i in range(3,blocksize+3):
            for j in range(3,blocksize+3):
                self.api.maskPixel(i,j,0)
        print "--> unmask Block 3/3 to " + str(blocksize+3)+"/"+ str(blocksize+3) +" ("+ str(self.api.getNMaskedPixels(0)) + " Pixel)"
    def complete_xEnableBlock(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_xEnableBlock.__doc__, '']

    @arity(2,2,[int, int])
    def do_enablePixel(self, row, column):
        """enablePixel [row] [column] : enables the desired Pixel and masks and disables the rest"""
        self.api.testPixel(row,column,1)
        self.api.maskPixel(row,column,0)
        print "--> enable and unmask Pixel " + str(row) + "/" + str(column) + " (" + str(self.api.getNEnabledPixels(0)) + ", " + str(self.api.getNMaskedPixels(0)) + ")"
    def complete_enablePixel(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_enablePixel.__doc__, '']

    @arity(0,0,[])
    def do_PixelActive(self):
        """PixelActive : shows how many Pixels are acitve and how many masked"""
        if self.api.getNEnabledPixels() == 1: print "1", "\tPixel active"
        else: print self.api.getNEnabledPixels(), "\tPixels active"
        print self.api.getNMaskedPixels(), "\tPixels masked"
    def complete_PixelActive(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_PixelActive.__doc__, '']

    @arity(1,1,[int])
    def do_varyAllDelays(self, filenumber):
        """varyAllDelays [filenumber] : writes rawEvent data for both delays varied between 0 and 20 to file (rawfile+filenumber)"""
        number = '{0:03d}'.format(filenumber)
        f = open('rawfile'+str(number),'w')
        for tin in range(20):
            for tout in range(20):
                if (tin-tout<8):
                    rawEvent = self.varyDelays(tin, tout,verbose=False)
                    print tin,"; ",tout,"; " ,rawEvent
                    f.write(str(tin)+';'+str(tout)+'; '+str(rawEvent)+'\n')
        f.close
    def complete_varyAllDelays(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_varyAllDelays.__doc__, '']

    @arity(2,2,[int, int])
    def do_varyDelays(self, tindelay, toutdelay):
        """varDelays [value of tinelay] [value of toutdelay] : sets the two delays to the desired values and prints a histogram of the rawfile"""
        self.varyDelays(tindelay,toutdelay,verbose=True)
    def complete_varyDelays(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_varyDelays.__doc__, '']

#    @arity(0,0,[])
#    def do_findAnalogueTBDelays(self):
#        """findAnalogueTBDelays: configures tindelay and toutdelay"""
#        print ""
#        bestTin = 10    #default value if algorithm should fail
#        print "scan tindelay:"
#        print "tindelay\ttoutdelay\trawEvent[0]"
#        for tin in range(5,20):
#            rawEvent = self.varyDelays(tin, 20,verbose=False)
#            print str(tin)+"\t\t20\t\t"+str(rawEvent[0])
#            if (rawEvent[0] < -100):    #triggers for UB, the first one should always be UB
#                bestTin = tin
#                break
#        print ""
#        bestTout = 20   #default value if algorithm should fail
#        tout = bestTin+5
#        print "scan toutdelay"
#        print "tindelay\ttoutdelay\trawEvent[-1]"
#        for i in range (15):
#            rawEvent = self.varyDelays(bestTin, tout,verbose=False)
#            print str(bestTin)+"\t\t"+str(tout)+"\t\t"+str(rawEvent[-1])
#            if rawEvent[-1] > 20:   #triggers for PH, the last one should always be a pos PH
#                bestTout = tout
#                break
#            tout -= 1
#        print ""
#        self.api.setTestboardDelays({"tindelay":bestTin,"toutdelay":bestTout})
#        print "set tindelay to:  ", bestTin
#        print "set toutdelay to: ", bestTout
#    def complete_FindTBDelays(self, text, line, start_index, end_index):
#        # return help for the cmd
#        return [self.do_FindTBDelays.__doc__, '']

    @arity(0,1,[str])
    def do_findAnalogueTBDelays(self, triggerSource = "intern"):
        """findAnalogueTBDelays: configures tindelay and toutdelay"""
        print ""
        bestTin     = 10    #default value if algorithm should fail
        bestTout    = 20    #default value if algorithm should fail
        print "scan tindelay:"
        print "tindelay\ttoutdelay\trawEvent[0]"

        for tin in range(5,20):
            if triggerSource == "intern":
                event = self.varyDelays(tin, 20,verbose=False)
            elif triggerSource == "extern":
                self.api.setTestboardDelays({"tindelay":tin})
                self.api.daqStart()
                event = self.convertedRaw()
                self.api.daqStop()
            print str(tin)+"\t\t20\t\t"+str(event[0])
            if (event[0] < -100):    #triggers for UB, the first one should always be UB
                bestTin = tin
                break

        print ""
        tout = bestTin+5
        print "scan toutdelay"
        print "tindelay\ttoutdelay\trawEvent[-1]"
        for i in range (15):
            rawEvent = self.varyDelays(bestTin, tout,verbose=False)
            print str(bestTin)+"\t\t"+str(tout)+"\t\t"+str(rawEvent[-1])
            if rawEvent[-1] > 20:   #triggers for PH, the last one should always be a pos PH
                bestTout = tout
                break
            tout -= 1
        print ""
        self.api.setTestboardDelays({"tindelay":bestTin,"toutdelay":bestTout})
        print "set tindelay to:  ", bestTin
        print "set toutdelay to: ", bestTout
    def complete_FindTBDelays(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_FindTBDelays.__doc__, '']

    @arity(0,2,[int, int])
    def do_findDelays(self, start=10, end=16):
        """findDelays: configures tindelay and toutdelay"""
        self.api.setDAC("wbc", 114)
        self.api.daqTriggerSource("extern")
        for tin in range(start, end):
            self.api.setTestboardDelays({"tindelay":14,"toutdelay":tin})
            self.api.daqStart()
            time.sleep(0.1)
            print tin,
            data = self.getRawEvent()
            print len(data), data
            self.api.daqStop()

    def complete_findDelays(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_findDelays.__doc__, '']

    @arity(0,0,[])
    def do_ScanVana(self):
        """ScanVana: finds the best setting for vana so that the analogue current is nearly 24"""
        for vana in range(100, 150):
            x = self.api.getTBia()*1000
            if (x<24.5 and x>23.5):
                y = vana
                break
            self.api.setDAC("vana", vana-1)
            time.sleep(0.4)
            print vana-1, x
        print "\nset vana to ", vana-1
    def complete_ScanVana(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_ScanVana.__doc__, '']

    @arity(2,2,[int, int])
    def do_varyClk(self, start, end):
        """varyClk [start] [end]: plots addresslevelscans for clk delay settings between [start] and [end] and varies all other delays accordingly"""
        self.api.maskAllPixels(1)
        self.api.testAllPixels(0)
        self.api.testPixel(25,25,1)
        self.api.maskPixel(25,25,0)
        self.api.testPixel(50,50,1)
        self.api.maskPixel(50,50,0)
        self.api.testPixel(10,70,1)
        self.api.maskPixel(10,70,0)
        for value in range(start, end+1):
            print "prints the histo for clk = "+str(value)+"..."
            self.setClock(value)
            self.window = PxarGui( ROOT.gClient.GetRoot(), 800, 800 )
            plotdata = self.addressLevelScan()
            plot = Plotter.create_th1(plotdata, -512, +512, "Address Levels for clk = "+str(value), "ADC", "#")
            self.window.histos.append(plot)
            self.window.update()
    def complete_varyClk(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_varyClk.__doc__, '']

#    @arity(2,2,[str, int])
#    def do_DacScan(self, )

    @arity(0,0,[])
    def do_maddressDecoder(self, verbose = False):
        """do_maddressDecoder: decodes the address of the activated pixel"""
        addresses = self.getAddressLevels()
        print addresses
        nAddresses = len(addresses)/5
        print "There are", nAddresses, "pixel activated"
        matrix = []
        for row in range(80):
            matrix.append([])
            for col in range(52):
                matrix[row].append(0)
        for j in range(10):
            addresses = self.getAddressLevels()
            for i in range(len(addresses)):     #norm the lowest level to zero
                addresses[i] += 1
            print str(j+1)+". measurement"
            for i in range(nAddresses):
                column = (addresses[i*5])*2*6 + (addresses[i*5+1])*2*1
                if addresses[i*5+4] % 2 != 0 :
                    column +=1
                row =  80 - ((addresses[i*5+2])*3*6 + (addresses[i*5+3])*3*1)
                if addresses[i*5+4] == 2 or addresses[i*5+4] == 3:
                    row -= 1
                elif addresses[i*5+4] > 3:
                    row -= 2
                #print "address of the "+str(i+1)+". pixel: ", column, row
                matrix[row][column] += 1
        if verbose:
            matrix.append([])
            for i in range(52):
                matrix[80].append(i)
            for i in range(80):
                matrix[i].insert(0,79-i)
            matrix[80].insert(0,99)
            for i in range(81):
                for j in range(53):
                    if matrix[80-i][j] != 0:
                        print '\033[91m'+'{0:02d}'.format(matrix[i][j])+'\033[0m',
                    else: print '{0:02d}'.format(matrix[i][j]),
                print ""
        else:

            data = []
            for row in range(len(matrix)):
                for col in range(len(matrix[row])):
                    if matrix[row][col] > 0:
                        px = Pixel()
                        value = self.codeEvent(row, col,matrix[row][col])
                        px = Pixel(value,0)
                        data.append(px)
            for i in data:
                print i
            self.window = PxarGui( ROOT.gClient.GetRoot(), 1000, 800 )
            self.plot_map(data,"maddressDecoding")


    def complete_maddressDecoder(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_maddressDecoder.__doc__, '']

    @arity(2,2,[int, int])
    def do_addressDecoding(self, start, end):
        """do_addressDecoding: prints and saves the values of the addresses from the specific pixels"""
        f = open('addresses','w')
        print "column\trow\taddresslevels"
        for row in range(start, end+1):
            for column in range(1):
                self.api.maskAllPixels(1)
                self.api.testAllPixels(0)
                self.api.maskPixel(column,row,0)
                self.api.testPixel(column,row,1)
                addresses = self.getAddressLevels()
                print '{0:02d}'.format(column)+"\t"+'{0:02d}'.format(row)+"\t"+str(addresses)
                f.write(str('{0:02d}'.format(column))+';'+str('{0:02d}'.format(row))+'; '+str(addresses)+'\n')
        f.close

    def complete_addressDecoding(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_addressDecoding.__doc__, '']

    @arity(1,1,[int])
    def do_pixelTest(self, x):
        self.api.daqStart()
        self.api.daqTrigger(1,500)
        rawEvent = self.api.daqGetRawEvent()
        sumEvent = []
        for i in range(len(rawEvent)):
            sumEvent.append(0)
        for i in range(x):
            self.api.daqTrigger(1,500)
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
            sumEvent[i] = int(round(float(sumEvent[i])/x,0))
        print sumEvent
        self.api.daqStop()

    def complete_pixelTest(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.pixelTest.__doc__, '']

    @arity(0,0,[])
    def do_Test(self):
        self.api.setDAC("wbc", 115)
        self.api.setTestboardDelays({"tindelay":14,"toutdelay":2})
        self.api.daqTriggerSource("extern")
        self.api.daqStart()
        time.sleep(0.1)

        #creating the matrix
        matrix = []
        for row in range(80):
            matrix.append([])
            for col in range(52):
                matrix[row].append(0)
        n_trigger = 10000
        print 'Start Test with {0} Trigger'.format(n_trigger)
        for i in range(n_trigger):
            if i%100 == 0:
                print '{0:5.2f}%\r'.format(i*100./n_trigger)
#            data = self.getRawEvent()
            event       = self.getRawEvent()
            length      = len(event)
            nEvent      = (length-3)/6          #number of single events
            addresses   = []
            for i in range(5*nEvent):            #fill the list with an many zero as we got addresslevels
                addresses.append(0)
            pos         = 0
            addressIndex= 0
            for eventIndex in range(5*nEvent+nEvent):
                if pos == 5:
                    pos = 0
                    continue
                addresses[addressIndex] = event[3+eventIndex]
                addressIndex    += 1
                pos             += 1

            nAddresses = len(addresses)/5
#            print "There are", nAddresses, "pixel activated"
            column  = 0
            row     = 0

            for i in range(nAddresses):
                column = (addresses[i*5])*2*6 + (addresses[i*5+1])*2*1
                if addresses[i*5+4] % 2 != 0 :
                    column +=1
                row =  80 - ((addresses[i*5+2])*3*6 + (addresses[i*5+3])*3*1)
                if addresses[i*5+4] == 2 or addresses[i*5+4] == 3:
                    row -= 1
                elif addresses[i*5+4] > 3:
                    row -= 2

#                print "address of the "+str(i+1)+". pixel: ", column, row
                matrix[row][column] += 1
        verbose = False
        if verbose:
            matrix.append([])
            for i in range(52):
                matrix[80].append(i)
            for i in range(80):
                matrix[i].insert(0,79-i)
            matrix[80].insert(0,99)
            for i in range(81):
                for j in range(53):
                    if matrix[80-i][j] != 0:
                        print '\033[91m'+'{0:02d}'.format(matrix[i][j])+'\033[0m',
                    else: print '{0:02d}'.format(matrix[i][j]),
                print ""
        else:

            data = []
            for row in range(len(matrix)):
                for col in range(len(matrix[row])):
                    if matrix[row][col] > 0:
                        px = Pixel()
                        value = self.codeEvent(row, col,matrix[row][col])
                        px = Pixel(value,0)
                        data.append(px)
#            for i in data:
#                print i
            self.window = PxarGui( ROOT.gClient.GetRoot(), 1000, 800 )
            self.plot_map(data,"maddressDecoding")

            #time.sleep(0.1)
            #self.api.daqGetEventBuffer()
#            data = []
#            try:
#                data = self.api.daqGetEventBuffer()
#                for i in range(len(data)):wbc
#                    print wbc, data[i]
#            except RuntimeError:
#                pass

    def complete_Test(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.Test.__doc__, '']

    @arity(0,2,[int, int])
    def do_wbcScan(self, minWBC = 90, nTrigger = 50):
        """ do_wbcScan [minWBC] [nTrigger]: sets the values of wbc from minWBC until it finds the wbc which has more than 90% filled events or it reaches 255 (default minWBC 90)"""
        self.api.daqTriggerSource("extern")
        self.api.daqStop()

        print "wbc \t#Events \texample Event"
        maxWBC = 255
        wbcScan = []
        for wbc in range (minWBC,maxWBC):
            self.convertedRaw()
            self.api.setDAC("wbc", wbc)
            time.sleep(0.01)
            self.api.daqStart()
            nEvents     = 0
            it          = 0
            exEvent     = []
            for j in range(nTrigger):
                data = self.convertedRaw()
                if len(data) > 0:   #and data[0] < -100 (might add this as well if tindelay is set correctly)
                    if(it==0):
                        exEvent = data
                        it +=1
                    nEvents += 1
            nEvents = 100*nEvents/nTrigger
            wbcScan.append(nEvents)
            if wbc>3+minWBC:
                if wbcScan[-3] > 90:
                    print "Set wbc to", wbc-2
                    self.api.setDAC("wbc", wbc-2)
                    self.api.daqStop()
                    break
            print '{0:03d}'.format(wbc),"\t", '{0:3.0f}%'.format(nEvents),"\t\t", exEvent
            self.api.daqStop()

        self.window = PxarGui( ROOT.gClient.GetRoot(), 1000, 800 )
#        plot = Plotter.create_th1(wbcScan, minWBC, maxWBC, "wbc scan", "wbc", "%")
        plot = Plotter.create_mygraph(wbcScan, "wbc scan", "wbc", "evt/trig [%]", minWBC)
        self.window.histos.append(plot)
        self.window.update()

    def complete_wbcScan(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_wbcScan.__doc__, '']

    @arity(0,3,[int, int, int])
    def do_wbcScan1(self, minWBC = 90, maxWBC = 200, nTrigger = 50):
        """ do_wbcScan [minWBC] [maxWBC] [nTrigger]: sets the values of wbc from minWBC until it finds the wbc which has more than 90% filled events or it reaches 255 (default minWBC 90)"""

        self.api.daqTriggerSource("extern")

        print "wbc \t#Events \texample Event"
        wbcScan = []
        for wbc in range (minWBC,maxWBC):
            self.api.setDAC("wbc", wbc)
            self.api.daqStart()

            nEvents = 0
            exEvent = []

            for j in range(nTrigger):
                try:
                    data = self.api.daqGetEvent()
                    if len(data.pixels) > 0:
                        nEvents += 1
                except RuntimeError:
                    pass

            nEvents = 100*nEvents/nTrigger
            wbcScan.append(nEvents)

            print '{0:03d}'.format(wbc),"\t", '{0:3.0f}%'.format(nEvents),"\t\t", exEvent
            self.api.daqStop()

        def complete_wbcScan1(self, text, line, start_index, end_index):
            # return help for the cmd
            return [self.do_wbcScan1.__doc__, '']


    @arity(0,2,[int, int])
    def do_dacDacScan(self, minWBC = 90, nTrigger = 50):
        """ do_wbcScan [minWBC] [nTrigger]: sets the values of wbc from minWBC until it finds the wbc which has more than 90% filled events or it reaches 200 (default minWBC 90)"""

#        self.api.maskAllPixels(1)
#        self.api.testPixel(25,40,1)
#        self.api.maskPixel(25,40,0)
#        self.api.daqStart()
#        print "--> enable and unmask Pixel " + str(25) + "/" + str(40) + " (" + str(self.api.getNEnabledPixels(0)) + ", " + str(self.api.getNMaskedPixels(0)) + ")"
#        for vthrcomp in range(0,256):
#            self.api.setDAC("vthrcomp",vthrcomp)
#            self.api.daqTrigger(1,500)
#            data = self.convertedRaw()
#            if len(data)>3:
##                print vthrcomp, data
#        for vthrcomp in range(0,256):
#            print vthrcomp
#            t = time.time()
#            for caldel in range(0,255):
#                self.api.setDAC("vthrcomp",vthrcomp)
#                self.api.setDAC("caldel",caldel)
#                self.api.daqTrigger(1,152)
#            print "time elapsed: ", time.time()-t
#        data = self.convertedRaw()
#                if len(data)>3:
#                    print vthrcomp, caldel, data
#        self.api.daqTrigger(1,500)
#        data = self.api.daqGetEvent()
#        print data, data.pixels, len(data.pixels)
#        self.api.daqStop()

        self.api.daqTriggerSource("extern")
        self.api.setDAC("wbc", 115)
        self.api.setTestboardDelays({"tindelay":14,"toutdelay":2})
        self.api.daqStart()


    def complete_dacDacScan(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_dacDacScan.__doc__, '']

    def do_quit(self, arg):
        """quit: terminates the application"""
        sys.exit(1)

    # shortcuts
    do_q    = do_quit
    do_a    = do_analogLevelScan
    do_sd   = do_setTinTout
    do_vd   = do_varyDelays
    do_vad  = do_varyAllDelays
    do_dre  = do_daqRawEvent
    do_de   = do_daqEvent
    do_sc   = do_setClockDelays
    do_vc   = do_varyClk
    do_arm  = do_enablePixel
    do_ucol = do_enableColumn
    do_raw  = do_daqGetRawEvent
    do_ds   = do_daqStart
    do_dt   = do_daqTrigger
    do_buf  = do_daqGetEventBuffer
    do_stat = do_daqStatus
    do_stop = do_daqStop



def main(argv=None):
    if argv is None:
        argv = sys.argv
        progName = os.path.basename(argv.pop(0))

    # command line argument parsing
    import argparse
    parser = argparse.ArgumentParser(prog=progName, description="A Simple Command Line Interface to the pxar API.")
    parser.add_argument('--dir', '-d', metavar="DIR", help="The digit rectory with all required config files.")
    parser.add_argument('--gui', '-g', action="store_true", help="The output verbosity set in the pxar API.")
    parser.add_argument('--run', '-r', metavar="FILE", help="Load a cmdline script to be executed before entering the prompt.")
    parser.add_argument('--verbosity', '-v', metavar="LEVEL", default="INFO", help="The output verbosity set in the pxar API.")
    args = parser.parse_args(argv)

    api = PxarStartup(args.dir,args.verbosity)

    print '\n###########################Test program for AddressLevelTest#############################\n'

    #start command line
    prompt = PxarCoreCmd(api,args.gui)

     # run the startup script if requested
    if args.run:
        prompt.do_run(args.run)
    # start user interaction
    prompt.cmdloop()

    # get pulseheight vs DAC

    #hits = api.getPulseheightVsDAC("vcal", 1, 15, 32)
#

    #hits = api.analogLevelTest()
#
    # print output
    # uncomment the next line for full output
    # set_printoptions(threshold=nan)
    #print hits

    #print "Done"



if __name__ == "__main__":
    sys.exit(main())
