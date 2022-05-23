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

    def __init__(self, handle, row, col) -> None:

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

        # self.dacs = {
        #     'blres': 10,
        #     'nu1': 0,
        #     'vn1': 10,
        #     'vnfb': 10,
        #     'vnfoll': 2,
        #     'nu5': 0,
        #     'nu6': 0,
        #     'nu7': 0,
        #     'nu8': 0,
        #     'vn2': 0,
        #     'vnfoll2': 10,
        #     'vnbias': 10,
        #     'vpload': 2,
        #     'nu13': 0,
        #     'vncomp': 20,
        #     'vpfoll': 20,
        #     'nu16': 0,
        #     'vprec': 30,
        #     'vnrec': 30
        # }
        bitconfig_col = 0
        if row==0:bitconfig_col=0b001_11111_11111_11111_11111_11111_11111_11100
        elif row==1:  bitconfig_col=0b001_11111_11111_11111_11111_11111_11111_11010
        elif row==2:  bitconfig_col=0b001_11111_11111_11111_11111_11111_11111_10110
        elif row==3:  bitconfig_col=0b001_11111_11111_11111_11111_11111_11111_01110
        elif row==4:  bitconfig_col=0b001_11111_11111_11111_11111_11111_11110_11110
        elif row==5:  bitconfig_col=0b001_11111_11111_11111_11111_11111_11101_11110
        elif row==6:  bitconfig_col=0b001_11111_11111_11111_11111_11111_11011_11110
        elif row==7:  bitconfig_col=0b001_11111_11111_11111_11111_11111_10111_11110
        elif row==8:  bitconfig_col=0b001_11111_11111_11111_11111_11111_01111_11110
        elif row==9:  bitconfig_col=0b001_11111_11111_11111_11111_11110_11111_11110
        elif row==10: bitconfig_col=0b001_11111_11111_11111_11111_11101_11111_11110
        elif row==11: bitconfig_col=0b001_11111_11111_11111_11111_11011_11111_11110
        elif row==12: bitconfig_col=0b001_11111_11111_11111_11111_10111_11111_11110
        elif row==13: bitconfig_col=0b001_11111_11111_11111_11111_01111_11111_11110
        elif row==14: bitconfig_col=0b001_11111_11111_11111_11110_11111_11111_11110
        elif row==15: bitconfig_col=0b001_11111_11111_11111_11101_11111_11111_11110
        elif row==16: bitconfig_col=0b001_11111_11111_11111_11011_11111_11111_11110
        elif row==17: bitconfig_col=0b001_11111_11111_11111_10111_11111_11111_11110
        elif row==18: bitconfig_col=0b001_11111_11111_11111_01111_11111_11111_11110
        elif row==19: bitconfig_col=0b001_11111_11111_11110_11111_11111_11111_11110
        elif row==20: bitconfig_col=0b001_11111_11111_11101_11111_11111_11111_11110
        elif row==21: bitconfig_col=0b001_11111_11111_11011_11111_11111_11111_11110
        elif row==22: bitconfig_col=0b001_11111_11111_10111_11111_11111_11111_11110
        elif row==23: bitconfig_col=0b001_11111_11111_01111_11111_11111_11111_11110
        elif row==24: bitconfig_col=0b001_11111_11110_11111_11111_11111_11111_11110
        elif row==25: bitconfig_col=0b001_11111_11101_11111_11111_11111_11111_11110
        elif row==26: bitconfig_col=0b001_11111_11011_11111_11111_11111_11111_11110
        elif row==27: bitconfig_col=0b001_11111_10111_11111_11111_11111_11111_11110
        elif row==28: bitconfig_col=0b001_11111_01111_11111_11111_11111_11111_11110
        elif row==29: bitconfig_col=0b001_11110_11111_11111_11111_11111_11111_11110
        elif row==30: bitconfig_col=0b001_11101_11111_11111_11111_11111_11111_11110
        elif row==31: bitconfig_col=0b001_11011_11111_11111_11111_11111_11111_11110
        elif row==32: bitconfig_col=0b001_10111_11111_11111_11111_11111_11111_11110
        elif row==33: bitconfig_col=0b001_01111_11111_11111_11111_11111_11111_11110
        elif row==34: bitconfig_col=0b000_11111_11111_11111_11111_11111_11111_11110

        #self.recconfig = {'ColConfig0': 0b011_00000_00000_00000_00000_00000_00000_00001}
        if col==0:
            self.recconfig = {'ColConfig0': bitconfig_col}
        else:
            self.recconfig = {'ColConfig0': 0b001_11111_11111_11111_11111_11111_11111_11110}
        print('row',row,'col',col,bitconfig_col)
        i = 1
        while i < 35:
            if i==col:
                self.recconfig[f'ColConfig{i}'] = bitconfig_col
            else:
                self.recconfig[f'ColConfig{i}'] = 0b001_11111_11111_11111_11111_11111_11111_11110
            #self.recconfig[f'ColConfig{i}'] = 0b001_11111_11111_11111_11111_11111_11111_11110
            #if i<3:
            #self.recconfig[f'ColConfig{i}'] = 0b011_00000_00000_00000_00000_00000_00000_00001
            #else: self.recconfig[f'ColConfig{i}'] = 0b001_11111_11111_11111_11111_11111_11111_11110
# 4,5,7,14,16,18 noisy. 6,9 less noisy
            #if i<21 and i!=4 and i!=5 and i!=6 and i!=7 and i!=9 and i!=14 and i!=16 and i!=18 and i!=19 :
            #            self.recconfig[f'ColConfig{i}'] = 0b011_11111_11111_11111_11111_11111_11111_11101
            #else:
            #            self.recconfig[f'ColConfig{i}'] = 0b001_11111_11111_11111_11111_11111_11111_11110
            i += 1

        #self.recconfig = {'ColConfig34': 0b111_11111_11111_11111_11111_11111_11111_11101}
        #self.recconfig = {'ColConfig1': 0b011_11111_11111_11111_11111_11111_11111_11011}

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
