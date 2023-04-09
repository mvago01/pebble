#!/usr/bin/python

from subprocess import run, DEVNULL, call
import re, os
from binascii import hexlify

from colorama import init as colorama_init
from colorama import Fore
from colorama import Style

colorama_init()

MAX_NUM = (1 << 32) - 1

def hex8(num):
    return '{0:08x}'.format(num)

def to_ascii_code(string):
    return hexlify(str(string).encode()).decode()

def ubyte_lit(string):
    string = ubyte(string)
    return re.sub(r'..', lambda matchobj: f"#{matchobj.group(0)} ", string)[:-1]

def ushort_lit(string):
    return re.sub(r'....', lambda matchobj: f"#{matchobj.group(0)} ", string)[:-1]

def ubyte(num):
    return format(num, '02x')

def uarray(elements):
    res = '00'.join(elements) + '0000'
    return ' '.join(split_str_to_chunks(res, 2))

def split_str_to_chunks(string, size):
    result = []
    while len(string) > 0:
        result.append(string[:size])   
        string = string[size:]
    return result

def _split_str_to_max_chunks(string):
    return split_str_to_chunks(string, 60)            

def _uword(matchobj):
    string = matchobj.group(0)
    if string.isspace():
        return ' 20 '
    chunks = _split_str_to_max_chunks(string)
    return '"' + ' "'.join(chunks)


def us(string):
    return re.sub(r'(\S+)|(\s)', _uword, str(string)) + ' $1'

def blank_replace(_, inputs):
    return f"[ [ {inputs.pop(0)} ] ]"

def abs_path_to_file(file):
    here = os.path.dirname(os.path.abspath(file))
    tal_file = os.path.basename(file)[:-2] + 'tal'
    return os.path.join(here, tal_file)

class Tester:
    uxn_loc = '/home/marton/uxn/uxn/'
    uxnasm = uxn_loc + 'uxnasm'
    uxncli = uxn_loc + 'uxncli'
    placeholder = r'\[ \[.*\] \]' 

    def __init__(self, file):
        self.filename = abs_path_to_file(file)
        self.rom = self.filename + '.rom'
        self.fail = False

    def test(self, name, inputs, expected):
        with open(self.filename, 'r+') as f:
            file = f.read()
            file = re.sub(self.placeholder, lambda matchobj: blank_replace(matchobj, inputs), file)

            f.seek(0)
            f.write(file)
            f.truncate()

        run([self.uxnasm, self.filename, self.rom], stderr = DEVNULL)
        result = run([self.uxncli, self.rom], capture_output = True)
        
        got = result.stdout.decode('utf-8')

        if got == expected:
            print(f"{Fore.GREEN}{name}: passed{Style.RESET_ALL}")
        else:
            self.fail = True
            case = {'got': got, 'expected': expected}
            print(f"{Fore.RED}{name}: failed{Style.RESET_ALL} ({case})")
