#!/usr/bin/env python
# --------------------------------------------------------
#       Class to write a list is pXar Events into a root tree
# created on February 20th 2017 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from ROOT import TTree, TFile, vector
from progressbar import Bar, ETA, FileTransferSpeed, Percentage, ProgressBar


class TreeWriter:

    def __init__(self, data):

        self.Data = data
        self.File = None
        self.Tree = None
        self.VectorBranches = self.init_vector_branches()
        self.ScalarBranches = self.init_scalar_branches()

        self.ProgressBar = None

    def start_pbar(self, n):
        self.ProgressBar = ProgressBar(widgets=['Progress: ', Percentage(), ' ', Bar(marker='>'), ' ', ETA(), ' ', FileTransferSpeed()], maxval=n)
        self.ProgressBar.start()

    @staticmethod
    def init_vector_branches():
        dic = {'plane': vector('unsigned short')(),
               'col': vector('unsigned short')(),
               'row': vector('unsigned short')(),
               'adc': vector('short')()}
        return dic

    @staticmethod
    def init_scalar_branches():
        dic = {'header': 0,
               'trailer': 0,
               'pkam': 0,
               'token_pass': 0,
               'reset_tbm': 0,
               'reset_roc': 0,
               'auto_reset': 0,
               'cal_trigger': 0,
               'trigger_count': 0,
               'trigger_phase': 0,
               'stack_count': 0,
               'incomplete_data': 0,
               'missing_roc_headers': 0,
               'roc_readback': 0,
               'invalid_addresses': 0,
               'invalid_pulse_heights': 0,
               'buffer_corruptions': 0}
        return dic

    def clear_vectors(self):
        for key in self.VectorBranches.iterkeys():
            self.VectorBranches[key].clear()

    def set_branches(self):
        for key, vec in self.VectorBranches.iteritems():
            self.Tree.Branch(key, vec)
        for key, branch in self.ScalarBranches.iteritems():
            self.Tree.Branch(key, branch, 's')

    def write_tree(self):
        self.File = TFile('errors.root', 'RECREATE')
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
            self.ScalarBranches['header'] = ev.header
            self.ScalarBranches['trailer'] = ev.trailer
            self.ScalarBranches['pkam'] = ev.havePkamReset
            self.ScalarBranches['cal_trigger'] = ev.haveCalTrigger
            self.ScalarBranches['token_pass'] = ev.haveTokenPass
            self.ScalarBranches['reset_tbm'] = ev.haveResetTBM
            self.ScalarBranches['reset_roc'] = ev.haveResetROC
            self.ScalarBranches['auto_reset'] = ev.haveAutoReset
            self.ScalarBranches['trigger_count'] = ev.triggerCounts
            self.ScalarBranches['trigger_phase'] = ev.triggerPhases
            self.ScalarBranches['stack_count'] = ev.stackCounts
            self.ScalarBranches['incomplete_data'] = ev.incomplete_data
            self.ScalarBranches['missing_roc_headers'] = ev.missing_roc_headers
            self.ScalarBranches['roc_readback'] = ev.roc_readback
            self.ScalarBranches['invalid_addresses'] = ev.invalid_addresses
            self.ScalarBranches['invalid_pulse_heights'] = ev.invalid_pulse_heights
            self.ScalarBranches['stack_buffer_corruptionscount'] = ev.buffer_corruptions
            self.Tree.Fill()
        self.ProgressBar.finish()
        self.File.cd()
        self.File.Write()
        self.File.Close()
