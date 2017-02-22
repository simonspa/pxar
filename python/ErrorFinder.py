#!/usr/bin/env python
# --------------------------------------------------------
#       Tool to find and categorise read-out errors in the layer 1 CMS pixel modules using the pXar core libraries
# created on February 20th 2017 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from ROOT import TCanvas, TCutG, gStyle, TColor, TH2F, TF2
from argparse import ArgumentParser
from numpy import zeros, array
from os.path import basename, dirname, realpath, split
from os.path import join as joinpath
from sys import argv, path
from progressbar import Bar, ETA, FileTransferSpeed, Percentage, ProgressBar
from time import time
from TreeWriter import TreeWriter

lib_dir = joinpath(split(dirname(realpath(__file__)))[0], 'lib')
path.insert(1, lib_dir)
from pxar_helpers import *
from pxar_plotter import Plotter

dacdict = PyRegisterDictionary()
probedict = PyProbeDictionary()
prog_name = basename(argv.pop(0))


class ErrorFinder:
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

    def restart_api(self):
        self.api = None
        self.api = PxarStartup(self.Dir, self.Verbosity, self.Trim)

    def start_pbar(self, n):
        self.ProgressBar = ProgressBar(widgets=['Progress: ', Percentage(), ' ', Bar(marker='>'), ' ', ETA(), ' ', FileTransferSpeed()], maxval=n)
        self.ProgressBar.start()

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
        module = self.api.getNRocs() > 1
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
        # draw margins of the ROCs for the module
        self.draw_module_grid(module)
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

    def find_errors(self, t=1, n=10000):
        set_palette(False)
        self.api.HVon()
        t_start = time()
        self.set_pg(cal=False, res=False)
        self.api.daqStart()
        self.start_pbar(t * 600)
        data = []
        stats = PxarStatistics(self.api.getNTbms())
        n_triggers = 0
        while time() - t_start < t * 60:
            n_triggers += n
            self.ProgressBar.update(int((time() - t_start) * 10) + 1)
            self.api.daqTrigger(n, 500)
            data += self.api.daqGetEventBuffer()
        self.ProgressBar.finish()
        stats.add(self.api.getStatistics())
        self.api.daqStop()
        self.api.HVoff()
        self.set_pg()
        writer = TreeWriter(data)
        writer.write_tree()
        data = [pix for ev in data for pix in ev.pixels]
        self.plot_map(data, 'Hit Map', count=True, no_stats=True)
        print stats
        stats.save()
        print 'Event Rate: {0:5.4f} MHz'.format(stats.event_rate / 1000000)
        print 'Hit Rate:   {0:5.4f} MHz'.format(stats.hit_rate / 1000000)

    def set_pg(self, cal=True, res=True):
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


def set_palette(custom=True, pal=1):
    if custom:
        stops = array([0., .5, 1], 'd')
        green = array([0. / 255., 200. / 255., 80. / 255.], 'd')
        blue = array([0. / 255., 0. / 255., 0. / 255.], 'd')
        red = array([180. / 255., 200. / 255., 0. / 255.], 'd')
        gStyle.SetNumberContours(20)
        bla = TColor.CreateGradientColorTable(len(stops), stops, red, green, blue, 255, 1)
        color_table = array([bla + ij for ij in xrange(255)], 'i')
        gStyle.SetPalette(len(color_table), color_table)
    else:
        gStyle.SetPalette(pal)

if __name__ == '__main__':
    # command line argument parsing

    parser = ArgumentParser(prog=prog_name, description="A Simple Command Line Interface to the pxar API.")
    parser.add_argument('--dir', '-d', metavar="DIR", help="The digit rectory with all required config files.")
    parser.add_argument('--run', '-r', metavar="FILE", help="Load a cmdline script to be executed before entering the prompt.")
    parser.add_argument('--verbosity', '-v', metavar="LEVEL", default="INFO", help="The output verbosity set in the pxar API.")
    parser.add_argument('--trim', '-T', nargs='?', default=None, help="The output verbosity set in the pxar API.")
    args = parser.parse_args(argv)

    print '\n================================================='
    print '# STARTING Error Finder'
    print '=================================================\n'

    # start command line
    z = ErrorFinder(args.dir, args.verbosity, args.trim)
