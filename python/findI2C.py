#!/usr/bin/env python
# --------------------------------------------------------
#       Script to find the I2C of a ROC
# created on February 20th 2017 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------


from os.path import dirname, realpath, split, join
from sys import path
from glob import glob
from shutil import move
from time import sleep

lib_dir = join(split(dirname(realpath(__file__)))[0], 'lib')
path.insert(1, lib_dir)

from pxar_helpers import *


def set_i2c(i2c):
    old_i2c = None
    for filename in glob('*Parameters_*'):
        old_i2c = filename.split('_')[-1].strip('C.dat')
        new_filename = filename.replace('C{i}'.format(i=old_i2c), 'C{i}'.format(i=i2c))
        move(filename, new_filename)

    f = open('configParameters.dat', 'r+')
    lines = f.readlines()
    f.seek(0)
    for line in lines:
        if 'i2c' in line and not line.startswith('#'):
            line = line.replace('i2c: {i}'.format(i=old_i2c), 'i2c: {i}'.format(i=i2c))
        f.write(line)
    f.close()

for i2c in xrange(16):
    set_i2c(i2c)
    api = PxarStartup('.', "INFO")
    sleep(2)
    current = api.getTBia() * 1000
    print i2c, current
    if current > 2:
        print 'found i2c', i2c
        break
    del api
