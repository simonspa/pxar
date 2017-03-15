#!/usr/bin/env python
# --------------------------------------------------------
#       Class to write a list is pXar Events into a root tree
# created on February 20th 2017 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from ROOT import TTree, TFile, vector
from progressbar import Bar, ETA, FileTransferSpeed, Percentage, ProgressBar
from collections import OrderedDict
from os.path import isfile


class TreeWriter:

    def __init__(self, data):

        self.Data = data
        self.File = None
        self.Tree = None
        self.VectorBranches = self.init_vector_branches()

        self.RunFileName = 'runNumber.txt'
        self.RunNumber = self.load_run_number()

        self.ProgressBar = None

    def start_pbar(self, n):
        self.ProgressBar = ProgressBar(widgets=['Progress: ', Percentage(), ' ', Bar(marker='>'), ' ', ETA(), ' ', FileTransferSpeed()], maxval=n)
        self.ProgressBar.start()

    def load_run_number(self):
        if isfile(self.RunFileName):
            f = open(self.RunFileName)
            run_number = int(f.readline())
            f.close()
            return run_number
        else:
            f = open(self.RunFileName, 'w')
            f.write('1')
            f.close()
            return 1

    def save_run_number(self):
        f = open(self.RunFileName, 'w')
        f.write('{n}'.format(n=self.RunNumber + 1))
        f.close()

    @staticmethod
    def init_vector_branches():
        dic = OrderedDict([('plane', vector('unsigned short')()),
                           ('col', vector('unsigned short')()),
                           ('row', vector('unsigned short')()),
                           ('adc', vector('short')()),
                           ('header', vector('unsigned int')()),
                           ('trailer', vector('unsigned int')()),
                           ('pkam', vector('unsigned short')()),
                           ('token_pass', vector('unsigned short')()),
                           ('reset_tbm', vector('unsigned short')()),
                           ('reset_roc', vector('unsigned short')()),
                           ('auto_reset', vector('unsigned short')()),
                           ('cal_trigger', vector('unsigned short')()),
                           ('trigger_count', vector('unsigned short')()),
                           ('trigger_phase', vector('unsigned short')()),
                           ('stack_count', vector('unsigned short')()),
                           ('invalid_address', vector('bool')()),
                           ('invalid_pulse_height', vector('bool')()),
                           ('buffer_corruption', vector('bool')()),
                           ('incomplete_data', vector('bool')()),
                           ('missing_roc_headers', vector('bool')()),
                           ('roc_readback', vector('bool')()),
                           ('no_data', vector('bool')()),
                           ('eventid_mismatch', vector('bool')())])
        return dic

    def clear_vectors(self):
        for key in self.VectorBranches.iterkeys():
            self.VectorBranches[key].clear()

    def set_branches(self):
        for key, vec in self.VectorBranches.iteritems():
            self.Tree.Branch(key, vec)

    def write_tree(self, hv, cur):
        hv_str = '-{v}'.format(v=hv) if hv is not None else ''
        cur_str = '-{c}'.format(c=cur) if cur is not None else ''
        self.File = TFile('run{n}{v}{c}.root'.format(n=str(self.RunNumber).zfill(3), v=hv_str, c=cur_str), 'RECREATE')
        self.Tree = TTree('tree', 'The error tree')
        self.set_branches()
        self.start_pbar(len(self.Data))
        for i, ev in enumerate(self.Data):
            self.ProgressBar.update(i + 1)
            self.clear_vectors()
            for pix in ev.pixels:
                self.VectorBranches['plane'].push_back(int(pix.roc))
                self.VectorBranches['col'].push_back(int(pix.column))
                self.VectorBranches['row'].push_back(int(pix.row))
                self.VectorBranches['adc'].push_back(int(pix.value))
                self.VectorBranches['invalid_address'].push_back(bool(pix.invalid_address))
                self.VectorBranches['invalid_pulse_height'].push_back(bool(pix.invalid_pulse_height))
                self.VectorBranches['buffer_corruption'].push_back(bool(pix.buffer_corruption))
            for k in xrange(len(ev.roc_readback)):
                self.VectorBranches['roc_readback'].push_back(ev.roc_readback[k])
                self.VectorBranches['incomplete_data'].push_back(ev.incomplete_data[k])
                self.VectorBranches['missing_roc_headers'].push_back(ev.missing_roc_headers[k])
            for err in ev.eventid_mismatch:
                self.VectorBranches['eventid_mismatch'].push_back(err)
            for err in ev.no_data:
                self.VectorBranches['no_data'].push_back(err)
            for j in xrange(len(ev.header)):
                self.VectorBranches['header'].push_back(ev.header[j])
                self.VectorBranches['trailer'].push_back(ev.trailer[j])
                self.VectorBranches['pkam'].push_back(ev.havePkamReset[j])
                self.VectorBranches['cal_trigger'].push_back(ev.haveCalTrigger[j])
                self.VectorBranches['token_pass'].push_back(ev.haveTokenPass[j])
                self.VectorBranches['reset_tbm'].push_back(ev.haveResetTBM[j])
                self.VectorBranches['reset_roc'].push_back(ev.haveResetROC[j])
                self.VectorBranches['auto_reset'].push_back(ev.haveAutoReset[j])
                self.VectorBranches['trigger_count'].push_back(ev.triggerCounts[j])
                self.VectorBranches['trigger_phase'].push_back(ev.triggerPhases[j])
                self.VectorBranches['stack_count'].push_back(ev.stackCounts[j])
            self.Tree.Fill()
        self.ProgressBar.finish()
        self.File.cd()
        self.File.Write()
        self.File.Close()
        self.save_run_number()


if __name__ == '__main__':
    z = TreeWriter(None)
