#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The Academy / ASC Common LUT Format Sample Implementations are provided by the
Academy under the following terms and conditions:

Copyright © 2015 Academy of Motion Picture Arts and Sciences ("A.M.P.A.S.").
Portions contributed by others as indicated. All rights reserved.

A worldwide, royalty-free, non-exclusive right to copy, modify, create
derivatives, and use, in source and binary forms, is hereby granted, subject to
acceptance of this license. Performance of any of the aforementioned acts
indicates acceptance to be bound by the following terms and conditions:

* Copies of source code, in whole or in part, must retain the above copyright
notice, this list of conditions and the Disclaimer of Warranty.

* Use in binary form must retain the above copyright notice, this list of
conditions and the Disclaimer of Warranty in the documentation and/or other
materials provided with the distribution.

* Nothing in this license shall be deemed to grant any rights to trademarks,
copyrights, patents, trade secrets or any other intellectual property of
A.M.P.A.S. or any contributors, except as expressly stated herein.

* Neither the name "A.M.P.A.S." nor the name of any other contributors to this
software may be used to endorse or promote products derivative of or based on
this software without express prior written permission of A.M.P.A.S. or the
contributors, as appropriate.

This license shall be construed pursuant to the laws of the State of California,
and any disputes related thereto shall be subject to the jurisdiction of the
courts therein.

Disclaimer of Warranty: THIS SOFTWARE IS PROVIDED BY A.M.P.A.S. AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND
NON-INFRINGEMENT ARE DISCLAIMED. IN NO EVENT SHALL A.M.P.A.S., OR ANY
CONTRIBUTORS OR DISTRIBUTORS, BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, RESITUTIONARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

WITHOUT LIMITING THE GENERALITY OF THE FOREGOING, THE ACADEMY SPECIFICALLY
DISCLAIMS ANY REPRESENTATIONS OR WARRANTIES WHATSOEVER RELATED TO PATENT OR
OTHER INTELLECTUAL PROPERTY RIGHTS IN THE ACES CONTAINER REFERENCE
IMPLEMENTATION, OR APPLICATIONS THEREOF, HELD BY PARTIES OTHER THAN A.M.P.A.S.,
WHETHER DISCLOSED OR UNDISCLOSED.
"""

__author__ = 'Haarm-Pieter Duiker'
__copyright__ = 'Copyright (C) 2015 Academy of Motion Picture Arts and Sciences'
__maintainer__ = 'Academy of Motion Picture Arts and Sciences'
__email__ = 'acessupport@oscars.org'
__status__ = 'Production'

__major_version__ = '1'
__minor_version__ = '0'
__change_version__ = '0'
__version__ = '.'.join((__major_version__,
                        __minor_version__,
                        __change_version__))

import os

import aces.clf as clf
from aces.lutFormats import *
from aces.lutFormats.LutFormat import *


class LutFormatCUBE(LutFormat):
    "A class that implements IO for Resolve .cube 3D LUT format"

    # Descriptions, extensions and capabilities for this class
    formatType = "cube"
    formats = [
        ["cube - 3D LUT format",
         "cube",
         [IO_CAPABILITY_READ]]
        ]

    def __init__(self):
        "%s - Initialize the standard class variables" % LutFormatCUBE.formatType
        LutFormat.__init__(self)
    # __init__

    @classmethod
    def read(cls,
             lutPath,
             inverse=False,
             interpolation='linear',
             inversesUseIndexMaps=True,
             inversesUseHalfDomain=True):
        print( "%s format read - %s" % (LutFormatCUBE.formatType, lutPath) )
        extension = os.path.splitext(lutPath)[1][1:].strip().lower()

        if extension == 'cube':
            return LutFormatCUBE.readCUBE3D(lutPath,
                inverse,
                interpolation)

        return False

    # XXX
    # Need to warn user about the lack of an inverse for 3D LUTs
    # Or implement one. That would be slow in Python (or C, or OpenCL) though
    @staticmethod
    def readCUBE3D(lutPath, inverse=False, interpolation='linear'):
        with open(lutPath) as f:
            lines = f.read().splitlines()

        # Translate between different names for the same interpolation if necessary
        ocioToCLFInterpolation = {'linear':'trilinear'}
        if interpolation in ocioToCLFInterpolation:
            interpolation = ocioToCLFInterpolation[interpolation]

        lut_start = -1
        size = 0
        resolution = [0, 0, 0]
        samples = []
        valid = False

        for idx, line in enumerate(lines):
            if not line:
                continue

            tokens = line.split()
            if tokens[0] == "LUT_3D_SIZE":
                size = int(tokens[1])
                resolution = [size, size, size]
                valid = True
            elif tokens[0] == "LUT_3D_INPUT_RANGE":
                min, max = map(float, tokens[1:])
                if min != 0 or max != 1:
                    print("Unsupported range operator")
            elif len(tokens) == 3 and not line.startswith('#'):
                lut_start = idx
                break

        if valid and lut_start > 0:
            # Logic from LutCSP.py
            # CUBE incremements LUT samples red, then green, then blue
            # CLF incremements LUT samples blue, then green, then red
            # so we need to move samples around
            samples = [0.0] * size * size * size * 3
            cubeIndex = 0

            for line in lines[lut_start:]:
                tokens = line.split()
                if len(tokens) != 3:
                    break

                # Convert from sample number to LUT index, CUBE-style
                indexR = cubeIndex % size
                indexG = (cubeIndex // size) % size
                indexB = cubeIndex // (size * size)

                # Convert from LUT index to sample number, CLF-style
                clfIndex = int((indexR * size + indexG) * size + indexB)
                clfIndex *= 3

                samples[clfIndex:clfIndex+3] = list(map(float, tokens))
                cubeIndex += 1

        #
        # Create ProcessNodes
        #
        lutpn = clf.LUT3D(clf.bitDepths["FLOAT16"], clf.bitDepths["FLOAT16"], "lut3d", "lut3d", interpolation=interpolation)
        lutpn.setArray(resolution, samples)

        return [lutpn]

# LutFormatCUBE
