#!/usr/bin/env python
# -*- coding: utf-8 -*-#
#
#
# Copyright (C) 2017, S3IT, University of Zurich. All rights reserved.
#
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

__docformat__ = 'reStructuredText'
__author__ = 'Antonio Messina <antonio.s.messina@gmail.com>'

def to_bib(num):
    """Convert num to a reasonable power of 2.

    >>> to_bib(100)
    (100.0, 'bytes')
    >>> to_bib(1024)
    (1.0, 'KiB')
    >>> t,u = to_bib(2**20+100)
    >>> "%.2f" % t
    '1.00'
    >>> u
    'MiB'
    >>> to_bib(5*2**50)
    (5.0, 'PiB')
    >>> to_bib(-1*2**30)
    (-1.0, 'GiB')
    """
    absnum = abs(num)
    sign = -1 if num < 0 else 1
    for thr, unit in (
            (2**60, 'EiB'),
            (2**50, 'PiB'),
            (2**40, 'TiB'),
            (2**30, 'GiB'),
            (2**20, 'MiB'),
            (2**10, 'KiB'),
    ):
        if absnum >= thr:
            return (sign*float(absnum)/thr, unit)
    return (float(num), 'bytes')
            
    

if __name__ == "__main__":
    import doctest
    doctest.testmod(name="utils",
                    optionflags=doctest.NORMALIZE_WHITESPACE)
