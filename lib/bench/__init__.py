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
from functools import wraps
import inspect
import os


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


class MemoryUsage(_ContextDecorator):
    def __init__(self):
        self._pid = os.getpid()
        self._stat1 = self.get_log()
        self._stat2 = None
        self._summary_print = True

    @property
    def usage_t0(self):
        return self._stat1

    @property
    def usage_t1(self):
        if self._stat2 is None:
            self._stat2 = self.get_log()
        return self._stat2

    def update_statistic(self):
        self._stat2 = self.get_log()

    @property
    def pid(self):
        return self._pid

    def get_log(self):
        fnme = os.path.join('/', 'proc', str(self.pid), 'status')
        with open(fnme, 'r') as fh:
            stat = fh.read()
            stat = [ss.split(':') for ss in
                    stat.replace(' ', '').replace('\t', '').split('\n')]
        return {item[0]: item[1] for item in stat if len(item) == 2}

    @staticmethod
    def print_summary(statistics):
        return ('Virtual memory usage {}Kb (peak {}Kb)\n'
                'Resident set size {}Kb (peak {}Kb)\n'.format(
                statistics['VmSize'], statistics['VmPeak'],
                statistics['VmRSS'], statistics['VmHWM']))

    def memory_consumption(self):
        return {name: (int(''.join(char for char in self.usage_t1[name] if
                                   char.isdigit())) -
                       int(''.join(char for char in self.usage_t0[name] if
                                   char.isdigit()))) for
                name in ['VmSize', 'VmPeak', 'VmRSS', 'VmHWM']}

    def __enter__(self):
        #stack = inspect.stack()
        #self.stack = inspect.stack()#[1]
        #self.stack = [inspect.currentframe()] + self.stack

        return self

    def __exit__(self, type, value, traceback):
        memcon = self.memory_consumption()
        if self._summary_print:
            print 'Memory consumption:'
            #print self.stack
            print self.print_summary(memcon)


if __name__ == '__main__':
    import numpy as np

    with MemoryUsage() as mu:
        arr = np.arange(200000)

    @MemoryUsage()
    def gen_array():
        arr = np.arange(200000)
        return arr

    gen_array()
