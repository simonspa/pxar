#!/usr/bin/env python
# --------------------------------------------------------
#       ipython command line tool using the pXar core api
# created on February 23rd 2017 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from ROOT import TCanvas, TCutG, gStyle, TColor, TH2F, TF2, TMultiGraph, TH1I
from argparse import ArgumentParser
from numpy import zeros, array
from os.path import basename, dirname, realpath, split
from os.path import join as joinpath
from sys import argv, path
from time import time, sleep
from progressbar import Bar, ETA, FileTransferSpeed, Percentage, ProgressBar
lib_dir = joinpath(split(dirname(realpath(__file__)))[0], 'lib')
path.insert(1, lib_dir)
from pxar_helpers import *
from pxar_plotter import Plotter
from TreeWriterShort import TreeWriter

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

        self.window = None
        self.Plots = []
        self.ProgressBar = None
        self.NRows = 80
        self.NCols = 52
        set_palette()

        self.Plotter = Plotter()

    def restart_api(self):
        self.api = None
        self.api = PxarStartup(self.Dir, self.Verbosity, self.Trim)

    def start_pbar(self, n):
        self.ProgressBar = ProgressBar(widgets=['Progress: ', Percentage(), ' ', Bar(marker='>'), ' ', ETA(), ' ', FileTransferSpeed()], maxval=n)
        self.ProgressBar.start()

    @staticmethod
    def convert_raw_event(event):
        for i, word in enumerate(event):
            word &= 0x0fff
            if word & 0x0800:
                word -= 4096
            event[i] = word

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

    def get_tb_ia(self):
        """ returns analog DTB current """
        print 'Analog Current: {c} mA'.format(c=self.api.getTBia() * 1000)
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
    # endregion

    def get_dac(self, dac, roc_id=0):
        dacs = self.api.getRocDACs(roc_id)
        if dac in dacs:
            return dacs[dac]
        else:
            print 'Unknown dac {d}!'.format(d=dac)

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

    def plot_map(self, data, name, count=False, no_stats=False):
        c = TCanvas('c', 'c', 1000, 1000)
        c.SetRightMargin(.12)

        # Find number of ROCs present:
        mod = self.api.getNRocs() > 1
        proc = 'proc' in self.api.getRocType()
        # Prepare new numpy matrix:
        d = zeros((417 if mod else 52, 161 if mod else 80))
        for px in data:
            roc = (px.roc - 12) % 16 if proc else 0
            xoffset = 52 * (roc % 8) if mod else 0
            yoffset = 80 * int(roc / 8) if mod else 0

            # Flip the ROCs upside down:
            y = (px.row + yoffset) if (roc < 8) else (2 * yoffset - px.row - 1)
            # Reverse order of the upper ROC row:
            x = (px.column + xoffset) if (roc < 8) else (415 - xoffset - px.column)
            d[x][y] += 1 if count else px.value

        plot = Plotter.create_th2(d, 0, 417 if mod else 52, 0, 161 if mod else 80, name, 'pixels x', 'pixels y', name)
        if no_stats:
            plot.SetStats(0)
        plot.Draw('COLZ')
        # draw margins of the ROCs for the module
        self.draw_module_grid(mod)
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

    def test(self):
        h = TH2F('h', 'h', 100, 0., 10., 100, 0., 10.)
        f = TF2("xyg", "xygaus", 0, 10, 0, 10)
        f.SetParameters(1, 5, 2, 5, 2)
        h.FillRandom('xyg', 2000000)
        h.Draw('colz')
        self.Plots.append(h)

    def set_pg(self, cal=True, res=True, delay=None):
        """ Sets up the trigger pattern generator for ROC testing """
        pgcal = self.get_dac('wbc') + (6 if 'dig' in self.api.getRocType() else 5)
        pg_setup = []
        if delay is not None:
            pg_setup.append(('DELAY', delay))
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

    def clear_buffer(self):
        try:
            self.api.daqGetEventBuffer()
        except RuntimeError:
            pass

    def wbc_scan(self, min_wbc=90, max_triggers=50, max_wbc=130):
        """do_wbcScan [minimal WBC] [number of events] [maximal WBC]: \n
        sets wbc from minWBC until it finds the wbc which has more than 90% filled events or it reaches maxWBC \n
        (default [90] [100] [130])"""

        # prepararations
        print 'Turning on HV!'
        self.api.HVon()
        print 'Setting trigger source to "extern"'
        self.api.daqTriggerSource('extern')
        self.api.daqStart()

        trigger_phases = zeros(10)
        yields = OrderedDict([(roc, {wbc: 0 for wbc in xrange(min_wbc, max_wbc)}) for roc in xrange(self.api.getNEnabledRocs())])
        set_dacs = {roc: False for roc in yields}
        print '\nROC EVENT YIELDS:\n  wbc\t{r}'.format(r='\t'.join(('roc' + str(yld)).rjust(6) for yld in yields.keys()))

        # loop over wbc
        for wbc in xrange(min_wbc, max_wbc):
            self.clear_buffer()
            self.api.setDAC('wbc', wbc)

            # loop until you find nTriggers
            n_triggers = 0
            while n_triggers < max_triggers:
                try:
                    data = self.api.daqGetEvent()
                    trigger_phases[data.triggerPhases[0]] += 1
                    for roc in set([pix.roc for pix in data.pixels]):
                        yields[roc][wbc] += 1. * 100. / max_triggers
                    n_triggers += 1
                except RuntimeError:
                    pass
            y_strings = ['{y:5.1f}%'.format(y=yld) for yld in [yields[roc][wbc] for roc in yields.iterkeys()]]
            print '  {w:03d}\t{y}'.format(w=wbc, y='\t'.join(y_strings))

            # stopping criterion
            best_wbc = max_wbc
            if wbc > min_wbc + 3:
                for roc, ylds in yields.iteritems():
                    if any(yld > 10 for yld in ylds.values()[:wbc - min_wbc - 2]):
                        best_wbc = ylds.keys()[ylds.values().index(max(ylds.values()))]
                        print 'set wbc of roc {i} to {v}'.format(i=roc, v=best_wbc)
                        self.api.setDAC('wbc', best_wbc, roc)
                        set_dacs[roc] = True
                if all(set_dacs.itervalues()):
                    print 'found all wbcs'

                    for roc, dic in yields.iteritems():
                        keys = dic.keys()
                        for key in keys:
                            if key >= best_wbc + 4:
                                yields[roc].pop(key)
                    break
        self.api.daqStop()

        # triggerphase

        print '\nTRIGGER PHASE:'
        for i, trigger_phase in enumerate(trigger_phases):
            if trigger_phase:
                percentage = trigger_phase * 100 / sum(trigger_phases)
                print '{i}\t{d} {v:2.1f}%'.format(i=i, d=int(round(percentage)) * '|', v=percentage)

        # plot wbc_scan
        mg = TMultiGraph('mg_wbc', 'WBC Scans for all ROCs')
        colors = range(1, len(yields) + 1)
        l = Plotter.create_legend(nentries=len(yields), x1=.7)
        for i, (roc, dic) in enumerate(yields.iteritems()):
            gr = Plotter.create_graph(x=dic.keys(), y=dic.values(), tit='wbcs for roc {r}'.format(r=roc), xtit='wbc', ytit='yield [%]', color=colors[i])
            l.AddEntry(gr, 'roc{r}'.format(r=roc), 'lp')
            mg.Add(gr, 'lp')
        self.Plotter.plot_histo(mg, draw_opt='a', l=l)
        mg.GetXaxis().SetTitle('WBC')
        mg.GetYaxis().SetTitle('Yield [%]')

    def hitmap(self, t=1, random_trigger=1, n=10000):
        self.api.HVon()
        t_start = time()
        if random_trigger:
            self.set_pg(cal=False, res=False, delay=20)
        else:
            self.api.daqTriggerSource('extern')
        self.api.daqStart()
        self.start_pbar(t * 600)
        data = []
        while time() - t_start < t * 60:
            self.ProgressBar.update(int((time() - t_start) * 10) + 1)
            if random_trigger:
                self.api.daqTrigger(n, 500)
            try:
                sleep(.5)
                data += self.api.daqGetEventBuffer()
            except RuntimeError:
                pass
            except MemoryError:
                break
        self.ProgressBar.finish()
        self.api.daqStop()
        self.api.HVoff()
        self.set_pg()
        pix_data = [pix for event in data for pix in event.pixels]
        h = TH1I('h', 'h', 512, -256, 256)
        for pix in pix_data:
            h.Fill(pix.value)
        print 'Entries:', h.GetEntries
        self.Plotter.plot_histo(h, draw_opt='hist')
        self.plot_map(pix_data, 'Hit Map', count=True, no_stats=True)
        stats = self.api.getStatistics()
        event_rate = stats.valid_events / (2.5e-8 * stats.total_events / 8.)
        hit_rate = stats.valid_pixels / (2.5e-8 * stats.total_events / 8.)
        stats.dump
        print 'Event Rate: {0:5.4f} MHz'.format(event_rate / 1000000)
        print 'Hit Rate:   {0:5.4f} MHz'.format(hit_rate / 1000000)
        writer = TreeWriter(data)
        writer.write_tree()

    def load_mask(self, file_name):
        f = open(file_name, 'r')
        lines = [line.strip('\n') for line in f.readlines() if len(line) > 3 and not line.startswith('#')]
        for i, line in enumerate(lines):
            data1 = line.split(' ')
            if data1[0] == 'cornBot':
                data2 = lines[i + 1].split(' ')
                i2c = int(data1[1])
                self.api.maskAllPixels(True, i2c)
                for col in xrange(int(data1[2]), int(data2[2]) + 1):
                    for row in xrange(int(data1[3]), int(data2[3]) + 1):
                        print col, row, i2c
                        self.api.maskPixel(col, row, False, i2c)




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

if __name__ == '__main__':
    # command line argument parsing

    parser = ArgumentParser(prog=prog_name, description="A Simple Command Line Interface to the pxar API.")
    parser.add_argument('--dir', '-d', metavar="DIR", help="The digit rectory with all required config files.")
    parser.add_argument('--run', '-r', metavar="FILE", help="Load a cmdline script to be executed before entering the prompt.")
    parser.add_argument('--verbosity', '-v', metavar="LEVEL", default="INFO", help="The output verbosity set in the pxar API.")
    parser.add_argument('--trim', '-T', nargs='?', default=None, help="The output verbosity set in the pxar API.")
    parser.add_argument('-wbc', action='store_true')
    args = parser.parse_args(argv)

    print '\n================================================='
    print '# STARTING Error Finder'
    print '=================================================\n'

    # start command line
    z = CLIX(args.dir, args.verbosity, args.trim)
    if args.wbc:
        z.wbc_scan()
        raw_input('Enter any key to close the program')

    # shortcuts
    ga = z.get_efficiency_map
    ds = z.daq_start
    st = z.daq_stop
    ev = z.daq_get_event
    raw = z.daq_get_raw_event
    dt = z.daq_trigger
    ia = z.get_tb_ia
    # sd = z.api.setDAC
