#!/usr/bin/env python2
"""
Helper classes and functions useful when interfacing the pxar API with Python.
"""
from PyPxarCore import Pixel, PixelConfig, PyPxarCore, PyRegisterDictionary, PyProbeDictionary, Statistics
from functools import wraps # used in parameter verification decorator ("arity")
import os # for file system cmds
import sys
import shlex
from collections import OrderedDict
from datetime import datetime
from ConfigParser import ConfigParser

# "arity": decorator used for parameter parsing/verification on each cmd function call
# Usually, the cmd module only passes a single string ('line') with all parameters;
# this decorator divides and verifies the types of each parameter.
def arity(n, m, cs=[]): # n = min number of args, m = max number of args, cs = types
    def __temp1(f):
        @wraps(f) # makes sure the docstring of the orig. function is passed on
        def __temp2(self, text):
            ps = filter(lambda p: p, text.split(" "))
            if len(ps) < n:
                print "Error: this command needs %d arguments (%d given)" % (n, len(ps))
                return
            if len(ps) > m:
                print "Error: this command takes at most %d arguments (%d given)" % (m, len(ps))
                return
            # now verify the type
            try:
                ps = [ c(p) for c, p in zip(cs, ps) ]
            except ValueError as e:
                print "Error: '" + str(p) + "' does not have " + str(c)
                return
            f(self, *ps)
        return __temp2
    return __temp1

def print_data(fullOutput,data,stepsize=1):
    for idac, dac in enumerate(data):
        s = "DAC " + str(idac*stepsize) + ": "
        if fullOutput:
            for px in dac:
                s += str(px)
        else:
            s += str(len(dac)) + " pixels"
        print s

def get_possible_filename_completions(text):
    head, tail = os.path.split(text.strip())
    if head == "": #no head
        head = "."
    files = os.listdir(head)
    return [ f for f in files if f.startswith(tail) ]

def extract_full_argument(line, endidx):
    newstart = line.rfind(" ", 0, endidx)
    return line[newstart:endidx]

class PxarConfigFile:
    """ class that loads the old-style config files of psi46expert """
    def __init__(self, f):
        self.config = {}
        thisf = open(f)
        try:
            for line in thisf:
                if not line.startswith("--") and not line.startswith("#"):
                    parts = shlex.split(line)
                    if len(parts) == 2:
                        self.config[parts[0].lower()] = parts[1]
                    elif len(parts) == 3:
                        parts = [parts[0],' '.join(parts[1:])]
                        self.config[parts[0].lower()] = parts[1]
                    elif len(parts) == 4:
                        parts = [parts[0],' '.join(parts[1:])]
                        if len(parts) == 2:
                            self.config[parts[0].lower()] = parts[1]

        finally:
            thisf.close()
    def show(self):
        print self.config
    def get(self, opt, default=None):
        return self.config.get(opt.lower(), default)

class PxarParametersFile:
    """ class that loads the old-style parameters files of psi46expert """
    def __init__(self, f):
        self.config = {}
        thisf = open(f)
        try:
            for line in thisf:
                if not line.startswith("--") and not line.startswith("#"):
                    parts = shlex.split(line)
                    if len(parts) == 3:
                        # ignore the first part (index/line number)
                        self.config[parts[1].lower()] = parts[2]
                    elif len(parts) == 2:
                        self.config[parts[0].lower()] = parts[1]
        finally:
            thisf.close()
    def show(self):
        print self.config
    def get(self, opt, default = None):
        if default:
            return self.config.get(opt.lower(),default)
        else:
            return self.config[opt.lower()]
    def getAll(self):
        return self.config

class PxarMaskFile:
    """ class that loads the mask files of pxarGUI """
    def __init__(self, f):
        self.config = list()
        thisf = open(f)
        try:
            for line in thisf:
                if not line.startswith("--") and not line.startswith("#"):
                    parts = shlex.split(line)
                    if len(parts) == 4:
                        # single pixel to be masked:
                        p = PixelConfig(int(parts[2]),int(parts[3]),15)
                        p.roc = int(parts[1])
                        p.mask = True
                        self.config.append(p)
                    elif len(parts) == 3:
                        # Full Column/Row to be masked:
                        if parts[0] == "col":
                            for row in range(0, 80):
                                p = PixelConfig(int(parts[2]),row,15)
                                p.roc = int(parts[1])
                                p.mask = True
                                self.config.append(p)
                        elif parts[0] == "row":
                            for column in range(0, 52):
                                p = PixelConfig(column,int(parts[2]),15)
                                p.roc = int(parts[1])
                                p.mask = True
                                self.config.append(p)
                    elif len(parts) == 2:
                        # Full ROC to be masked
                        for column in range(0, 52):
                            for row in range(0, 80):
                                p = PixelConfig(column,row,15)
                                p.roc = int(parts[1])
                                p.mask = True
                                self.config.append(p)
        finally:
            thisf.close()
    def show(self):
        print self.config
    def get(self):
        return self.config

