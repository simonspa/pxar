#!/usr/bin/env python
# --------------------------------------------------------
#       ipython command line tool using the pXar core api
# created on February 23rd 2017 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from ROOT import TCanvas, TCutG, gStyle, TColor, TH2F, TF2, TH1I
from argparse import ArgumentParser
from numpy import zeros, array
from os.path import basename, dirname, realpath, split
from os.path import join as joinpath
from sys import argv, path
from progressbar import Bar, ETA, FileTransferSpeed, Percentage, ProgressBar
lib_dir = joinpath(split(dirname(realpath(__file__)))[0], 'lib')
path.insert(1, lib_dir)
from pxar_helpers import *
from pxar_plotter import Plotter
from time import time

dacdict = PyRegisterDictionary()
probedict = PyProbeDictionary()
prog_name = basename(argv.pop(0))


class CLIX:
    """Simple command processor for the pxar core API."""

    def __init__(self, conf_dir, verbosity, trim):
        # main
        self.api = PxarStartup(conf_dir, verbosity, trim)
        self.Dir = conf_dir
        self.Trim = trim
        self.Verbosity = verbosity

        # dicts
        self.DacDict = PyRegisterDictionary()
        self.ProbeDict = PyProbeDictionary()
        self.TBDelays = self.api.getTestboardDelays()

        self.window = None
        self.Plots = []
        self.ProgressBar = None
        self.NRows = 80
        self.NCols = 52
        set_palette()

    def restart_api(self):
        self.api = None
        self.api = PxarStartup(self.Dir, self.Verbosity, self.Trim)

    def start_pbar(self, n):
        self.ProgressBar = ProgressBar(widgets=['Progress: ', Percentage(), ' ', Bar(marker='>'), ' ', ETA(), ' ', FileTransferSpeed()], maxval=n)
        self.ProgressBar.start()

    @staticmethod
    def run(filename):
        print '\nReading commands from file...\n'
        if not file_exists(filename):
            'File {} does not exit'.format(filename)
        f = open(filename)
        for line in f.readlines():
            if line.startswith('#'):
                continue
            print line.strip('\n\r')
            data = line.split()
            arguments = [float(word) if is_num(word) else word for word in data[1:]]
            exec 'z.{f}({args})'.format(f=data[0], args=dumps(arguments).strip('[]'))
    def convert_raw_event(event):
        for i, word in enumerate(event):
            word &= 0x0fff
            if word & 0x0800:
                word -= 4096
            event[i] = word

    # -----------------------------------------
    # region API
    def get_dac(self, dac, roc_id=0):
        dacs = self.api.getRocDACs(roc_id)
        if dac in dacs:
            return dacs[dac]
        else:
            print 'Unknown dac {d}!'.format(d=dac)
    # endregion

    # -----------------------------------------
    # region DAQ
    def daq_start(self, arg=0):
        self.api.daqStart(arg)

    def daq_stop(self):
        self.api.daqStop()

    def daq_trigger(self, n_trig=1, period=500):
        self.api.daqTrigger(n_trig, period)

    def daq_get_event(self):
        try:
            data = self.api.daqGetEvent()
            print data
        except RuntimeError:
            pass

    def daq_get_raw_event(self, convert=1):
        try:
            event = self.api.daqGetRawEvent()
        except RuntimeError:
            return
        self.convert_raw_event(event) if convert == 1 else do_nothing()
        print event
    # endregion

    # -----------------------------------------
    # region MASK // ENABLE
    def get_activated(self, roc=None):
        return self.api.getNEnabledPixels(roc), self.api.getNMaskedPixels(roc)

    def enable_single_pixel(self, row=14, column=14, roc=None):
        """enableOnePixel [row] [column] [roc] : enables one Pixel (default 14/14); masks and disables the rest"""
        print '--> disable and mask all pixels of all activated ROCs'
        self.api.testAllPixels(0)
        self.api.maskAllPixels(1)
        self.api.testPixel(row, column, 1, roc)
        self.api.maskPixel(row, column, 0, roc)
        print_string = '--> enable and unmask Pixel {r}/{c}: '.format(r=row, c=column)
        print_string += '(' + ','.join('ROC {n}: {a}/{m}'.format(n=roc, a=self.get_activated(roc)[0], m=self.get_activated(roc)[1]) for roc in xrange(self.api.getNEnabledRocs())) + ')'
        print print_string

    def set_pattern_gen(self, cal=True, res=True):
        """ Sets up the trigger pattern generator for ROC testing """
        pgcal = self.get_dac('wbc') + (6 if 'dig' in self.api.getRocType() else 5)
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

    def get_efficiency_map(self, flags=0, n_triggers=10):
        data = self.api.getEfficiencyMap(flags, n_triggers)
        self.print_eff(data, n_triggers)
        self.plot_map(data, "Efficiency", no_stats=True)

    def print_eff(self, data, n_trig):
        unmasked = 4160 - self.api.getNMaskedPixels()
        active = self.api.getNEnabledPixels()
        read_back = sum(px.value for px in data)
        total = n_trig * (unmasked if unmasked < active else active)
        eff = 100. * read_back / total
        print 'Efficiency: {eff:6.2f}% ({rb:5d}/{tot:5d})'.format(eff=eff, rb=int(read_back), tot=total)
        return eff

    def plot_graph(self, gr, lm=.12, rm=.1, draw_opt='alp'):
        c = TCanvas('c', 'c', 1000, 1000)
        c.SetMargin(lm, rm, .1, .1)
        gr.Draw(draw_opt)
        self.window = c
        self.Plots.append(gr)
        self.window.Update()

    def plot_map(self, data, name, count=False, no_stats=False):
        c = TCanvas('c', 'c', 1000, 1000)
        c.SetRightMargin(.12)

        # Find number of ROCs present:
        is_module = self.api.getNRocs() > 1
        proc = 'proc' in self.api.getRocType()
        # Prepare new numpy matrix:
        d = zeros((417 if is_module else 52, 161 if is_module else 80))
        for px in data:
            roc = (px.roc - 12) % 16 if proc else 0
            xoffset = 52 * (roc % 8) if is_module else 0
            yoffset = 80 * int(roc / 8) if is_module else 0

            # Flip the ROCs upside down:
            y = (px.row + yoffset) if (roc < 8) else (2 * yoffset - px.row - 1)
            # Reverse order of the upper ROC row:
            x = (px.column + xoffset) if (roc < 8) else (415 - xoffset - px.column)
            d[x][y] += 1 if count else px.value

        plot = Plotter.create_th2(d, 0, 417 if is_module else 52, 0, 161 if is_module else 80, name, 'pixels x', 'pixels y', name)
        if no_stats:
            plot.SetStats(0)
        plot.Draw('COLZ')
        # draw margins of the ROCs for the module
        self.draw_module_grid(is_module)
        self.window = c
        self.Plots.append(plot)
        self.window.Update()

    def draw_module_grid(self, draw):
        if not draw:
            return
        for i in xrange(2):
            for j in xrange(8):
                rows, cols = self.NRows, self.NCols
                x = array([cols * j, cols * (j + 1), cols * (j + 1), cols * j, cols * j], 'd')
                y = array([rows * i, rows * i, rows * (i + 1), rows * (i + 1), rows * i], 'd')
                cut = TCutG('r{n}'.format(n=j + (j * i)), 5, x, y)
                cut.SetLineColor(1)
                cut.SetLineWidth(1)
                self.Plots.append(cut)
                cut.Draw('same')

    def hitmap(self, t=1, n=10000):
        self.api.HVon()
        t_start = time()
        self.set_pattern_gen(cal=False, res=False)
        self.api.daqStart()
        self.start_pbar(t * 600)
        data = []
        while time() - t_start < t * 60:
            self.ProgressBar.update(int((time() - t_start) * 10) + 1)
            self.api.daqTrigger(n, 500)
            data += self.api.daqGetEventBuffer()
        self.ProgressBar.finish()
        self.api.daqStop()
        self.api.HVoff()
        self.set_pattern_gen()
        data = [pix for event in data for pix in event.pixels]
        self.plot_map(data, 'Hit Map', count=True, no_stats=True)
        stats = self.api.getStatistics()
        event_rate = stats.valid_events / (2.5e-8 * stats.total_events / 8.)
        hit_rate = stats.valid_pixels / (2.5e-8 * stats.total_events / 8.)
        stats.dump
        print 'Event Rate: {0:5.4f} MHz'.format(event_rate / 1000000)
        print 'Hit Rate:   {0:5.4f} MHz'.format(hit_rate / 1000000)

    def test(self):
        h = TH2F('h', 'h', 100, 0., 10., 100, 0., 10.)
        f = TF2("xyg", "xygaus", 0, 10, 0, 10)
        f.SetParameters(1, 5, 2, 5, 2)
        h.FillRandom('xyg', 2000000)
        h.Draw('colz')
        self.Plots.append(h)

    def do_adc_disto(self, vcal=50, col=14, row=14, high=False, n_trig=10000):
        self.api.setDAC('ctrlreg', 4 if high else 0)
        self.api.setDAC('vcal', vcal)
        self.api.daqStart()
        self.api.daqTrigger(n_trig, 500)
        self.enable_single_pixel(col, row)
        data = self.api.daqGetEventBuffer()
        self.api.daqStop()
        adcs = [px.value for evt in data for px in evt.pixels]
        h = TH1I('h_adc', 'ACD Distribution for vcal {v} in {h} Range'.format(v=vcal, h='high' if high else 'low'), 255, 0, 255)
        for adc in adcs:
            h.Fill(adc)
        self.plot_graph(h, draw_opt='')


