# The MIT License (MIT)
#
# Copyright (c) 2014 Carwyn Pelley
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
from functools import wraps
import os
import sys


class _ContextDecorator(object):
    """
    A modified base class or mixin taken from python3.2 contextlib source that
    enables context managers to work as decorators.

    """
    def __call__(self, func):
        @wraps(func)
        def inner(*args, **kwds):
            with self:
                return func(*args, **kwds)
        return inner


class _Engine(object):
    fields = ['VmSize', 'VmRSS', 'VmPeak', 'VmHWM']

    def get_log(self):
        return NotImplemented


class _LinuxEngine(_Engine):
    def __init__(self):
        self._pid = os.getpid()

    @property
    def pid(self):
        return self._pid

    def get_log(self):
        def get_field(string):
            stat = string.replace(' ', '').replace('\t', '').split(':')
            if stat[0] in self.fields:
                assert stat[1][-2:] == 'kB'
                stat = {stat[0]: int(stat[1][:-2])}
            else:
                stat = None
            return stat

        fnme = os.path.join('/', 'proc', str(self.pid), 'status')
        with open(fnme, 'r') as fh:
            stat = fh.read()
        fields = {}
        for line in stat.split('\n'):
            field = get_field(line)
            if field:
                fields.update(field)
        return fields


# Set operating system dependent engine.
if os.name == 'posix':
    ENGINE = _LinuxEngine()
else:
    raise RuntimeError('operating system: {} not yet supported'.format(
        sys.platform))


class MemoryUsage(_ContextDecorator):
    """
    Determine process current and peak usage as well as consumption between
    retrievals.

    """
    def __init__(self, out='stdout'):
        self._pid = os.getpid()
        self._stat = []
        self.get_log()
        self._summary_print = True
        self.out = out

    @property
    def usage(self):
        return self._stat

    @property
    def pid(self):
        return self._pid

    def get_log(self):
        fields = ENGINE.get_log()
        self.usage.append(fields)

    @staticmethod
    def print_summary(statistic):
        width = 9
        msg = (''.join([item.rjust(width*2, ' ') for item in
               ['Current Usage', 'Current Usage Inc', 'Process Peak',
                'Process Peak Inc']])) + '\n'
        msg = msg + ' '.ljust(width*2, '#') * 4 + '\n'
        msg = msg + (''.join([item.rjust(width, ' ') for item in
                     ['VirtMem', 'RSS']])) * 4 + '\n'
        msg += '{}' * 8 + '\n'
        params = [statistic['VmSize'], statistic['VmRSS'],
                  statistic['inc_VmSize'], statistic['inc_VmRSS'],
                  statistic['VmPeak'], statistic['VmHWM'],
                  statistic['inc_VmPeak'], statistic['inc_VmHWM']]
        for iparam in range(len(params)):
            param = params[iparam]
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
            params[iparam] = ('{:6.2f}{}'.format(param, unit))
            params[iparam] = params[iparam].rjust(width, ' ')

        print msg.format(*params)

    def get_usage(self):
        self.get_log()
        diff_log = {'inc_{}'.format(name):
                    (self.usage[-1][name] - self.usage[-2][name]) for
                    name in self.usage[-1].keys()}
        diff_log.update({name: self.usage[-1][name] for name in
                         self.usage[-1].keys()})
        self.print_summary(diff_log)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.get_usage()


if __name__ == '__main__':
    #import sys

    #module = os.path.splitext(sys.argv[1])[0]
    mem = MemoryUsage()
    #exec('import {}'.format(module))
    a = range(300000)
    mem.get_usage()