class PxarTrimFile:
    """ class that loads the old-style trim parameters files of psi46expert """
    def __init__(self, f, roc, masks):
        self.config = list()
        thisf = open(f)
        try:
            for line in thisf:
                if not line.startswith("--") and not line.startswith("#"):
                    parts = shlex.split(line)
                    if len(parts) == 4:
                        # Ignore the 'Pix' string in the file...
                        p = PixelConfig(int(parts[2]),int(parts[3]),int(parts[0]))
                        p.roc = roc
                        # Check if this pixel is masked:
                        if p in masks:
                            p.mask = True
                        else:
                            p.mask = False
                        self.config.append(p)
        finally:
            thisf.close()
    def show(self):
        print self.config
    def get(self, opt, default = None):
        if default:
            return self.config.get(opt.lower(),default)
        else:
            return self.config[opt.lower()]
    def getAll(self):
        return self.config


class PxarStatistics:

    def __init__(self, channels):
        self.NChannels = channels if channels else 1
        self.GeneralInformation = OrderedDict([('words read', 0),
                                               ('events empty', 0),
                                               ('events valid', 0),
                                               ('pixels valid', 0)])
        self.EventErrors = OrderedDict([('start marker', 0),
                                        ('stop marker', 0),
                                        ('overflow', 0),
                                        ('invalid words', 0),
                                        ('invalid XOR', 0),
                                        ('frame', 0),
                                        ('idle data', 0),
                                        ('no data', 0),
                                        ('PKAM', 0)])
        self.TbmErrors = OrderedDict([('header', 0),
                                      ('trailer', 0),
                                      ('eventid mismatch', 0)])
        self.RocErrors = OrderedDict([('missing header', 0),
                                      ('readback', 0)])
        self.PixelDecodingErrors = OrderedDict([('incomplete', 0),
                                                ('address', 0),
                                                ('pulse height', 0),
                                                ('buffer corruption', 0)])
        self.AllDics = OrderedDict([('General Information', self.GeneralInformation),
                                    ('Event Errors', self.EventErrors),
                                    ('TBM Errors', self.TbmErrors),
                                    ('ROC Errors', self.RocErrors),
                                    ('Pixel Decoding Errors', self.PixelDecodingErrors)])

    def __str__(self):
        string = ''
        for head, dic in self.AllDics.iteritems():
            string += '{h}\n'.format(h=head)
            for key, value in dic.iteritems():
                string += '\t{k}{v}\n'.format(k=(key + ':').ljust(20), v=value)
        return string

    def save(self, hv=None, cur=None):
        hv_str = '-{v}'.format(v=hv) if hv is not None else ''
        cur_str = '-{c}'.format(c=cur) if cur is not None else ''
        f = open('stats{v}{c}-{t}.conf'.format(t=datetime.now().strftime('%m-%d_%H_%M_%S'), v=hv_str, c=cur_str), 'w')
        p = ConfigParser()
        for head, dic in self.AllDics.iteritems():
            p.add_section(head)
            for key, value in dic.iteritems():
                p.set(head, key, value)
        p.write(f)
        f.close()

    def add(self, stats):
        self.GeneralInformation['words read'] += stats.info_words_read
        self.GeneralInformation['events empty'] += stats.empty_events
        self.GeneralInformation['events valid'] += stats.valid_events
        self.GeneralInformation['pixels valid'] += stats.valid_pixels
        self.EventErrors['start marker'] += stats.errors_event_start
        self.EventErrors['stop marker'] += stats.errors_event_stop
        self.EventErrors['overflow'] += stats.errors_event_overflow
        self.EventErrors['invalid words'] += stats.errors_event_invalid_words
        self.EventErrors['invalid XOR'] += stats.errors_event_invalid_xor
        self.EventErrors['frame'] += stats.errors_event_frame
        self.EventErrors['idle data'] += stats.errors_event_idledata
        self.EventErrors['no data'] += stats.errors_event_nodata
        self.EventErrors['PKAM'] += stats.errors_event_pkam
        self.TbmErrors['header'] += stats.errors_tbm_header
        self.TbmErrors['trailer'] += stats.errors_tbm_trailer
        self.TbmErrors['eventid mismatch'] += stats.errors_tbm_eventid_mismatch
        self.RocErrors['missing header'] += stats.errors_roc_missing
        self.RocErrors['readback'] += stats.errors_roc_readback
        self.PixelDecodingErrors['incomplete'] += stats.errors_pixel_incomplete
        self.PixelDecodingErrors['address'] += stats.errors_pixel_address
        self.PixelDecodingErrors['pulse height'] += stats.errors_pixel_pulseheight
        self.PixelDecodingErrors['buffer corruption'] += stats.errors_pixel_buffer_corrupt

    def clear(self):
        for dic in self.AllDics:
            for key in dic.iterkeys():
                dic[key] = 0

    @property
    def valid_pixels(self):
        return self.GeneralInformation['pixels valid']

    @property
    def valid_events(self):
        return self.GeneralInformation['events valid']

    @property
    def total_events(self):
        return self.GeneralInformation['pixels valid'] + self.GeneralInformation['events empty']

    @property
    def event_rate(self):
        return self.valid_events / (2.5e-8 * self.total_events / float(self.NChannels))

    @property
    def hit_rate(self):
        return self.valid_pixels / (2.5e-8 * self.total_events / float(self.NChannels))


