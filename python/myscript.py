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
        self.api.setTestboardDelays({"tindelay":tindelay})
        self.api.setTestboardDelays({"toutdelay":toutdelay})
        self.api.daqStart()
        self.api.daqTrigger(1, 500)
        rawEvent = self.api.daqGetRawEvent()
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
        return plotdata

    def setClock(self, value):
        """sets all the delays to the right value if you want to change clk"""
        self.api.setTestboardDelays({"clk":value})
        self.api.setTestboardDelays({"ctr":value})
        self.api.setTestboardDelays({"sda":value+15})
        self.api.setTestboardDelays({"tin":value+5})


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

    @arity(0,2,[int, int])
    def do_getEfficiencyMap(self, flags = 0, nTriggers = 10):
        """getEfficiencyMap [flags = 0] [nTriggers = 10]: returns the efficiency map"""
        data = self.api.getEfficiencyMap(flags,nTriggers)
        self.plot_map(data,"Efficiency")
    def complete_getEfficiencyMap(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_getEfficiencyMap.__doc__, '']

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

 ######################################TESTFUNCTIONS############################################################################


    @arity(2,2,[str, int])
    def do_setTBdelay(self, dacname, value):
        """setTBdelays: returns analog DTB current"""
        print "set TB DACs: ",dacname,value
        self.api.setTestboardDelays({dacname:value})
    def complete_setTBdelay(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_setTBdelay.__doc__, '']

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
        #print "##########################################"
        rawEvent = self.api.daqGetRawEvent()
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
        """analogLevelScan: scan the ADC levels of an analog ROC"""
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
        self.api.daqStop()
    def complete_analogLevelScan(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_analogLevelScan.__doc__, '']

    @arity (0,0,[])
    def do_enableAllPixel(self):
        self.api.maskAllPixels(0)
        self.api.testAllPixels(1)
    def complete_enableAllPixel(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_enableAllPixel.__doc__, '']

    @arity(2,2,[int, int])
    def do_enableFirstPixel(self, row, column):
        """enablePixel [row] [column] : enables the desired Pixel and masks and disables the rest"""
        self.api.maskAllPixels(1)
        self.api.testAllPixels(0)
        print "--> disable and mask all Pixels (" + str(self.api.getNEnabledPixels(0)) + ", " + str(self.api.getNMaskedPixels(0)) + ")"
        self.api.testPixel(row,column,1)
        self.api.maskPixel(row,column,0)
        print "--> enable and unmask Pixel " + str(row) + "/" + str(column) + " (" + str(self.api.getNEnabledPixels(0)) + ", " + str(self.api.getNMaskedPixels(0)) + ")"
    def complete_enableFirstPixel(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_enableFirstPixel.__doc__, '']

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
#        self.window = PxarGui(ROOT.gClient.GetRoot(), 800, 800)
#        rawEvent.append(0)
#        x = len(rawEvent)-1
#        for i in range(len(rawEvent)):
#            rawEvent[x] = rawEvent[x-1]
#            x-=1
#        plot = Plotter.create_th1(rawEvent, 0, len(rawEvent), "Raw Event", "#", "Value")
#        self.window.histos.append(plot)
#        self.window.update()
    def complete_varyDelays(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_varyDelays.__doc__, '']

    @arity(0,0,[])
    def do_FindDelays(self):
        """FindDelays: prints the best settings for tindelay and toutdelay"""
        bestTin = 10
        for tin in range(5,20):
            rawEvent = self.varyDelays(tin, 20,verbose=False)
            print tin,"; ",20,"; " ,rawEvent[0]
            if (rawEvent[0] < -100):
                bestTin = tin
                break
        print "\ntindelay should be:", bestTin, "\n"

        tout = bestTin+5
        for i in range (11):
            rawEvent = self.varyDelays(bestTin, tout,verbose=False)
            print bestTin ,"; ",tout,"; " ,rawEvent[-1]
            if rawEvent[-1] > 20:
                bestTout = tout
            tout -= 1
        print "\ntindelay should be:", bestTout, "\n"

    def complete_FindDelays(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_FindDelays.__doc__, '']


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
        for value in range(start, end):
            print "prints the histo for clk = "+str(value)+"..."
            self.setClock(value)
            self.window = PxarGui( ROOT.gClient.GetRoot(), 800, 800 )
            plotdata = self.addressLevelScan()
            plot = Plotter.create_th1(plotdata, -512, +512, "Address Levels for clk = "+str(value), "ADC", "#")
            self.window.histos.append(plot)
            self.window.update()
            self.api.daqStop()


    def complete_varyClk(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_varyClk.__doc__, '']

#    @arity(2,2,[str, int])
#    def do_DacScan(self, )


    def do_quit(self, arg):
        """quit: terminates the application"""
        sys.exit(1)

    # shortcuts
    do_q    = do_quit
    do_a    = do_analogLevelScan
    do_sd   = do_setTBdelay
    do_vd   = do_varyDelays
    do_vad  = do_varyAllDelays
    do_dre  = do_daqRawEvent
    do_de   = do_daqEvent
    do_sc   = do_setClockDelays
    do_vc   = do_varyClk


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
