# -*- coding: utf-8 -*-
""""""
"""
Created on Tue Jul 12 20:07:13 2021

@author: Nicolas Striebig
"""
import binascii
import logging

# from tqdm import tqdm

from bitstring import BitArray

from time import sleep

from modules.setup_logger import logger


# SR
SPI_SR_BROADCAST    = 0x7E
SPI_SR_BIT0         = 0x00
SPI_SR_BIT1         = 0x01
SPI_SR_LOAD         = 0x03
SPI_EMPTY_BYTE      = 0x00

# Registers
SPI_CONFIG_REG      = 0x15
SPI_CLKDIV_REG      = 0x16
SPI_WRITE_REG       = 0x17
SPI_READ_REG        = 0x18
SPI_READBACK_REG    = 0x3C
SPI_READBACK_REG_CONF = 0x3D

# Daisychain 3bit Header + 5bit ID
SPI_HEADER_EMPTY    = 0b001 << 5
SPI_HEADER_ROUTING  = 0b010 << 5
SPI_HEADER_SR       = 0b011 << 5

logger = logging.getLogger(__name__)


class Spi:
    """
    Nexys SPI Communication

    Registers:
    | SPI_Config Register 21 (0x15)
        | 0 Write FIFO reset
        | 1	Write FIFO empty flag (read-only)
        | 2	Write FIFO full flag (read-only)
        | 3	Read FIFO reset
        | 4	Read FIFO empty flag (read-only)
        | 5	Read FIFO full flag (read-only)
        | 6	SPI Readback Enable
        | 7	SPI module reset
    | SPI_CLKDIV Register 22
    | SPI_Write Register 23
    | SPI_Read Register 24
    """
    def __init__(self):
        self._spi_clkdiv = 16

    @staticmethod
    def set_bit(value, bit):
        return value | (1 << bit)

    @staticmethod
    def clear_bit(value, bit):
        return value & ~(1 << bit)

    def get_spi_config(self) -> int:
        return int.from_bytes(self.read_register(SPI_CONFIG_REG), 'big')

    def get_sr_readback_config(self) -> int:
        return int.from_bytes(self.read_register(SPI_READBACK_REG_CONF), 'big')

    def asic_spi_vector(self, value: bytearray, load: bool, n_load: int = 10, broadcast: bool = True, chipid: int = 0) -> bytearray:
        """
        Write ASIC config via SPI

        :param value: Bytearray vector
        :param load: Load signal
        :param n_load: Length of load signal

        :param broadcast: Enable Broadcast
        :param chipid: Set chipid if !broadcast

        :returns: SPI ASIC config pattern
        """

        # Number of Bytes to write
        length = len(value) * 5 + 4

        logger.info("SPI Write Asic Config\n")
        logger.debug(
            "SPI Write Asic Config"
            f"Length: {length}\n"
            f"Data ({len(value)} Bits): {value}\n"
        )

        # Write SPI SR Command to set MUX
        if broadcast:
            data = bytearray([SPI_SR_BROADCAST])
        else:
            data = bytearray([SPI_HEADER_SR | chipid])

        # data
        for bit in value:

            sin = SPI_SR_BIT1 if bit == 1 else SPI_SR_BIT0

            data.append(sin)

        # Append Load signal and empty bytes
        if load:

            data.extend([SPI_SR_LOAD] * n_load)

            data.extend([SPI_EMPTY_BYTE] * n_load)

        return data

    @property
    def spi_clkdiv(self):
        """SPI Clockdivider"""

        return self._spi_clkdiv

    @spi_clkdiv.setter
    def spi_clkdiv(self, clkdiv: int):

        if 0 <= clkdiv <= 65535:
            self._spi_clkdiv = clkdiv
            self.write_register(SPI_CLKDIV_REG, clkdiv, True)

    def spi_enable(self, enable: bool = True) -> None:
        """
        Enable or disable SPI

        Set SPI Reset bit to 0/1 active-low
        :param enable: Enable
        """
        configregister = self.get_spi_config()

        # Set Reset bits 1
        configregister = self.clear_bit(configregister, 7) if enable else self.set_bit(configregister, 7)

        logger.debug(f'Configregister: {hex(configregister)}')
        self.write_register(SPI_CONFIG_REG, configregister, True)

    def spi_reset(self) -> None:
        """
        Reset SPI

        Resets SPI module and FIFOs
        """

        reset_bits = [0, 3]

        for bit in reset_bits:

            configregister = self.get_spi_config()

            # Set Reset bits 1
            configregister = self.set_bit(configregister, bit)
            self.write_register(SPI_CONFIG_REG, configregister, True)

            configregister = self.get_spi_config()

            # Set Reset bits and readback bit 0
            configregister = self.clear_bit(configregister, bit)
            self.write_register(SPI_CONFIG_REG, configregister, True)

    def sr_readback_reset(self) -> None:
        """
        Reset SPI

        Resets SPI module and FIFOs
        """

        reset_bits = [0]

        for bit in reset_bits:

            configregister = self.get_sr_readback_config()

            # Set Reset bits 1
            configregister = self.set_bit(configregister, bit)
            self.write_register(SPI_READBACK_REG_CONF, configregister, True)

            configregister = self.get_sr_readback_config()

            # Set Reset bits and readback bit 0
            configregister = self.clear_bit(configregister, bit)
            self.write_register(SPI_READBACK_REG_CONF, configregister, True)

    def direct_write_spi(self, data: bytes) -> None:
        """
        Direct write to SPI Write Register

        :param data: Data
        """
        self.write_registers(SPI_WRITE_REG, data, True)

    def read_spi(self, num: int):
        """
        Direct Read from SPI Read Register

        :param num: Number of Bytes

        :returns: SPI Read data
        """

        return self.read_register(SPI_READ_REG, num)

    def read_spi_readback(self, num: int):
        """
        Direct Read from SPI Read Register

        :param num: Number of Bytes

        :returns: SPI Read data
        """

        return self.read_register(SPI_READBACK_REG, num)

    def read_spi_readoutmode(self):
        """ Continous readout """
        pass

    def read_spi_fifo(self) -> bytearray:
        """ Read Data from SPI FIFO until empty """

        idle_bytes = 0
        count_hits = 0
        idle_bytes_temp = 0

        read_stream = bytearray()
        i=0

        while not(self.get_spi_config() & 16):
            readbuffer = self.read_spi(8)

            read_stream.extend(readbuffer)

            if (readbuffer == b'\xaf\x2f\x2f\x2f\x2f\x2f\x2f\x2f') | (readbuffer == b'\x2f\x2f\x2f\x2f\x2f\x2f\x2f\x2f'):
                idle_bytes += 1
                idle_bytes_temp += 1
                logger.debug('Read SPI: IDLE')
            else:
                count_hits += 1

                if (idle_bytes_temp > 0):
                    logger.debug(f'Read SPI: {idle_bytes_temp} IDLE Frames')
                    idle_bytes_temp = 0

                logger.debug(f'Read SPI: {binascii.hexlify(readbuffer)}')

            sleep(0.01)

        if idle_bytes > 0:
            logger.info(f'Read SPI: {idle_bytes} IDLE Frames')

        logger.info(f'Total {(idle_bytes+count_hits)*8}Bytes: Number of Frames with hits: {count_hits}')

        return read_stream

    def read_spi_fifo_readback(self) -> bytearray:
        """ Read Data from SPI FIFO until empty """

        idle_bytes = 0
        count_hits = 0
        idle_bytes_temp = 0

        read_stream = bytearray()
        i=0


        while not(self.get_sr_readback_config() & 16):
            readbuffer = self.read_spi_readback(8)

            read_stream.extend(readbuffer)

            # if (readbuffer == b'\xaf\x2f\x2f\x2f\x2f\x2f\x2f\x2f') | (readbuffer == b'\x2f\x2f\x2f\x2f\x2f\x2f\x2f\x2f'):
            #     idle_bytes += 1
            #     idle_bytes_temp += 1
            #     logger.debug('Read SPI: IDLE')
            # else:
            #     count_hits += 1

            #     if (idle_bytes_temp > 0):
            #         logger.debug(f'Read SPI: {idle_bytes_temp} IDLE Frames')
            #         idle_bytes_temp = 0

            #     logger.debug(f'Read SPI: {binascii.hexlify(readbuffer)}')

            sleep(0.01)

        if idle_bytes > 0:
            logger.info(f'Read SPI: {idle_bytes} IDLE Frames')

        logger.info(f'Total {(idle_bytes+count_hits)*8}Bytes: Number of Frames with hits: {count_hits}')

        return read_stream

    def write_spi_bytes(self, n_bytes: int) -> None:
        """
        Write to SPI for readout

        :param n_bytes: Number of Bytes
        """

        if(n_bytes > 64000):
            n_bytes = 64000
            logger.warning("Cannot write more than 64000 Bytes")

        logger.info(f"SPI: Write {8 * n_bytes + 4} Bytes")
        self.write_spi(bytearray([SPI_HEADER_EMPTY] * n_bytes * 8), False, 8191)

    def send_routing_cmd(self) -> None:
        """
        Send routing cmd

        """
        logger.info("SPI: Send routing cmd")
        self.write_spi(bytearray([SPI_HEADER_EMPTY, 0, 0, 0, 0, 0, 0, 0]), False)

    def write_spi(self, data: bytearray, MSBfirst: bool = True, buffersize: int = 1023) -> None:
        """
        Write to Nexys SPI Write FIFO

        :param data: Bytearray vector
        :param MSBfirst: SPI MSB first
        :param buffersize: Buffersize
        """

        if not MSBfirst:

            for index, item in enumerate(data):

                item_rev = BitArray(uint=item, length=8)
                item_rev.reverse()

                data[index] = item_rev.uint

        logger.debug(f'SPIdata: {data}')

        waiting = True
        i = 0
        counter = buffersize / 3

        # WrFIFO bit positons in spi_config register 0x21
        compare_empty = 2
        compare_full = 4

        # Check if WrFIFO is Empty
        while waiting:

            # Convert Hex string to int
            result = self.get_spi_config()

            # Wait until WrFIFO empty
            if result & compare_empty:
                waiting = False

        while i < len(data):

            if counter > 0:
                writebuffer = bytearray(data[i:(i + 16)])

                i += 16
                counter -= 1

                self.direct_write_spi(bytes(writebuffer))

            else:
                result = self.get_spi_config()

                if result & compare_empty:
                    counter = buffersize / 3
                elif not result & compare_full:
                    counter = 1