def PxarStartup(directory, verbosity, trim=None):
    if not directory or not os.path.isdir(directory):
        print "Error: no or invalid configuration directory specified!"
        sys.exit(404)

    config = PxarConfigFile('%sconfigParameters.dat'%(os.path.join(directory,"")))
    tbparameters = PxarParametersFile('%s%s'%(os.path.join(directory,""),config.get("tbParameters")))
    masks = PxarMaskFile('%s%s'%(os.path.join(directory,""),config.get("maskFile")))
    
    # Power settings:
    power_settings = {
        "va":config.get("va", 1.9),
        "vd":config.get("vd", 2.6),
        "ia":config.get("ia", 1.190),
        "id":config.get("id", 1.10)}
    if float(power_settings['va']) > 100:
        print 'INFO: set power settings from [mV] to [V]'
        power_settings = {key: int(value) / 1000. for key, value in power_settings.iteritems()}

    tbmDACs = []
    for tbm in range(int(config.get("nTbms"))):
        for n in range(2):
            tbmparameters = PxarParametersFile('%s%s'%(os.path.join(directory,""),config.get("tbmParameters") + "_C" + str(tbm) + ("a" if n%2 == 0 else "b") + ".dat"))
            tbmDACs.append(tbmparameters.getAll())

    print "Have DAC config for " + str(len(tbmDACs)) + " TBM cores:"
    for idx, tbmDAC in enumerate(tbmDACs):
        for key in tbmDAC:
            print "  TBM " + str(idx/2) + ("a" if idx%2 == 0 else "b") + " dac: " + str(key) + " = " + str(tbmDAC[key])

    # init pixel list
    pixels = list()
    for column in range(0, 52):
        for row in range(0, 80):
            p = PixelConfig(column,row,15)
            p.mask = False
            pixels.append(p)

    rocDacs = []
    rocPixels = list()
    rocI2C = []
    config_nrocs = config.get("nrocs").split()
    nrocs = int(config_nrocs[0])
    i2cs = [i for i in xrange(nrocs)]
    if len(config_nrocs) > 1:
        if config_nrocs[1].startswith('i2c'):
            i2cs = ' '.join(config_nrocs[2:])
            i2cs = [int(i) for i in i2cs.split(',')]
            print "Number of ROCs:", nrocs, "\b; Configured I2C's:", i2cs
    for i2c in i2cs:
        dac_file = '{dir}/{f}{trim}_C{i2c}.dat'.format(dir=directory, trim=trim if trim is not None else '', i2c=i2c, f=config.get('dacParameters'))
        trim_file = '{dir}/{f}{trim}_C{i2c}.dat'.format(dir=directory, trim=trim if trim is not None else '', i2c=i2c, f=config.get('trimParameters'))
        dacconfig = PxarParametersFile(dac_file)
        trimconfig = PxarTrimFile(trim_file, i2c, masks.get())
        print "We have " + str(len(trimconfig.getAll())) + " pixels for ROC " + str(i2c)
        rocI2C.append(i2c)
        rocDacs.append(dacconfig.getAll())
        rocPixels.append(trimconfig.getAll())


    # set pgcal according to wbc
    pgcal = int(rocDacs[0]['wbc'])
    pgcal += 6 if 'dig' in config.get('rocType') else 5
    print 'pgcal is:', pgcal

    # Pattern Generator for single ROC operation:
    if int(config.get("nTbms")) == 0:
        pg_setup = (
            ("PG_RESR",25),
            ("PG_CAL",pgcal),
            ("PG_TRG",16),
            ("PG_TOK",0)
            )
    else:
        pg_setup = (
            ("PG_RESR",15),
            ("PG_CAL",pgcal),
            ("PG_TRG",0))
       # Start an API instance from the core pxar library
    api = PyPxarCore(usbId=config.get("testboardName"),logLevel=verbosity)
    print api.getVersion()
    if not api.initTestboard(pg_setup = pg_setup,
    power_settings = power_settings,
    sig_delays = tbparameters.getAll()):
        print "WARNING: could not init DTB -- possible firmware mismatch."
        print "Please check if a new FW version is available"
        exit()

    if not any(word in config.get('rocType') for word in ['dig', 'proc']):
        print 'Analogue decodingOffset set to:', int(config.get("decodingOffset", 0))
        api.setDecodingOffset(int(config.get("decodingOffset", int(0))))
    print "And we have just initialized " + str(len(pixels)) + " pixel configs to be used for every ROC!"

    hubids = [int(i) for i in config.get("hubId",31).split(',')]
    print 'HubIds set to:', hubids
    api.initDUT(hubids, config.get("tbmType","tbm08"), tbmDACs,config.get("rocType"), rocDacs, rocPixels, rocI2C)

    api.testAllPixels(True)
    print "Now enabled all pixels"

    print "pxar API is now started and configured."
    return api
