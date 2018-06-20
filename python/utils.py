# --------------------------------------------------------
#       UTILITY FUNCTIONS
# created on June 19th 2018 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from os.path import isfile


GREEN = '\033[92m'
ENDC = '\033[0m'
YELLOW = '\033[93m'
RED = '\033[91m'


def file_exists(filename):
    return isfile(filename)


def is_num(string):
    try:
        float(string)
        return True
    except ValueError:
        return False


def print_banner(msg, symbol='=', new_lines=True):
    print '{n}{delim}\n{msg}\n{delim}{n}'.format(delim=(len(str(msg)) + 10) * symbol, msg=msg, n='\n' if new_lines else '')
