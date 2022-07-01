
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

import os,sys
import time

import hitplotter
import argparse
import numpy as np

def main(args):

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
    asic = Asic(handle)
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
    vboard1 = Voltageboard(handle, 4, (8, [0, 0, 1.1, 1, 0, 0, 1, 1.1]))

    # Set measured 1V for one-point calibration
    vboard1.vcal = 0.989
    vboard1.vsupply = 2.7 #3.3

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

    wait_progress(3)

    decode = Decode()
    
    
    name = '' if (args.name == '') else  args.name+"_"
  
    
    #dir="noise"
    dir = "June_LBNL"
    #dir="source"

    #raw data file
    timestr = time.strftime("beam_%Y%m%d-%H%M%S")
    file = open("%s/%s%s.log" % (dir,name, timestr), "w")
    file.write(f"Voltageboard settings: {vboard1.dacvalues}\n")
    file.write(f"Digital: {asic.digitalconfig}\n")
    file.write(f"Biasblock: {asic.biasconfig}\n")
    file.write(f"DAC: {asic.dacs}\n")
    file.write(f"Receiver: {asic.recconfig}\n\n")

    #decoded data file
    timestr1 = time.strftime("beamDigital_%Y%m%d-%H%M%S")
    fileTyp = 'csv' if args.saveAsCSV else 'txt'
    delim = ',' if args.saveAsCSV else '\t'
    file1 = open("%s/%s%s.%s" % (dir,name, timestr1,fileTyp), "w")
    if not args.saveAsCSV:
        file1.write(f"Voltageboard settings: {vboard1.dacvalues}\n")
        file1.write(f"Digital: {asic.digitalconfig}\n")
        file1.write(f"Biasblock: {asic.biasconfig}\n")
        file1.write(f"DAC: {asic.dacs}\n")
        file1.write(f"Receiver: {asic.recconfig}\n\n")

    readout = bytearray()

    i = 0 #interrupt index
    file1.write(f"NEvent{delim}ChipId{delim}Payload{delim}"
        f"Locatn{delim}Row/Col{delim}tStamp{delim}"
        f"MSB{delim}LSB{delim}ToT{delim}ToT(us){delim}RealTime\n"
    )

    #set up the real-time plot
    #to save some of the event plots, change outdir to the name of the directory to save the plots in.
    plotter = hitplotter.HitPlotter(35, outdir=args.outdir)

    # This reads out the hits register if the interupt is present
    # By doing this the FPGA dump is ignored

    if(int.from_bytes(nexys.read_register(70),"big") == 0): #if interrupt signal
        time.sleep(0.05)
        timestmp=time.time()
        nexys.write_spi_bytes(20)
        readout = nexys.read_spi_fifo()
    

    try:
        while True:
            #print("Reg: {}".format(int.from_bytes(nexys.read_register(70),"big")))
            if(int.from_bytes(nexys.read_register(70),"big") == 0): #if interrupt signal
                time.sleep(0.05)
                timestmp=time.time()
                nexys.write_spi_bytes(20)
                readout = nexys.read_spi_fifo()
                file.write(f"{i}\t")
                file.write(str(binascii.hexlify(readout)))
                file.write("\n")
                print(binascii.hexlify(readout))

                decList=decode.decode_astropix2_hits(decode.hits_from_readoutstream(readout), i, file1, timestmp, False, args.saveAsCSV) #last arg (bool) = "print_only", if False then return list of deocded info
                file1.write("\n")

                if args.showhits:
                    rows,columns=[],[]
                    if len(decList)>0:#safeguard against bad readouts without recorded decodable hits
                        #Isolate row and column information from array returned from decoder
                        decList=np.array(decList)
                        location = np.array(decList[:,0])
                        rowOrCol = np.array(decList[:,1])
                        rows = location[rowOrCol==0]
                        columns = location[rowOrCol==1]
                    plotter.plot_event( rows, columns, i)

                i +=1
    except KeyboardInterrupt:
        # Close connection cleanly
        nexys.close()

if __name__ == "__main__":


    parser = argparse.ArgumentParser(description='Take AstroPix data during testbeam')
    parser.add_argument('-n', '--name', default='', required=False,
                    help='Option to give extra name to output files upon running')
    parser.add_argument('-s', '--showhits', action='store_true',
                    default=False, required=False,
                    help='Display hits in real time during data taking')
    parser.add_argument('-o', '--outdir', default=None, required=False,
                    help='output directory for real-time plots. If None, do not save plots. Events with exactly one row and one column hit are not saved.')
    parser.add_argument('-c', '--saveAsCSV', action='store_true', 
                    default=False, required=False, 
                    help='save output files as CSV. If False, save as txt')

    args = parser.parse_args()
    
    main(args)
