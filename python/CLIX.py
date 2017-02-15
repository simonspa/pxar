#!/usr/bin/env python2
"""
Simple Example Python Script Using the Pxar API.
"""


# ==============================================
# IMPORTS
# ==============================================
# region imports
from numpy import zeros, array, mean
from pxar_helpers import *  # arity decorator, PxarStartup, PxarConfigFile, PxarParametersFile and others
from sys import stdout

# Try to import ROOT:
gui_available = True
try:
    import ROOT
except ImportError:
    gui_available = False
    pass
if gui_available:
    from ROOT import PyConfig, gStyle, TCanvas, gROOT, TGraph, TMultiGraph, TH1I, gRandom, TCutG

    PyConfig.IgnoreCommandLineOptions = True
    from pxar_gui import PxarGui
    from pxar_plotter import Plotter

import cmd  # for command interface and parsing
import os  # for file system cmds
import sys
from time import time, sleep, strftime
from collections import OrderedDict
from progressbar import Bar, ETA, FileTransferSpeed, Percentage, ProgressBar

# set up the DAC and probe dictionaries
dacdict = PyRegisterDictionary()
probedict = PyProbeDictionary()
# endregion

palette = array([632, 810, 807, 797, 800, 400, 830, 827, 817, 417], 'i')
gStyle.SetPalette(len(palette), palette)


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
        self.Plots = []
        self.ProgressBar = None
        self.NRows = 80
        self.NCols = 52
        if gui and gui_available:
            self.window = PxarGui(ROOT.gClient.GetRoot(), 800, 800)
        elif gui and not gui_available:
            print "No GUI available (missing ROOT library)"

    def start_pbar(self, n):
        self.ProgressBar = ProgressBar(widgets=['Progress: ', Percentage(), ' ', Bar(marker='>'), ' ', ETA(), ' ', FileTransferSpeed()], maxval=n)
        self.ProgressBar.start()

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

    def plot_graph(self, gr, lm=.12, rm=.1, draw_opt='alp'):
        c = TCanvas('c', 'c', 1000, 1000)
        c.SetMargin(lm, rm, .1, .1)
        gr.Draw(draw_opt)
        self.window = c
        self.Plots.append(gr)
        self.window.Update()

    def plot_map(self, data, name, count=False, no_stats=False):
        # if not self.window:
        #     print data
        #     return

        # c = gROOT.GetListOfCanvases()[-1]
        c = TCanvas('c', 'c', 1000, 1000)
        c.SetRightMargin(.12)

        # Find number of ROCs present:
        module = False
        for px in data:
            if px.roc > 0:
                module = True
                break
        # Prepare new numpy matrix:
        d = zeros((417 if module else 52, 161 if module else 80))
        for px in data:
            xoffset = 52 * (px.roc % 8) if module else 0
            yoffset = 80 * int(px.roc / 8) if module else 0
            # Flip the ROCs upside down:
            y = (px.row + yoffset) if (px.roc < 8) else (2 * yoffset - px.row - 1)
            # Reverse order of the upper ROC row:
            x = (px.column + xoffset) if (px.roc < 8) else (415 - xoffset - px.column)
            d[x][y] += 1 if count else px.value


        plot = Plotter.create_th2(d, 0, 417 if module else 52, 0, 161 if module else 80, name, 'pixels x', 'pixels y', name)
        if no_stats:
            plot.SetStats(0)
        plot.Draw('COLZ')
        # draw margins of the rocs for the module
        if module:
            for i in xrange(2):
                for j in xrange(8):
                    rows, cols = self.NRows, self.NCols
                    x = array([cols * j, cols * (j + 1), cols * (j + 1), cols * j, cols * j ], 'd')
                    y = array([rows * i, rows * i, rows * (i + 1), rows * (i + 1), rows * i], 'd')
                    cut = TCutG('r{n}'.format(n=j + (j * i)), 5, x, y)
                    cut.SetLineColor(1)
                    cut.SetLineWidth(1)
                    self.Plots.append(cut)
                    cut.Draw('same')
        self.window = c
        self.Plots.append(plot)
        # self.window.histos.append(plot)
        self.window.Update()

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
        # if not self.window:
        #     for idac, dac in enumerate(data):
        #         dac1 = min1 + (idac / ((max2 - min2) / step2 + 1)) * step1
        #         dac2 = min2 + (idac % ((max2 - min2) / step2 + 1)) * step2
        #         s = "DACs " + str(dac1) + ":" + str(dac2) + " - "
        #         for px in dac:
        #             s += str(px)
        #         print s
        #     return
        c = TCanvas('c', 'c', 1000, 1000)
        c.SetRightMargin(.12)

        # Prepare new numpy matrix:
        bins1 = (max1 - min1) / step1 + 1
        bins2 = (max2 - min2) / step2 + 1
        d = zeros((bins1, bins2))

        for idac, dac in enumerate(data):
            if dac:
                bin1 = (idac / ((max2 - min2) / step2 + 1))
                bin2 = (idac % ((max2 - min2) / step2 + 1))
                d[bin1][bin2] = dac[0].value

        plot = Plotter.create_th2(d, min1, max1, min2, max2, name, dac1, dac2, 'Efficiency')
        plot.Draw('COLZ')
        plot.SetStats(0)
        self.window = c
        self.Plots.append(plot)
        self.window.Update()

    def do_gui(self, line):
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
        try:
            event = self.api.daqGetRawEvent()
        except RuntimeError:
            return
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
        events = self.converted_raw_event()
        if len(events) == 0:
            raise Exception('Empty Event: %s' % events)
        ub = events[0]
        rocs = sum(1 for ev in events if ev < ub * .75)
        hits = (len(events) - rocs * 3) / 6
        for hit in range(hits):
            for level in range(3, 8):
                events[level + 6 * hit] = self.translate_level(events[level + 6 * hit], events)
        for i in range(len(events)):
            if convert_header and events[i] < ub * 3 / 4:
                events[i], events[i + 1] = self.translate_level(events[i], events, i), self.translate_level(events[i + 1], events, i)
        return events

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
        self.api.testAllPixels(0)
        self.api.maskAllPixels(1)
        self.api.testPixel(row, col, 1, roc)
        self.api.maskPixel(row, col, 0, roc)

    def enable_all(self, roc=None):
        self.api.testAllPixels(1) if roc is None else self.api.testAllPixels(1, roc)
        self.api.maskAllPixels(0) if roc is None else self.api.maskAllPixels(0, roc)

    def vcal_scan(self, vec_ph, average, loops, start=0):
        for vcal in range(256):
            self.api.setDAC("vcal", vcal)
            sum_ph = zeros(80)
            for i in range(average):
                self.api.daqTrigger(1, 500)
                data = self.api.daqGetEvent()
                for j in range(loops):
                    if len(data.pixels) > j:
                        row = data.pixels[i].row
                        sum_ph[row] += data.pixels[i].value
            sum_ph /= average
            for row in range(start, loops + start):
                vec_ph[row].append(sum_ph[row])

    def scan_vcal(self, ctrl_reg, ntrig=10):
        self.api.setDAC('ctrlreg', ctrl_reg)
        for vcal in xrange(0, 256):
            self.api.setDAC('vcal', vcal)
            self.api.daqTrigger(ntrig, 500)
        data = self.api.daqGetEventBuffer()
        values = [[]] * 256
        for i in xrange(256):
            values[i] = [px.value for evt in data[(i * ntrig):((i + 1) * ntrig)] for px in evt.pixels]
        return OrderedDict({vcal: mean(lst) for vcal, lst in enumerate(values) if lst})

    @staticmethod
    def find_factor(low_vals, high_vals):
        gr = TGraph()
        vals = {}
        for i, scale in enumerate(xrange(600, 800)):
            vcals = low_vals.keys() + [scale / 100. * key for key in high_vals.keys()]
            values = low_vals.values() + high_vals.values()
            g = Plotter.create_graph(vcals, values)
            fit = g.Fit('pol1', 'qs', '', vcals[0], low_vals.keys()[-1])
            gr.SetPoint(i, scale / 100., fit.Chi2())
            vals[fit.Chi2()] = scale / 100.
        xmin = vals[min(vals.keys())]
        print xmin

    def trim_ver(self, vec_trim, ntrig, start=0, loops=40):
        for vcal in range(256):
            self.api.setDAC('vcal', vcal)
            ph_ver = zeros(80)
            for i in range(ntrig):
                self.api.daqTrigger(1, 500)
                data = self.api.daqGetEvent()
                for pix in data.pixels:
                    ph_ver[pix.row] += 1
            # stop loop if all thresholds are found
            found_values = True
            for row in range(start, loops + start):
                if int(ph_ver[row]) == ntrig and vec_trim[row + 1] == 0:
                    vec_trim[row + 1] = vcal
            for row in range(start, loops + start):
                if vec_trim[row + 1] == 0:
                    found_values = False
            if found_values:
                break

    def print_activated(self, roc=None):
        active = self.api.getNEnabledPixels() if roc is None else self.api.getNEnabledPixels(roc)
        masked = self.api.getNMaskedPixels() if roc is None else self.api.getNMaskedPixels(roc)
        print 'Pixels active: {n}'.format(n=active)
        print 'Pixels masked: {n}'.format(n=masked)

    def get_activated(self, roc=None):
        return (self.api.getNEnabledPixels(), self.api.getNMaskedPixels()) if roc is None else (self.api.getNEnabledPixels(roc), self.api.getNMaskedPixels(roc))

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

    def eff_check(self, ntrig=10, col=14, row=14, vcal=200):
        print 'checking pixel with col {c} and row {r}'.format(c=col, r=row)
        self.api.HVon()
        self.api.setDAC('vcal', vcal)
        self.enable_pix(col, row)
        self.api.maskAllPixels(0)
        # self.api.maskPixel(51, 79, 1)
        self.api.daqStart()
        self.api.daqTrigger(ntrig, 500)
        data = self.api.daqGetEventBuffer()
        good_events = 0
        for ev in data:
            for px in ev.pixels:
                if ntrig <= 50:
                    print px,
                if px.column == col and px.row == row and len(ev.pixels) == 1:
                    good_events += 1
            if ntrig <= 50:
                print
        eff = 100 * good_events / float(ntrig)
        print '\nEFFICIENCY:\n  {e}/{t} ({p:5.2f}%)'.format(e=good_events, t=ntrig, p=eff)
        # self.api.HVoff()
        # self.api.daqStop()
        return eff

    def getDAC(self, dac, roc_id=0):
        dacs = self.api.getRocDACs(roc_id)
        if dac in dacs:
            return dacs[dac]
        else:
            print 'Unknown dac {d}!'.format(d=dac)

    def maskEdges(self, enable=1, rocid=0):
        for col, row in [(0, 0), (51, 0), (0, 79), (51, 79)]:
            self.api.maskPixel(col, row, enable, rocid)

    def print_eff(self, data, n_trig):
        unmasked = 4160 - self.api.getNMaskedPixels()
        active = self.api.getNEnabledPixels()
        read_back = sum(px.value for px in data)
        total = n_trig * (unmasked if unmasked < active else active)
        eff = 100. * read_back / total
        print 'Efficiency: {eff:6.2f}% ({rb:5d}/{tot:5d})'.format(eff=eff, rb=int(read_back), tot=total)
        return eff

    def dac_dac_scan(self, dac1name="caldel", dac1step=1, dac1min=0, dac1max=255, dac2name="vthrcomp", dac2step=1,
                          dac2min=0, dac2max=255, flags=0, nTriggers=10):
        for roc in xrange(self.api.getNEnabledRocs()):
            self.api.testAllPixels(0)
            self.api.testPixel(14, 14, 1, roc)
            data = self.api.getEfficiencyVsDACDAC(dac1name, dac1step, dac1min, dac1max, dac2name, dac2step, dac2min, dac2max, flags, nTriggers)
            name = '{dac1} vs {dac2} Scan for ROC {roc}'.format(dac1=dac1name.title(), dac2=dac2name.title(), roc=roc)
            self.plot_2d(data, name, dac1name, dac1step, dac1min, dac1max, dac2name, dac2step, dac2min, dac2max)
            self.enable_all(roc)

    def decode_header(self, string):
        num = int('0x' + string, 0)
        print 'Decoding Header:'
        print '    MMMM 0111 1111 10RB'
        bin_str = bin(num).replace('0b', '')
        print 'bin {w}'.format(w=' '.join([bin_str[i:i + 4] for i in xrange(0, len(bin_str), 4)]))
        print 'hex    {w}'.format(w='    '.join(list(string)))
        print 'header identifier: {hi} {eq} 0x7f8'.format(hi=hex(num & 0x0ffc), eq='=' if (num & 0x0ffc) == 0x7f8 else '!=')
        return (num & 0x0ffc) == 0x7f8

    def decode_pixel(self, lst):
        col, row = None, None
        for i in xrange(0, len(lst), 2):
            print '\nDecoding Pixel Hit {n}'.format(n=i / 2 + 1)
            string = lst[i] + lst[i + 1]
            raw = int('0x{s}'.format(s=lst[i] + lst[i + 1]), 0)
            print '    0000 CCC0 CCCR RRR0 MMMM RRRP PPP0 PPPP'
            bin_str = bin(raw).replace('0b', '').zfill(32)
            print 'bin {w}'.format(w=' '.join([bin_str[j:j + 4] for j in xrange(0, len(bin_str), 4)]))
            print 'hex    {w}'.format(w='    '.join(list(string)))
            ph = (raw & 0x0f) + ((raw >> 1) & 0xf0)
            col = ((raw >> 21) & 0x07) + ((raw >> 22) & 0x38)
            row = ((raw >> 9) & 0x07) + ((raw >> 14) & 0x78)
            print '===== [{c}, {r}, {p}] ====='.format(c=col, r=row, p=ph)
            if lst[i + 1].startswith('4'):
                break
        return col, row

    def count_hits(self, duration, wbc):
        t = time()
        counts = 0
        self.api.setDAC('wbc', wbc)
        self.api.daqTriggerSource('async')
        self.api.daqStart()
        while time() - t < duration:
            sleep(.3)
            try:
                data = self.api.daqGetEventBuffer()
                counts += sum(len(ev.pixels) for ev in data)
            except RuntimeError:
                pass
            t1 = duration - time() + t
            print '\rTime left: {m:02d}:{s:02d}\tCounts: {c:05d}'.format(m=int(t1 / 60), s=int(t1 % 60), c=counts),
            sys.stdout.flush()
        self.api.daqStop()
        return counts

    def make_canvas(self):
        c = TCanvas('c', 'c', 1000, 1000)
        self.window = c
        return c

    def mask_frame(self, pix=1):
        self.api.maskAllPixels(1)
        self.api.testAllPixels(1)
        print '--> mask and enable all pixels!'
        for i in range(pix, 52 - pix):
            for j in range(pix, 80 - pix):
                self.api.maskPixel(i, j, 0)
        print '--> masking frame of {n} pixels'.format(n=pix)

    def setPG(self, cal=True, res=True):
        """ Sets up the trigger pattern generator for ROC testing """
        pgcal = self.getDAC('wbc') + (6 if 'dig' in self.api.getRocType() else 5)
        pg_setup = []
        if res:
            pg_setup.append(('PG_RESR', 25))
        if cal:
            pg_setup.append(('PG_CAL', pgcal))
        pg_setup.append(('PG_TRG', 0 if self.api.getNTbms() != 0 else 15))
        if self.api.getNTbms() == 0:
            pg_setup.append(('PG_TOK', 0))
        print pg_setup
        try:
            self.api.setPatternGenerator(tuple(pg_setup))
        except RuntimeError, err:
            print err

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

    @arity(0, 1, [int])
    def do_setOffset(self, os):
        """setOffset"""
        self.api.setDecodingOffset(os)

    def complete_setOffset(self):
        # return help for the cmd
        return [self.do_setOffset.__doc__, '']

    @arity(0, 0, [])
    def do_getTBid(self):
        """getTBia: returns analog DTB current"""
        print "Digital Current: ", (self.api.getTBid() * 1000), " mA"

    def complete_getTBid(self):
        # return help for the cmd
        return [self.do_getTBid.__doc__, '']

    @arity(0, 1, [int])
    def do_setExternalClock(self, enable=1):
        """setExternalClock [enable]: enables the external DTB clock input, switches off the internal clock. Only switches if external clock is present."""
        if self.api.setExternalClock(enable) is True:
            print "Switched to " + ("external" if enable else "internal") + " clock."
        else:
            print "Could not switch to " + ("external" if enable else "internal") + " clock!"

    def complete_setExternalClock(self):
        # return help for the cmd
        return [self.do_setExternalClock.__doc__, '']

    @arity(0, 2, [int, int])
    def do_setPG(self, cal=True, res=True):
        """setPG [enable]: enables the external DTB clock input, switches off the internal clock. Only switches if external clock is present."""
        self.setPG(cal, res)

    def complete_setPG(self):
        # return help for the cmd
        return [self.do_setPG.__doc__, '']

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
        self.api.daqStart(0)

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
    def do_maskEdges(self, enable=1, rocid=None):
        """maskEdges [enable] [rocid]: mask/unmask all pixels on given ROC"""
        self.maskEdges(enable, rocid)

    def complete_maskEdges(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_maskEdges.__doc__, '']

    @arity(0, 2, [int, int])
    def do_getEfficiencyMap(self, flags=0, nTriggers=10):
        """getEfficiencyMap [flags = 0] [nTriggers = 10]: returns the efficiency map"""
        # self.window = PxarGui(ROOT.gClient.GetRoot(), 1000, 800)
        data = self.api.getEfficiencyMap(flags, nTriggers)
        self.print_eff(data, nTriggers)
        self.plot_map(data, "Efficiency", no_stats=True)

    def complete_getEfficiencyMap(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_getEfficiencyMap.__doc__, '']

    @arity(0, 2, [int, int])
    def do_getXPixelAlive(self, nTriggers=50):
        """getxPixelAlive [flags = 0] [nTriggers = 10]: returns the efficiency map"""
        data = self.api.getEfficiencyMap(896, nTriggers)
        self.print_eff(data, nTriggers)
        self.plot_map(data, "Efficiency", no_stats=True)

    def complete_getXPixelAlive(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_getXPixelAlive.__doc__, '']

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

    @arity(0, 10, [int, str, int, int, int, str, int, int, int, int])
    def do_dacDacScan(self, nTriggers=10, dac1name="caldel", dac1step=1, dac1min=0, dac1max=255, dac2name="vthrcomp", dac2step=1,
                      dac2min=0, dac2max=255, flags=0):
        """getEfficiencyVsDACDAC [DAC1 name] [step size 1] [min 1] [max 1] [DAC2 name] [step size 2] [min 2] [max 2] [flags = 0] [nTriggers = 10]
        return: the efficiency over a 2D DAC1-DAC2 scan"""
        self.dac_dac_scan(dac1name, dac1step, dac1min, dac1max, dac2name, dac2step,
                      dac2min, dac2max, flags, nTriggers)

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

    @arity(0, 9, [int, str, int, int, int, str, int, int, int])
    def do_xdacDacScan(self, nTriggers=10, dac1name="caldel", dac1step=1, dac1min=0, dac1max=255, dac2name="vthrcomp", dac2step=1,
                      dac2min=0, dac2max=255):
        """getEfficiencyVsDACDAC with unmasked ROC"""
        self.dac_dac_scan(dac1name, dac1step, dac1min, dac1max, dac2name, dac2step, dac2min, dac2max, flags=896, nTriggers=nTriggers)

    def complete_xdacDacScan(self):
        return [self.do_xdacDacScan.__doc__, '']

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
    def do_getStatistics(self):
        """getStatistics: print full statistics accumulated during last DAQ session"""
        data = self.api.getStatistics()
        data.dump

    def complete_getStatistics(self):
        # return help for the cmd
        return [self.do_getStatistics.__doc__, '']

    @arity(0, 0, [])
    def do_daqGetBuffer(self):
        """daqGetBuffer: read full raw data DTB buffer"""
        try:
            dat = self.api.daqGetBuffer()
            s = ""
            for i in dat:
                if i & 0x0FF0 == 0x07f0:
                    s += "\n"
                    s += '{:04x}'.format(i) + " "
                    print s
        except RuntimeError:
            pass

    def complete_daqGetBuffer(self):
        # return help for the cmd
        return [self.do_daqGetBuffer.__doc__, '']

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

    def complete_daqGetEventBuffer(self):
        # return help for the cmd
        return [self.do_daqGetEventBuffer.__doc__, '']

    @arity(0, 0, [])
    def do_daqStatus(self):
        """daqStatus: reports status of the running DAQ session"""
        if self.api.daqStatus():
            print "DAQ session is fine"
        else:
            print "DAQ session returns faulty state"

    def complete_daqStatus(self):
        # return help for the cmd
        return [self.do_daqStatus.__doc__, '']

    @arity(1, 2, [list, int])
    def do_update_trim_bits(self, trim_list, roc_i2c):
        self.api.updateTrimBits(self, trim_list, roc_i2c)

    def complete_update_trim_bits(self):
        # return help for the cmd
        return [self.do_update_trim_bits.__doc__, '']

    @arity(0, 1, [int])
    def do_getRocDacs(self, roc_id=0):
        """ shows the current settings for dacs"""
        for dac, value in self.api.getRocDACs(roc_id).iteritems():
            print dac, value

    def complete_getRocDacs(self):
        # return help for the cmd
        return [self.do_getRocDacs.__doc__, '']

    @arity(1, 2, [str, int])
    def do_getDAC(self, dac, roc_id=0):
        """ shows the current settings for dacs"""
        print '{d}: {v}'.format(d=dac, v=self.getDAC(dac, roc_id))

    def complete_getDAC(self):
        # return help for the cmd
        return [self.do_getDAC.__doc__, '']

    @arity(0, 1, [str])
    def do_getTestboardDelays(self, delay=None):
        """ shows the current settings for dacs"""
        for dac, value in self.api.getTestboardDelays().iteritems():
            print dac, value

    def complete_getTestboardDelays(self):
        # return help for the cmd
        return [self.do_getTestboardDelays.__doc__, '']

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
    def do_setClockDelays(self, value):
        """SetClockDelays [value of clk and ctr]: sets the two TB delays clk and ctr """
        print "TB delays clk and ctr set to: ", value
        self.set_clock(value)

    def complete_setClockDelays(self):
        # return help for the cmd
        return [self.do_setClockDelays.__doc__, '']

    @arity(0, 3, [int, int, int])
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
        print "get level splitting:"
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
                        except (IndexError, TypeError):
                            spread_j = 99
                            break
                    sum_spread += spread_j / 5
                    # level split
                    stop_loop = False
                    for j in range(len(cols)):
                        try:
                            mean_value[roc][j] += event[5 + roc * 3 + j * 6]
                        except (IndexError, TypeError):
                            mean_value[roc][j] = 0
                            stop_loop = True
                            break
                    if stop_loop:
                        break
                spread_black[roc].append(sum_spread / float(n_triggers))
                for i in range(n_levels):
                    levels_y[roc][i].append(mean_value[roc][i] / float(n_triggers))
                print '\rclk-delay:', "{0:2d}".format(clk), 'black lvl spread: ', "{0:2.2f}".format(spread_black[roc][clk]),
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
                best_clk = i
        print
        print 'best clk: ', best_clk
        names = ['clk\t\t\t', 'level spread:\t\t', 'black level spread:\t']
        infos = [clk_x, spread, spread_black[0]]
        for i in range(3):
            print names[i],
            for j in range(-2, 3):
                if not i:
                    print infos[i][best_clk + j], '\t',
                else:
                    print '{0:2.2f}'.format(infos[i][best_clk + j]), '\t',
            print
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

    def complete_analogLevelScan(self):
        # return help for the cmd
        return [self.do_analogLevelScan.__doc__, '']

    @arity(0, 0, [])
    def do_enableAllPixel(self):
        """enableAllPixel: enables and unmasks all Pixels"""
        self.api.maskAllPixels(0)
        self.api.testAllPixels(1)

    def complete_enableAllPixel(self):
        # return help for the cmd
        return [self.do_enableAllPixel.__doc__, '']

    @arity(0, 1, [int])
    def do_print_activated_pixels(self, roc=0):
        """print_activated_pixels: prints which pixels are activated"""
        print self.print_activated(roc)

    def print_activated_pixels(self):
        # return help for the cmd
        return [self.do_print_activated_pixels.__doc__, '']

    @arity(0, 3, [int, int, int])
    def do_enableOnePixel(self, row=14, column=14, roc=None):
        """enableOnePixel [row] [column] [roc] : enables one Pixel (default 14/14); masks and disables the rest"""
        if roc is None:
            self.api.testAllPixels(0)
            self.api.maskAllPixels(1)
            self.api.testPixel(row, column, 1)
            self.api.maskPixel(row, column, 0)
        else:
            self.api.testAllPixels(0, roc)
            self.api.maskAllPixels(1, roc)
            self.api.testPixel(row, column, 1, roc)
            self.api.maskPixel(row, column, 0, roc)
        print '--> disable and mask all pixels of all activated ROCs'
        print_string = '--> enable and unmask Pixel {r}/{c}: '.format(r=row, c=column)
        print_string += '(' + ','.join('ROC {n}: {a}/{m}'.format(n=roc, a=self.get_activated(roc)[0], m=self.get_activated(roc)[1]) for roc in xrange(self.api.getNEnabledRocs())) + ')'
        print print_string

    def complete_enableOnePixel(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_enableOnePixel.__doc__, '']

    @arity(0, 4, [int, int, int, int])
    def do_enableBlock(self, right=3, up=None, row=3, col=3):
        """enableBlock [right=3] [up=right] [row=3] [col=3] : unmask all Pixels; starting from row and col enable block of size up * right"""
        up = right if up is None else up
        self.api.maskAllPixels(0)
        self.api.testAllPixels(1)
        print '--> mask and enable all pixels!'
        for i in range(right):
            for j in range(up):
                self.api.maskPixel(i + col, j + row, 1)
        print '--> unmask Block from {c}/{r} to {c1}/{r1}'.format(c=col, r=row, c1=col + right, r1=row + up)
        self.print_activated()

    def complete_enableBlock(self):
        return [self.do_enableBlock.__doc__, '']
    
    @arity(0, 4, [int, int, int, int])
    def do_maskFrame(self, pix=1):
        """maskFrame [pix=1] : masking outer frame with equal pixel distance"""
        self.mask_frame(pix)
        self.print_activated()

    def complete_maskFrame(self):
        return [self.do_maskFrame.__doc__, '']

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
        """PixelActive : shows how many Pixels are active and how many masked"""
        active = self.api.getNEnabledPixels()
        masked = self.api.getNMaskedPixels()
        print 'Pixel{s} active: {n}'.format(s='s' if active > 1 else ' ', n=active)
        print 'Pixel{s} masked: {n}'.format(s='s' if masked > 1 else ' ', n=masked)

    def complete_PixelActive(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_PixelActive.__doc__, '']


    @arity(0, 0, [])
    def do_findAnalogueTBDelays(self):
        """findAnalogueTBDelays: configures tindelay and toutdelay"""
        self.api.setTestboardDelays({'tindelay': 0, 'toutdelay': 20})
        self.enable_all()
        old_vcal = self.getDAC('vcal')
        self.api.setDAC('vcal', 0)
        data = self.daq_converted_raw()
        tin = data.index([word for word in data if word < -100][0])
        data.reverse()
        tout = 20 - data.index([word for word in data if word > 3 * abs(mean(data[:5]))][0])

        self.api.setDAC('vcal', old_vcal)
        self.api.setTestboardDelays({'tindelay': tin, 'toutdelay': tout})
        print 'set tindelay to:  ', tin
        print 'set toutdelay to: ', tout

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
        f.close()

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
        
        print 'Turning on HV! YES I DID IT :D'
        self.api.HVon()
        self.api.daqTriggerSource("extern")
        rocs = self.api.getNEnabledRocs()
        wbc_scan = []
        wbc_values = []
        roc_hits = []
        best_wbc = None
        trigger_phase = []
        for i in range(10):
            trigger_phase.append(0)
        print "wbc \tyield"

        # loop over wbc
        for wbc in range(min_wbc, max_wbc):
            self.api.setDAC("wbc", wbc)
            self.api.daqStart()
            wbc_values.append(wbc)
            hits = 0
            triggers = 0
            roc_hits.append([])
            for i in range(rocs):
                roc_hits[wbc - min_wbc].append(0)

            # loop until you find nTriggers
            while triggers < max_triggers:
                try:
                    data = self.api.daqGetEvent()
                    if len(data.pixels) > 0:
                        hits += 1
                    found_roc = []
                    for i in range(rocs):
                        found_roc.append(False)
                    for i in range(len(data.pixels)):
                        roc = data.pixels[i].roc
                        if not found_roc[roc]:
                            roc_hits[wbc - min_wbc][roc] += 1
                            found_roc[roc] = True
                    triggers += 1
                except RuntimeError:
                    pass

            hit_yield = 100 * hits / max_triggers
            wbc_scan.append(hit_yield)
            print '{0:03d}'.format(wbc), "\t", '{0:3.0f}%'.format(hit_yield)

            # stopping criterion
            if wbc > 3 + min_wbc:
                if wbc_scan[-4] > 50:
                    best_wbc = wbc - 3
                    print "Set DAC wbc to", wbc - 3
                    self.api.setDAC("wbc", wbc - 3)
                    break

            # Clear the buffer:
            try:
                self.api.daqGetEventBuffer()
            except RuntimeError:
                pass

        stop = 0
        while stop < 1000:
            bla = self.converted_raw_event()
            if len(bla) > 2:
                for i in range(10):
                    if bla[1] == i:
                        trigger_phase[i] += 1
                stop += 1

        self.api.daqStop()

        if best_wbc == None:
            last_wbc = 0
            for i in range(len(wbc_scan)):
                if wbc_scan[i] < last_wbc and last_wbc > 10:
                    best_wbc = wbc_values[i - 1]
                    break
                last_wbc = wbc_scan[i]
            if best_wbc != None:
                print "Set DAC wbc to", best_wbc
                self.api.setDAC("wbc", best_wbc)

        # roc statistics
        print "\nROC STATISTICS:"
        print 'wbc\t',
        for i in range(rocs):
            print 'roc' + str(i) + '\t',
        print
        for i in range(-4, 4):
            print best_wbc + i, '\t',
            for j in range(rocs):
                print "{0:2.1f}".format(roc_hits[best_wbc - min_wbc + i][j] / float(max_triggers) * 100), '\t',
            print

        # triggerphase
        print '\nTRIGGER PHASE:'
        for i in range(len(trigger_phase)):
            if trigger_phase[i]:
                print i, '\t', trigger_phase[i] / 20 * '|', "{0:2.1f}%".format(trigger_phase[i] / float(10))


        # plot wbc_scan
        self.window = TCanvas('c', 'c', 1000, 1000)
        plot = Plotter.create_tgraph(wbc_scan, "wbc scan", "wbc", "evt/trig [%]", min_wbc)
        self.Plots.append(plot)
        plot.Draw('ap')

    def complete_wbcScan(self):
        # return help for the cmd
        return [self.do_wbcScan.__doc__, '']

    @arity(0, 4, [int, int, int, str])
    def do_latencyScan(self, minlatency=75, maxlatency=85, triggers=50, triggersignal="extern"):
        """ do_latencyScan [min] [max] [triggers] [signal]: scan the trigger latency from min to max with set number of triggers)"""

        self.api.testAllPixels(0, None)
        self.api.HVon()

        latencyScan = []
        print "latency \tyield"

        # loop over latency
        for latency in range(minlatency, maxlatency):
            delay = {}
            delay["triggerlatency"] = latency
            self.api.setTestboardDelays(delay)
            self.api.daqTriggerSource(triggersignal)
            self.api.daqStart()
            nHits = 0
            nTriggers = 0

            # loop until you find maxTriggers
            while nTriggers < triggers:
                try:
                    data = self.api.daqGetEvent()
                    if len(data.pixels) > 0:
                        rocs = []
                        for i in range(len(data.pixels)):
                            rocs.append(data.pixels[i].roc)
                        if 1 in rocs and 2 in rocs:
                            nHits += 1
                    nTriggers += 1
                except RuntimeError:
                    pass

            hitYield = 100 * nHits / triggers
            latencyScan.append(hitYield)
            print '{0:03d}'.format(latency), "\t", '{0:3.0f}%'.format(hitYield)
            self.api.daqStop()

        if (self.window):
            self.window = PxarGui(ROOT.gClient.GetRoot(), 1000, 800)
            plot = Plotter.create_tgraph(latencyScan, "latency scan", "trigger latency", "evt/trig [%]", minlatency)
            self.window.histos.append(plot)
            self.window.update()

    def complete_latencyScan(self, text, line, start_index, end_index):
        # return help for the cmd
        return [self.do_latencyScan.__doc__, '']

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
        """ do_hitMap [maxTriggers]: collects a certain amount triggers and plots a hitmap"""

        self.api.daqTriggerSource('extern')
        self.api.setDAC('wbc', 93)
        self.api.HVon()
        windowsize = 100
        t = time()
        self.api.daqStart()

        # check if module is True
        module = True
        while True:
            try:
                data = self.api.daqGetEvent().pixels
                if len(data) > 0:
                    if data[0].roc == 0:
                        module = False
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

        print "\ntest took: ", round(time() - t, 2), "s"
        plot = Plotter.create_th2(d, 0, 417 if module else 53, 0, 161 if module else 81, "hitmap", 'pixels x',  'pixels y', "hitmap")
        self.plot_graph(plot, draw_opt='hist')

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

    @arity(0, 3, [int, int, int])
    def do_trim_verification(self,a=0,b=52, ntrig=10):
        start_time = time()


        vcal_thresh = zeros((53, 81))

        for col in range(a, b):
            # first half col
            self.api.testAllPixels(0)
            self.api.maskAllPixels(1)
            for row in range(40):
                self.api.testPixel(col, row, 1)
                self.api.maskPixel(col, row, 0)
            self.api.daqStart()
            self.api.setDAC('ctrlreg', 0)
            self.trim_ver(vcal_thresh[col + 1], ntrig)
            for row in range(40):
                print '\r', '{0:2.2f}%'.format((col + float(row) / 80) / float(52) * 100),
                sys.stdout.flush()
            self.api.daqStop()
            # second half col
            self.api.testAllPixels(0)
            self.api.maskAllPixels(1)
            for row in range(40, 80):
                self.api.testPixel(col, row, 1)
                self.api.maskPixel(col, row, 0)
            self.api.daqStart()
            self.api.setDAC('ctrlreg', 0)
            self.trim_ver(vcal_thresh[col + 1], ntrig, 40)
            for row in range(40, 80):
                print '\r', '{0:2.2f}%'.format((col + float(row) / 80) / float(52) * 100),
                sys.stdout.flush()
            self.api.daqStop()

        self.window = PxarGui(ROOT.gClient.GetRoot(), 1000, 800)
        plot = Plotter.create_th2(vcal_thresh, 0, 52, 0, 80, 'trim verfication', 'col', 'row', 'thresh')
        self.window.histos.append(plot)
        self.window.update()
        self.elapsed_time(start_time)

    @arity(0, 3, [int, str, int])
    def do_ph_vs_vcal(self, average=10, name='ph.cal', do_plot=False):
        start_time = time()



        f = open(name, 'w')

        # create vectors
        ph_y = []
        vcal_high_x = []
        vcal_low_x = []
        for vcal in range(256):
            vcal_high_x.append(vcal * 7)
            vcal_low_x.append(vcal)
        for col in range(52):
            ph_y.append([])
            for row in range(80):
                ph_y[col].append([])

        for col in range(52):
            # first half col
            self.api.testAllPixels(0)
            self.api.maskAllPixels(1)
            for row in range(40):
                self.api.testPixel(col, row, 1)
                self.api.maskPixel(col, row, 0)
            self.api.daqStart()
            self.api.setDAC('ctrlreg', 0)
            self.vcal_scan(ph_y[col], average, 40)
            self.api.setDAC('ctrlreg', 4)
            self.vcal_scan(ph_y[col], average, 40)
            for row in range(40):
                print '\r', '{0:2.2f}%'.format((col + float(row) / 80) / float(52) * 100),
                sys.stdout.flush()
                f.write('Pix ' + str(col) + ' ' + str(row) + ' ')
                for val in ph_y[0][row]:
                    f.write(str(val) + ' ')
                f.write('\n')
            self.api.daqStop()
            # second half col
            self.api.testAllPixels(0)
            self.api.maskAllPixels(1)
            for row in range(40, 80):
                self.api.testPixel(col, row, 1)
                self.api.maskPixel(col, row, 0)
            self.api.daqStart()
            self.api.setDAC('ctrlreg', 0)
            self.vcal_scan(ph_y[col], average, 40, 40)
            self.api.setDAC('ctrlreg', 4)
            self.vcal_scan(ph_y[col], average, 40, 40)
            for row in range(40, 80):
                print '\r', '{0:2.2f}%'.format((col + float(row) / 80) / float(52) * 100),
                sys.stdout.flush()
                f.write('Pix ' + str(col) + ' ' + str(row) + ' ')
                for val in ph_y[0][row]:
                    f.write(str(val) + ' ')
                f.write('\n')
            self.api.daqStop()
        print
        f.close()

        if do_plot:
            # plot ph vs vcal
            # self.window = PxarGui(ROOT.gClient.GetRoot(), 1000, 800)
            plot = Plotter.create_tgraph(ph_y[0][20], "ph scan", "vcal", "ph", 0, vcal_high_x)
            plot.SetMarkerSize(0.5)
            plot.SetMarkerStyle(20)
            plot2 = Plotter.create_tgraph(ph_y[0][40],"ph scan", "vcal", "ph", 0, vcal_high_x)
            plot2.SetMarkerSize(0.5)
            plot2.SetMarkerStyle(20)
            plot2.SetMarkerColor(3)
            c1 = ROOT.TCanvas('c1', 'c1', 800, 800)
            c1.DrawFrame(0, 0, 1900, 200)
            plot.Draw('P')
            plot2.Draw('P')
            c1.Update()
            raw_input()
            # f1 = ROOT.TH1.pol1
            # plot.Fit(fit, 'Q')
            # self.window.histos.append(plot)
            # self.window.histos.append(plot2)
            # self.window.update()
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
        black_dev2 = []
        black_real = []
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
                    black_dev2[roc][adr] += val * val
        for roc in range(rocs):
            print roc, ":",
            for i in range(len(black_dev[roc])):
                mean = black_dev[roc][i] / avg
                # mean2 = black_dev2[roc][i]/ avg - mean * mean
                # mean2 = math.sqrt(mean2)
                print mean
            print
        # for r in black_real[roc]:
        #     print r,
        # print

        self.api.daqStop()

    def complete_do_adjust_black(self):
        # return help for the cmd
        return [self.do_adjust_black.__doc__, '']

    @arity(0, 2, [int, str])
    def do_marie_can_save(self, events=1000, filename=None):
        """
        Saves <n> events to file
        :param events:\t number of saved events
        :param filename:
        """
        if filename is None:
            filename = 'saved_events_' + strftime('%H:%M:%S_%d.%m.')
        conf_triggers = 0
        hits = 0
        f = open(filename, 'w')

        self.api.daqStart()
        while conf_triggers < events:
            try:
                data = self.api.daqGetEvent()
                f.write(str(data) + '\n')
                if len(data.pixels) > 0:
                    hits += 1
                print '\rprocess:', '{0:6d}'.format(conf_triggers) + '/' + str(events),
                sys.stdout.flush()
                conf_triggers += 1
            except RuntimeError:
                pass
        self.api.daqStop()
        print '\rhit yield:', "{0:5.2f}%".format(hits / float(events) * 100), '({hits}/{events})'.format(hits=hits, events=events)
        f.close()

    def complete_marie_can_save(self):
        # return help for the cmd
        return [self.do_marie_can_save.__doc__, '']

    @arity(0, 2, [int, int])
    def do_checkADCTimeConstant(self, vcal=200, ntrig=10):
        """ checkADCTimeConstant [vcal=200] [ntrig=10]: sends an amount of triggers for a fixed vcal in high/low region and prints adc values"""
        self.api.setDAC('vcal', vcal)
        self.enable_pix(14, 14)
        self.api.daqStart()
        for ctrl_reg in [0, 4]:
            print 'ctrlreg:', ctrl_reg
            self.api.setDAC('ctrlreg', ctrl_reg)
            sleep(.5)
            trig = 0
            n_err = 0
            while trig < ntrig and n_err < 100:
                try:
                    self.api.daqTrigger(1, 500)
                    data = self.api.daqGetEvent()
                    if len(data.pixels):
                        print '{0:4d}'.format(int(data.pixels[0].value))
                        trig += 1
                    else:
                        n_err += 1
                except Exception as err:
                    n_err += 1
                    print err
        self.api.daqStop()

    def complete_checkADCTimeConstant(self):
        # return help for the cmd
        return [self.do_checkADCTimeConstant.__doc__, '']

    @arity(0, 4, [int, int, int, int])
    def do_efficiency_check(self, ntrig=10, col=14, row=14, vcal=200):
        """ checkADCTimeConstant [vcal=200] [ntrig=10]: sends an amount of triggers for a fixed vcal in high/low region and prints adc values"""
        self.eff_check(ntrig, col, row, vcal)
        self.api.daqStop()

    def complete_efficiency_check(self):
        # return help for the cmd
        return [self.do_efficiency_check.__doc__, '']

    @arity(2, 2, [int, int])
    def do_setZaxis(self, low, high):
        """ checkADCTimeConstant [vcal=200] [ntrig=10]: sends an amount of triggers for a fixed vcal in high/low region and prints adc values"""
        c = gROOT.GetListOfCanvases()[-1]
        for item in c.GetListOfPrimitives():
            if item.GetName() not in ['TFrame', 'title']:
                item.GetZaxis().SetRangeUser(low, high)
                break

    def complete_setZaxis(self):
        return [self.do_setZaxis.__doc__, '']

    @arity(2, 7, [int, int, str, int, int, int, int])
    def do_efficiency_scan(self, start, stop, dac_str='vana', ntrig=100, col=14, row=14, vcal=200):
        """ checkADCTimeConstant [vcal=200] [ntrig=10]: sends an amount of triggers for a fixed vcal in high/low region and prints adc values"""
        efficiencies = []
        for dac in xrange(start, stop):
            print '\rmeasuring {1}: {0:3d}'.format(dac, dac_str),
            self.api.setDAC(dac_str, dac)
            efficiencies.append(self.eff_check(ntrig, col, row, vcal if dac_str != 'vcal' else dac))
        print
        gr = Plotter.create_graph(range(start, stop), efficiencies, 'Efficiency Vs {0}'.format(dac_str.title()), '{d} [dac]'.format(d=dac_str), 'Efficiency [%]')
        self.plot_graph(gr)
        self.api.daqStop()

    def complete_efficiency_scan(self):
        # return help for the cmd
        return [self.do_efficiency_scan.__doc__, '']

    @arity(0, 3, [int, int, int])
    def do_findThreshold(self, col=14, row=14, ntrig=1000):
        """ checkADCTimeConstant [vcal=200] [ntrig=10]: sends an amount of triggers for a fixed vcal in high/low region and prints adc values"""
        self.enable_pix(row, col)
        self.api.daqStart()
        vanas = range(55, 110)
        thresholds = []
        for vana in vanas:
            self.api.setDAC('vana', vana)
            for vcal in xrange(0, 256):
                print '\rscanning vcal for vana: {1} {0:3d}'.format(vcal, vana),
                self.api.setDAC('vcal', vcal)
                self.api.daqTrigger(ntrig, 500)
                good_events = 0
                for i in xrange(ntrig):
                    good_events += bool(self.api.daqGetEvent().pixels)
                eff = good_events / float(ntrig)
                # eff = sum(1 for ev in self.api.daqGetEventBuffer() if ev.pixels) / float(ntrig)
                print '{0:4.2f}%'.format(eff),
                stdout.flush()
                if eff > .99:
                    thresholds.append(vcal)
                    break
                if vcal == 255 and eff < .99:
                    thresholds.append(0)
        print
        gr = Plotter.create_graph(vanas, thresholds, 'Vana vs. Threshold (trimmed to 40 vcal)', 'vana [dac]', 'measured threshold [vcal]')
        self.plot_graph(gr)
        self.api.daqStop()

    def complete_findThreshold(self):
        # return help for the cmd
        return [self.do_findThreshold.__doc__, '']

    @arity(0, 3, [int, int, int])
    def do_noisemap(self, col=14, row=14, ntrig=1000):
        """ checkADCTimeConstant [vcal=200] [ntrig=10]: sends an amount of triggers for a fixed vcal in high/low region and prints adc values"""
        self.enable_pix(row, col)
        self.api.maskAllPixels(0)
        self.api.daqStart()
        self.api.daqTrigger(ntrig, 500)
        d = self.api.daqGetEventBuffer()
        data = zeros((52, 80))
        for ev in d:
            for px in ev.pixels:
                data[px.column][px.row] += 1
        th2d = Plotter.create_th2(data, 0, 52, 0, 80, 'Noise Map for Pix {c} {r}'.format(r=row, c=col), 'col', 'row', 'hits')
        th2d.SetStats(0)
        self.plot_graph(th2d, .1, .14, 'colz')
        self.api.daqStop()

    def complete_noisemap(self):
        # return help for the cmd
        return [self.do_noisemap.__doc__, '']

    @arity(0, 0, [])
    def do_anaCurrent(self):
        """ checkADCTimeConstant [vcal=200] [ntrig=10]: sends an amount of triggers for a fixed vcal in high/low region and prints adc values"""
        old_vana = self.getDAC('vana')
        vanas = range(255)
        ianas = []
        for vana in vanas:
            self.api.setDAC('vana', vana)
            sleep(.01)
            iana = mean([self.api.getTBia() for _ in xrange(10)]) * 1000
            ianas.append(iana)
        gr = Plotter.create_graph(vanas, ianas, 'Analogue Current', 'vana [dac]', 'iana [mA]')
        self.plot_graph(gr)
        self.api.setDAC('vana', old_vana)

    def complete_anaCurrent(self):
        # return help for the cmd
        return [self.do_anaCurrent.__doc__, '']

    def do_decode_linear(self, sample):
        words = sample.split(' ')
        headers = 0
        good_headers = 0
        i = 0
        pixels = {}
        while i < len(words):
            if words[i][0] in ['8', 'c']:
                headers += 1
                good_headers += self.decode_header(words[i])
            else:
                col, row = self.decode_pixel(words[i:])
                string = '{c} {r}'.format(c=col, r=row)
                if string not in pixels:
                    pixels[string] = 0
                pixels[string] +=1
                i +=1
            i += 1
        print 'Good Headers: {p:4.1f}% ({g}/{h})'.format(p=good_headers / float(headers) * 100, g=good_headers, h=headers)
        for key, word in pixels.iteritems():
            print 'Pixel', key, word

    def complete_decode_linear(self):
        return [self.do_decode_linear.__doc__, '']

    @arity(0, 2, [int, int])
    def do_countHits(self, duration=30, wbc=110):
        counts = self.count_hits(duration, wbc)
        print '\n\nTotal Count after {t} seconds: {c}'.format(t=duration, c=counts)

    def complete_countHits(self):
        return [self.do_countHits.__doc__, '']

    @arity(0, 3, [int, int, int])
    def do_calcHighVcal(self, col=14, row=14, ntrig=10):
        self.api.HVon()
        self.enable_pix(col, row)
        self.api.daqStart()
        data_low = self.scan_vcal(0, ntrig)
        data_high = self.scan_vcal(4, ntrig)
        self.find_factor(data_low, data_high)

    def complete_calcHighVcal(self):
        return [self.do_calcHighVcal.__doc__, '']

    @arity(0, 3, [int, int, int])
    def do_scanVcal(self, col=14, row=14, ntrig=10):
        self.api.HVon()
        self.enable_pix(col, row)
        self.api.daqStart()
        data_low = self.scan_vcal(0, ntrig)
        data_high = self.scan_vcal(4, ntrig)
        gr1 = Plotter.create_graph(data_low.keys(), data_low.values(), 'gr1', xtit='vcal', ytit='adc')
        gr2 = Plotter.create_graph(data_high.keys(), data_high.values(), 'gr2', xtit='vcal', ytit='adc')
        gr1.SetLineColor(3)
        gr1.SetMarkerColor(3)
        mg = TMultiGraph()
        mg.Add(gr2)
        mg.Add(gr1)
        self.plot_graph(mg)

    def complete_scanVcal(self):
        return [self.do_scanVcal.__doc__, '']

    @arity(2, 4, [int, int, int, int])
    def do_threshVsCounts(self, start, stop, duration=10, wbc=110):
        gr = TGraph()
        for i, vthr in enumerate(xrange(start, stop)):
            self.api.setDAC('vthrcomp', vthr)
            counts = self.count_hits(duration, wbc)
            gr.SetPoint(i, vthr, counts)
        self.make_canvas()
        self.Plots.append(gr)
        gr.SetMarkerStyle(20)
        gr.Draw('alp')

    def complete_threshVsCounts(self):
        return [self.do_threshVsCounts.__doc__, '']

    @arity(0, 2, [int, int])
    def do_effVsMaskedPix(self, n=5, n_trig=100):
        gr = TGraph()
        for i in xrange(n):
            self.mask_frame(i)
            data = self.api.getEfficiencyMap(896, n_trig)
            eff = self.print_eff(data, n_trig)
            unmasked = 4180 - self.api.getNMaskedPixels()
            gr.SetPoint(i, unmasked, eff)
        self.make_canvas()
        self.Plots.append(gr)
        gr.SetMarkerStyle(20)
        gr.Draw('alp')

    def complete_effVsMaskedPix(self):
        return [self.do_effVsMaskedPix.__doc__, '']

    @arity(0, 2, [float])
    def do_findErrors2(self, t=1, n=10000):
        self.api.HVon()
        t_start = time()
        self.setPG(cal=False, res=False)
        self.api.daqStart()
        self.start_pbar(t * 600)
        while time() - t_start < t * 60:
            self.ProgressBar.update(int((time() - t_start) * 10) + 1)
            self.api.daqTrigger(n, 500)
            self.api.daqGetEventBuffer()
        self.ProgressBar.finish()
        self.api.daqStop()
        self.api.HVoff()
        self.setPG()
        stats = self.api.getStatistics()
        stats.dump

    def complete_findErrors2(self):
        return [self.do_findErrors2.__doc__, '']

    @arity(0, 1, [float])
    def do_findErrors(self, t=1):
        t_start = time()
        errors = [0] * 4
        n_triggers = 0
        while time() - t_start < t * 60:
            self.api.getEfficiencyMap(0, 10)
            n_triggers += 41600
            stats = self.api.getStatistics()
            errors[0] += stats.errors_event
            errors[1] += stats.errors_tbm
            errors[2] += stats.errors_roc
            errors[3] += stats.errors_pixel
        print 'Number of triggers: ', n_triggers
        print 'Number of triggers per pixel: ', n_triggers / 4160
        print 'Errors: ', errors

    def complete_findErrors(self):
        return [self.do_findErrors.__doc__, '']

    @arity(0, 2, [float, int])
    def do_findErrors1(self, t=1, n=10000):
        self.api.HVon()
        t_start = time()
        self.api.testAllPixels(0)
        gRandom.SetSeed(int(time()))
        for roc in xrange(self.api.getNRocs()):
            for _ in xrange(1):
                col, row = [int(gRandom.Rndm() * i) for i in [52, 80]]
                print col, row
                self.api.testPixel(col, row, 1, roc)
        self.api.daqStart()
        self.start_pbar(t * 600)
        n_trig = 0
        while time() - t_start < t * 60:
            self.ProgressBar.update(int((time() - t_start) * 10) + 1)
            self.api.daqTrigger(n, 500)
            n_trig += n
            self.api.daqGetEventBuffer()
        self.ProgressBar.finish()
        self.api.daqStop()
        self.api.HVoff()
        stats = self.api.getStatistics()
        print 'Triggers: {n}'.format(n=n_trig)
        stats.dump

    def complete_findErrors1(self):
        return [self.do_findErrors1.__doc__, '']

    @arity(0, 1, [int])
    def do_getTriggerPhase(self, n_events=100):
        events = 0
        gROOT.ProcessLine("gErrorIgnoreLevel = kError;")
        h = TH1I('h_tp', 'Trigger Phases', 10, 0, 10)
        h.GetXaxis().SetTitle('Trigger Phase')
        self.api.daqTriggerSource('extern')
        self.api.daqStart()
        t = time()
        values = []
        while n_events > events:
        # while time() - t < 30:
            event = self.converted_raw_event()
            if event is not None:
                p.update(events + 1)
                # print '{0:05d}/{1:05d}'.format(events, n_events)
                events += 1
                values.append(event[1])
                h.Fill(event[1])
        print
        print values
        self.api.daqStop()
        h.GetYaxis().SetRangeUser(0, h.GetMaximum() * 1.1)
        self.plot_graph(h, draw_opt='hist')

    def complete_getTriggerPhase(self):
        return [self.do_getTriggerPhase.__doc__, '']

    @staticmethod
    def do_quit(q=1):
        """quit: terminates the application"""
        sys.exit(q)

    do_exit = do_quit

    # shortcuts
    do_q = do_quit
    do_a = do_analogLevelScan
    do_sd = do_set_tin_tout
    do_dre = do_daqRawEvent
    do_de = do_daqEvent
    do_sc = do_setClockDelays
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
    parser.add_argument('--run', '-r', metavar="FILE", help="Load a cmdline script to be executed before entering the prompt.")
    parser.add_argument('--verbosity', '-v', metavar="LEVEL", default="INFO", help="The output verbosity set in the pxar API.")
    parser.add_argument('--trim', '-T', nargs='?', default=None, help="The output verbosity set in the pxar API.")
    args = parser.parse_args(argv)

    print '\n================================================='
    print '# Extended pXarCore Command Line Interface'
    print '=================================================\n'

    api = PxarStartup(args.dir, args.verbosity, args.trim)

    # start command line
    prompt = PxarCoreCmd(api, args.gui, args.dir)

    # run the startup script if requested
    if args.run:
        prompt.do_run(args.run)
    # start user interaction
    prompt.cmdloop()


if __name__ == "__main__":
    sys.exit(main())
