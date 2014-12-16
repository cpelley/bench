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
    def __init__(self, out='stdout'):
        self._pid = os.getpid()
        self._stat = []
        self.get_log()
        self._summary_print = True
        self.out = out

        # Override stack from get_log
        stack = inspect.stack()
        self.usage[-1].update({'context': inspect.stack()[2]})


    @property
    def usage(self):
        return self._stat

    @property
    def pid(self):
        return self._pid

    def get_log(self):
        fnme = os.path.join('/', 'proc', str(self.pid), 'status')
        with open(fnme, 'r') as fh:
            stat = fh.read()
            stat = [ss.split(':') for ss in
                    stat.replace(' ', '').replace('\t', '').split('\n')]
        self.usage.append({item[0]: item[1] for
                           item in stat if len(item) == 2})
        stack = inspect.stack()
        self.usage[-1].update({'context': inspect.stack()[2]})

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

        msg += statistic['context']
        print msg.format(*params)

    def get_usage(self):
        self.get_log()
        diff_log = {'inc_{}'.format(name):
                    (int(''.join(char for char in self.usage[-1][name] if
                                 char.isdigit())) -
                     int(''.join(char for char in self.usage[-2][name] if
                                 char.isdigit()))) for
                    name in ['VmSize', 'VmPeak', 'VmRSS', 'VmHWM']}
        diff_log.update({name:
                        (int(''.join(char for char in self.usage[-1][name] if
                                     char.isdigit()))) for name in
                         ['VmSize', 'VmPeak', 'VmRSS', 'VmHWM']})
        diff_log.update({'context': '{}-{}'.format(
                         self.usage[-2]['context'][2],
                         self.usage[-1]['context'][2])})
        self.print_summary(diff_log)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.get_usage()


if __name__ == '__main__':
    @MemoryUsage()
    def gen_array():
        arr = range(200000)
        return arr

    # Method 1: decorator
    gen_array()

    # Method 2: context manager
    with MemoryUsage() as mu:
        arr = range(200000)

    # Method 3: instance
    mem = MemoryUsage()
    arr = range(200000)
    mem.get_usage()
    arr = range(200000)
    mem.get_usage()
    arr = range(400000)
    mem.get_usage()