def set_palette(custom=True, pal=1):
    if custom:
        stops = array([0., .5, 1], 'd')
        green = array([0. / 255., 200. / 255., 80. / 255.], 'd')
        blue = array([0. / 255., 0. / 255., 0. / 255.], 'd')
        red = array([180. / 255., 200. / 255., 0. / 255.], 'd')
        gStyle.SetNumberContours(20)
        bla = TColor.CreateGradientColorTable(len(stops), stops, red, green, blue, 255)
        color_table = array([bla + ij for ij in xrange(255)], 'i')
        gStyle.SetPalette(len(color_table), color_table)
    else:
        gStyle.SetPalette(pal)


def do_nothing():
    pass


def bit_shift(value, shift):
    return (value >> shift) & 0b0111


if __name__ == '__main__':
    # command line argument parsing

    parser = ArgumentParser(prog=prog_name, description="A Simple Command Line Interface to the pxar API.")
    parser.add_argument('--dir', '-d', metavar="DIR", help="The digit rectory with all required config files.")
    parser.add_argument('--run', '-r', metavar="FILE", help="Load a cmdline script to be executed before entering the prompt.", default='')
    parser.add_argument('--verbosity', '-v', metavar="LEVEL", default="INFO", help="The output verbosity set in the pxar API.")
    parser.add_argument('--trim', '-T', nargs='?', default=None, help="The output verbosity set in the pxar API.")
    args = parser.parse_args(argv)

    print_banner('# STARTING ipython pXar Command Line Interface')

    # start command line
    z = CLIX(args.dir, args.verbosity, args.trim)
    print
    if args.run:
        z.run(args.run)

    # shortcuts

    hvon = z.api.HVon
    hvoff = z.api.HVoff
    ge = z.get_efficiency_map
    ds = z.daq_start
    st = z.daq_stop
    ev = z.daq_get_event
    raw = z.daq_get_raw_event
    dt = z.daq_trigger
