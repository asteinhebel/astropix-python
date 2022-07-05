
# -*- coding: utf-8 -*-
""""""
"""
Created on Sat Jun 26 00:10:56 2021

@author: Nicolas Striebig
"""

from modules.asic import Asic
from modules.injectionboard import Injectionboard
from modules.nexysio import Nexysio
from modules.voltageboard import Voltageboard
from modules.decode import Decode

from utils.utils import wait_progress

import binascii

import os
import time

def main(row,col,str_file_loop):

    nexys = Nexysio()

    # Open FTDI Device with Index 0
    #handle = nexys.open(0)
    handle = nexys.autoopen()
    #nexys.close()
    #return 0

    # Write and read directly to register
    # Example: Write 0x55 to register 0x09 and read it back
    nexys.write_register(0x09, 0x55, True)
    nexys.read_register(0x09)

    nexys.spi_reset()
    nexys.sr_readback_reset()

    #
    # Configure ASIC
    #

    # Write to asicSR
    asic = Asic(handle,row,col)
    asic.update_asic()

    # Example: Update Config Bit
    # asic.digitalconfig['En_Inj17'] = 1
    # asic.dacs['vn1'] = 63
    # asic.update_asic()

    #
    # Configure Voltageboard
    #

    # Configure 8 DAC Voltageboard in Slot 4 with list values
    # 3 = Vcasc2, 4=BL, 7=Vminuspix, 8=Thpix
    vboard1 = Voltageboard(handle, 4, (8, [0, 0, 1.1, 1, 0, 0, 1, 1.075]))

    # Set measured 1V for one-point calibration
    vboard1.vcal = 0.989
    vboard1.vsupply = 2.7# 3.3

    # Update voltageboards
    vboard1.update_vb()

    # Write only first 3 DACs, other DACs will be 0
    # vboard1.dacvalues = (8, [1.2, 1, 1])
    # vboard1.update_vb()

    #
    # Configure Injectionboard
    #

    # Set Injection level
    injvoltage = Voltageboard(handle, 3, (2, [0.4, 0.0]))
    injvoltage.vcal = vboard1.vcal
    injvoltage.vsupply = vboard1.vsupply
    injvoltage.update_vb()

    inj = Injectionboard(handle)

    # Set Injection Params for 330MHz patgen clock
    inj.period = 100
    inj.clkdiv = 400
    inj.initdelay = 10000
    inj.cycle = 0
    inj.pulsesperset = 1

    #
    # SPI
    #

    # Enable SPI
    nexys.spi_enable()
    nexys.spi_reset()

    # Set SPI clockdivider
    # freq = 100 MHz/spi_clkdiv
    nexys.spi_clkdiv = 255

    #asic.dacs['vn1'] = 5

    # Generate bitvector for SPI ASIC config
    asic_bitvector = asic.gen_asic_vector()
    spi_data = nexys.asic_spi_vector(asic_bitvector, True, 10)

    # Write Config via spi
    # nexys.write_spi(spi_data, False, 8191)

    # Send Routing command
    nexys.send_routing_cmd()

    # Reset SPI Read FIFO

    #inj.start()
    inj.stop()

    wait_progress(1)
    #wait_progress(3)

    #not using the decoder - not saving any digital output
    #decode = Decode()

    #save voltage information in logTestBeam/ for each file
    #DO NOT DELETE THIS OR NEXYS WILL NOT CONNECT
    timestr = time.strftime("beam_%Y%m%d-%H%M%S")
    file = open("logTestBeam/%s.log" % timestr, "w")
    file.write(f"Voltageboard settings: {vboard1.dacvalues}\n")
    file.write(f"Digital: {asic.digitalconfig}\n")
    file.write(f"Biasblock: {asic.biasconfig}\n")
    file.write(f"DAC: {asic.dacs}\n")
    file.write(f"Receiver: {asic.recconfig}\n\n")
    file.close()

    readout = bytearray()

    j=0
    h=0

    loopMax=5

    while j<loopMax:
        #print("Reg: {}".format(int.from_bytes(nexys.read_register(70),"big")))
        j += 1
        #time.sleep(0.1)
        
        #just check interrupt signal and record if it was triggered
        #don't store any digital data from these runs - too time consuming
        if(int.from_bytes(nexys.read_register(70),"big") == 0):
            h += 1
            time.sleep(0.1)

        if j%100==0:
            print(f"On test {j}")

    print(f"Pixel ({row},{col}) had {h} / {loopMax} counts")
    tmp_file=open(str_file_loop,"a+")
    tmp_file.write(f"{col}\t{row}\t{h}\t{timestr}\n")
    tmp_file.close()

    # Close connection
    nexys.close()


if __name__ == "__main__":

    dirName="June_LBNL/noiseMap_06_22_2022_601_75mV_lbnlTestFinal"
    if not os.path.exists(dirName):
        os.makedirs(dirName)

    #for col in range(0,1):
    for col in range(0,35):
        timestrloop = time.strftime("%Y%m%d-%H%M%S")
        filename="%s/lognoise_Col%s_%s.txt" %(dirName, col, timestrloop)
        file_loop = open(filename,"w")
        file_loop.write("Col\tRow\tCount\tTime\n")
        file_loop.close()
        for row in range(0,35):
        #for row in range(28,35):
            try:
               print(f"Column {col}, row {row}")
               main(row,col,filename)
            except:
               pass
            #time.sleep(1)
