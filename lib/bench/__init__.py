# The MIT License (MIT)
#
# Copyright (c) 2013 Carwyn Pelley
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
'''
Bench is a small module for determining program memory usage.

'''
import os


class Memory(object):
    def __init__(self, vmsize, vmpeak, vmrss, vmhwm, tag=None):
        self.mem = {'vmsize': vmsize, 'vmpeak': vmpeak, 'vmrss': vmrss,
                    'vmhwm': vmhwm}
        self.tag = tag

    def __str__(self):
        def get_unit(param):
            if param > 1e9:
                param *= 1e-9
                unit = 'TB'
            elif param > 1e6:
                param *= 1e-6
                unit = 'GB'
            elif param > 1e3:
                param *= 1e-3
                unit = 'MB'
            else:
                unit = 'KB'
            return param, unit

        mem = {}
        for key, value in self.mem.iteritems():
            val, unit = get_unit(value)
            mem[key] = '{:6.2f} {}'.format(val, unit)

        return ('Virtual memory usage {} (peak {})\n'
                'Resident set size {} (peak {})\n'
                'Tag: {}\n\n'.format(
                mem['vmsize'], mem['vmpeak'], mem['vmrss'], mem['vmhwm'],
                self.tag))

    def __sub__(self, other):
        res = {}
        for key, value in self.mem.iteritems():
            res[key] = value - other.mem[key]
        res['tag'] = '({} - {})'.format(self.tag, other.tag)
        return Memory(**res)


def get_usage(tag=None):
    fnme = os.path.join('/', 'proc', str(os.getpid()), 'status')
    usage = {}
    with open(fnme, 'r') as fh:
        for line in fh:
            key, value = line.split(':')
            key = key.strip().lower()
            if key in ['vmsize', 'vmpeak', 'vmrss', 'vmhwm']:
                usage[key] = int(''.join([ss for ss in value.strip() if
                                          ss.isdigit()]))
            usage['tag'] = tag
    return Memory(**usage)


if __name__ == '__main__':
    import numpy as np

    mem = get_usage('before array creation')
    arr = np.arange(200000)
    mem2 = get_usage('after array creation')
    print mem2 - mem
