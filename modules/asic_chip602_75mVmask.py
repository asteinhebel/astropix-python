
# -*- coding: utf-8 -*-
""""""
"""
Created on Fri Jun 25 16:28:27 2021

@author: Nicolas Striebig

Astropix2 Configbits
"""
from bitstring import BitArray
from dataclasses import dataclass

from modules.nexysio import Nexysio

@dataclass
class Astropix2Config:
    # TODO Improvement: Move Configbits to dedicated dataclass
    pass


class Asic(Nexysio):
    """Configure ASIC"""

    def __init__(self, handle) -> None:

        self._handle = handle

        self.digitalconfig = {'interrupt_pushpull': 1}

        i = 1
        while i < 19:
            self.digitalconfig[f'En_Inj{i}'] = 0
            i += 1

        self.digitalconfig['ResetB'] = 0

        i = 0
        while i < 8:
            self.digitalconfig[f'Extrabit{i}'] = 1
            i += 1
        while i < 15:
            self.digitalconfig[f'Extrabit{i}'] = 0
            i += 1

        self.biasconfig = {
            'DisHiDR': 0,
            'q01': 0,
            'qon0': 0,
            'qon1': 1,
            'qon2': 0,
            'qon3': 1,
        }

        
	#new DACs
        self.dacs = {
            'blres': 0,
            'nu1': 0,
            'vn1': 20,
            'vnfb': 1,
            'vnfoll': 10,
            'nu5': 0,
            'nu6': 0,
            'nu7': 0,
            'nu8': 0,
            'vn2': 0,
            'vnfoll2': 1,
            'vnbias': 0,
            'vpload': 5,
            'nu13': 0,
            'vncomp': 2,
            'vpfoll': 60,
            'nu16': 0,
            'vprec': 30,
            'vnrec': 30
        }
        """
	#old DACs
        self.dacs = {
            'blres': 10,
            'nu1': 0,
            'vn1': 10,
            'vnfb': 10,
            'vnfoll': 2,
            'nu5': 0,
            'nu6': 0,
            'nu7': 0,
            'nu8': 0,
            'vn2': 0,
            'vnfoll2': 10,
            'vnbias': 10,
            'vpload': 2,
            'nu13': 0,
            'vncomp': 20,
            'vpfoll': 20,
            'nu16': 0,
            'vprec': 30,
            'vnrec': 30
        }
        
	#test DACs
        self.dacs = {
            'blres': 0,
            'nu1': 0,
            'vn1': 1,
            'vnfb': 1,
            'vnfoll': 2,
            'nu5': 0,
            'nu6': 0,
            'nu7': 0,
            'nu8': 0,
            'vn2': 0,
            'vnfoll2': 1,
            'vnbias': 0,
            'vpload': 5,
            'nu13': 0,
            'vncomp': 2,
            'vpfoll': 60,
            'nu16': 0,
            'vprec': 30,
            'vnrec': 30
        }
        """

	#Implement pixel mask from output of noiseVisualiation.py (after running noise scan)
        # 75mV noise scan with anding two runs
        bitconfig_col =  0b111_00000_00000_01010_10000_00100_10000_00011
        self.recconfig = {'ColConfig0': bitconfig_col}
        
        self.recconfig[f'ColConfig1'] = 0b000_11010_01000_00001_10101_10010_11100_00100
        self.recconfig[f'ColConfig2'] = 0b001_00000_01001_01000_00010_10010_01000_10010
        self.recconfig[f'ColConfig3'] = 0b000_01101_01010_00011_11011_00000_11111_00000
        self.recconfig[f'ColConfig4'] = 0b000_00010_01000_00010_00000_00101_01111_00000
        self.recconfig[f'ColConfig5'] = 0b000_00010_01101_00001_11000_10001_00000_11100
        self.recconfig[f'ColConfig6'] = 0b000_00110_01011_10000_01000_01000_00110_00000
        self.recconfig[f'ColConfig7'] = 0b001_10100_01101_00010_10100_01000_10000_00000
        self.recconfig[f'ColConfig8'] = 0b000_10010_01100_00100_00100_01000_11010_01010
        self.recconfig[f'ColConfig9'] = 0b001_00010_10010_10111_10100_11000_10001_10100
        self.recconfig[f'ColConfig10'] = 0b000_01011_01010_11001_00010_00111_00100_00010
        self.recconfig[f'ColConfig11'] = 0b000_10011_00000_01010_10100_01101_10010_01010
        self.recconfig[f'ColConfig12'] = 0b000_10011_01000_10000_00100_11111_00001_00000
        self.recconfig[f'ColConfig13'] = 0b000_01101_00010_10000_00000_00000_10010_00000
        self.recconfig[f'ColConfig14'] = 0b000_01001_00101_00100_01000_00011_11110_01100
        self.recconfig[f'ColConfig15'] = 0b000_01100_01000_00000_00011_00001_10000_01000
        self.recconfig[f'ColConfig16'] = 0b001_01100_00001_10000_10101_10100_00100_10100
        self.recconfig[f'ColConfig17'] = 0b000_00000_10111_10100_01011_10000_00001_11000
        self.recconfig[f'ColConfig18'] = 0b001_00010_01110_11110_10011_00000_10011_00000
        self.recconfig[f'ColConfig19'] = 0b000_00100_00100_01101_10110_00000_00100_00000
        self.recconfig[f'ColConfig20'] = 0b000_01100_00000_10000_00000_00110_00001_10000
        self.recconfig[f'ColConfig21'] = 0b000_01100_00100_00101_10000_01111_00011_00010
        self.recconfig[f'ColConfig22'] = 0b001_01100_00100_11000_10011_00110_01010_10100
        self.recconfig[f'ColConfig23'] = 0b000_00010_00100_01100_00000_10001_00001_01100
        self.recconfig[f'ColConfig24'] = 0b000_00100_00110_00001_11000_01111_00110_01000
        self.recconfig[f'ColConfig25'] = 0b001_00100_00010_10011_10001_01011_01000_00000
        self.recconfig[f'ColConfig26'] = 0b000_10000_11100_11010_00111_00100_00110_01100
        self.recconfig[f'ColConfig27'] = 0b000_01100_10010_10001_11101_01110_00000_00000
        self.recconfig[f'ColConfig28'] = 0b000_01101_00100_10010_01110_11000_10001_10100
        self.recconfig[f'ColConfig29'] = 0b001_10000_01111_01010_10001_10001_01001_00000
        self.recconfig[f'ColConfig30'] = 0b000_10111_00010_10000_11111_10000_00010_00010
        self.recconfig[f'ColConfig31'] = 0b001_01111_01011_01011_11001_01010_00001_01000
        self.recconfig[f'ColConfig32'] = 0b000_00110_00000_00011_10000_00110_01100_10100
        self.recconfig[f'ColConfig33'] = 0b000_10010_00000_01100_01100_00101_11001_00100
        self.recconfig[f'ColConfig34'] = 0b000_10000_00100_01000_01100_11010_00100_00000
        """
        i = 1
        while i < 35:
            self.recconfig[f'ColConfig{i}'] = 0b001_11111_11111_11111_11111_11111_11111_11110
            i += 1
        """

    @staticmethod
    def __int2nbit(value: int, nbits: int) -> BitArray:
        """Convert int to 6bit bitarray

        :param value: DAC value 0-63
        """

        try:
            return BitArray(uint=value, length=nbits)
        except ValueError:
            print(f'Allowed Values 0 - {2**nbits-1}')

    def gen_asic_vector(self, msbfirst: bool = False) -> BitArray:
        """Generate asic bitvector from digital, bias and dacconfig

        :param msbfirst: Send vector MSB first
        """

        bitvector = BitArray()

        for value in self.digitalconfig.values():
            bitvector.append(self.__int2nbit(value, 1))

        for value in self.biasconfig.values():
            bitvector.append(self.__int2nbit(value, 1))

        for value in self.dacs.values():
            bitvector.append(self.__int2nbit(value, 6))

        for value in self.recconfig.values():
            bitvector.append(self.__int2nbit(value, 38))

        if not msbfirst:
            bitvector.reverse()

        # print(f'Bitvector: {bitvector} \n')

        return bitvector

    def update_asic(self) -> None:
        """Update ASIC"""

        # Not needed for v2
        # dummybits = self.gen_asic_pattern(BitArray(uint=0, length=245), True)

        # Write config
        asicbits = self.gen_asic_pattern(self.gen_asic_vector(), True)
        self.write(asicbits)

    def readback_asic(self):
        asicbits = self.gen_asic_pattern(self.gen_asic_vector(), True, readback_mode = True)
        print(asicbits)
        self.write(asicbits)
