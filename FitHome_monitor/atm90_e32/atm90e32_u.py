from app_error import NoMonitor
from machine import Pin, SPI
import math
import time
import struct
from atm90e32_registers import *
# 
#  Copyright 2019, Margaret Johnson
#
# Update 11/24/2019 - added reactive power readings.


SPI_WRITE = 0
SPI_READ = 1


class ATM90e32:
    ##############################################################################

    def __init__(self, linefreq, pgagain, ugain, igainA, igainB, igainC):
        self._linefreq = linefreq
        self._pgagain = pgagain
        self._ugain = ugain
        self._igainA = igainA
        self._igainB = igainB
        self._igainC = igainC
        # HSPI Pins
        mosi_pin = Pin(13)
        miso_pin = Pin(12)
        sck_pin = Pin(14)
        cs_pin = 15
        # Chip select pin
        self.cs = Pin(cs_pin, Pin.OUT)
        # not using SPI, set to HIGH
        self.cs.on()

        # Setting SPI for what works for SAMD....
        # Doc on esp8266 SPI hw init: http://bit.ly/2ZhqeRB

        self.device = SPI(1, baudrate=200000, sck=sck_pin,
                          mosi=mosi_pin, miso=miso_pin, polarity=1, phase=1)
        self.num_write_failed = 0
        self._init_config()
        if self.num_write_failed > 0:  # Can't write to registers..probably not connected.
            print(self.num_write_failed)
            raise OSError(NoMonitor().number,
                          NoMonitor().explanation)

    def _init_config(self):
        # CurrentGainCT2 = 25498  #25498 - SCT-013-000 100A/50mA
        if (self._linefreq == 4485 or self._linefreq == 5231):
            # North America power frequency
            FreqHiThresh = 61 * 100
            FreqLoThresh = 59 * 100
            sagV = 90
        else:
            FreqHiThresh = 51 * 100
            FreqLoThresh = 49 * 100
            sagV = 190

        # calculation for voltage sag threshold - assumes we do not want to go under 90v for split phase and 190v otherwise
        # sqrt(2) = 1.41421356
        fvSagTh = (sagV * 100 * 1.41421356) / (2 * self._ugain / 32768)
        # convert to int for sending to the atm90e32.
        vSagTh = self._round_number(fvSagTh)

        self._spi_rw(SPI_WRITE, SoftReset, 0x789A)   # Perform soft reset
        # enable register config access
        self._spi_rw(SPI_WRITE, CfgRegAccEn, 0x55AA)
        self._spi_rw(SPI_WRITE, MeterEn, 0x0001)   # Enable Metering

        self._spi_rw(SPI_WRITE, SagTh, vSagTh)         # Voltage sag threshold
        # High frequency threshold - 61.00Hz
        self._spi_rw(SPI_WRITE, FreqHiTh, FreqHiThresh)
        # Lo frequency threshold - 59.00Hz
        self._spi_rw(SPI_WRITE, FreqLoTh, FreqLoThresh)
        self._spi_rw(SPI_WRITE, EMMIntEn0, 0xB76F)   # Enable interrupts
        self._spi_rw(SPI_WRITE, EMMIntEn1, 0xDDFD)   # Enable interrupts
        self._spi_rw(SPI_WRITE, EMMIntState0, 0x0001)  # Clear interrupt flags
        self._spi_rw(SPI_WRITE, EMMIntState1, 0x0001)  # Clear interrupt flags
        # ZX2, ZX1, ZX0 pin config
        self._spi_rw(SPI_WRITE, ZXConfig, 0x0A55)

        # Set metering config values (CONFIG)
        # PL Constant MSB (default) - Meter Constant = 3200 - PL Constant = 140625000
        self._spi_rw(SPI_WRITE, PLconstH, 0x0861)
        # PL Constant LSB (default) - this is 4C68 in the application note, which is incorrect
        self._spi_rw(SPI_WRITE, PLconstL, 0xC468)
        # Mode Config (frequency set in main program)
        self._spi_rw(SPI_WRITE, MMode0, self._linefreq)
        # PGA Gain Configuration for Current Channels - 0x002A (x4) # 0x0015 (x2) # 0x0000 (1x)
        self._spi_rw(SPI_WRITE, MMode1, self._pgagain)
        # Active Startup Power Threshold - 50% of startup current = 0.9/0.00032 = 2812.5
        # self._spi_rw(SPI_WRITE, PStartTh, 0x0AFC)
        # Testing a little lower setting...because readings aren't hapenng if power is off then
        # turned on....
        # Startup Power Threshold = .4/.00032 = 1250 = 0x04E2
        # Just checking with 0.
        self._spi_rw(SPI_WRITE, PStartTh, 0x0000)
        # Reactive Startup Power Threshold
        #  self._spi_rw(SPI_WRITE, QStartTh, 0x0AEC)
        self._spi_rw(SPI_WRITE, QStartTh, 0x0000)
        # Apparent Startup Power Threshold
        self._spi_rw(SPI_WRITE, SStartTh, 0x0000)
        # Active Phase Threshold = 10% of startup current = 0.06/0.00032 = 187.5
        # self._spi_rw(SPI_WRITE, PPhaseTh, 0x00BC)
        self._spi_rw(SPI_WRITE, PPhaseTh, 0x0000)
        self._spi_rw(SPI_WRITE, QPhaseTh, 0x0000)    # Reactive Phase Threshold
        # Apparent  Phase Threshold
        self._spi_rw(SPI_WRITE, SPhaseTh, 0x0000)

        # Set metering calibration values (CALIBRATION)
        self._spi_rw(SPI_WRITE, PQGainA, 0x0000)     # Line calibration gain
        self._spi_rw(SPI_WRITE, PhiA, 0x0000)        # Line calibration angle
        self._spi_rw(SPI_WRITE, PQGainB, 0x0000)     # Line calibration gain
        self._spi_rw(SPI_WRITE, PhiB, 0x0000)        # Line calibration angle
        self._spi_rw(SPI_WRITE, PQGainC, 0x0000)     # Line calibration gain
        self._spi_rw(SPI_WRITE, PhiC, 0x0000)        # Line calibration angle
        # A line active power offset
        self._spi_rw(SPI_WRITE, PoffsetA, 0x0000)
        # A line reactive power offset
        self._spi_rw(SPI_WRITE, QoffsetA, 0x0000)
        # B line active power offset
        self._spi_rw(SPI_WRITE, PoffsetB, 0x0000)
        # B line reactive power offset
        self._spi_rw(SPI_WRITE, QoffsetB, 0x0000)
        # C line active power offset
        self._spi_rw(SPI_WRITE, PoffsetC, 0x0000)
        # C line reactive power offset
        self._spi_rw(SPI_WRITE, QoffsetC, 0x0000)

        # Set metering calibration values (HARMONIC)
        # A Fund. active power offset
        self._spi_rw(SPI_WRITE, POffsetAF, 0x0000)
        # B Fund. active power offset
        self._spi_rw(SPI_WRITE, POffsetBF, 0x0000)
        # C Fund. active power offset
        self._spi_rw(SPI_WRITE, POffsetCF, 0x0000)
        # A Fund. active power gain
        self._spi_rw(SPI_WRITE, PGainAF, 0x0000)
        # B Fund. active power gain
        self._spi_rw(SPI_WRITE, PGainBF, 0x0000)
        # C Fund. active power gain
        self._spi_rw(SPI_WRITE, PGainCF, 0x0000)

        # Set measurement calibration values (ADJUST)
        self._spi_rw(SPI_WRITE, UgainA, self._ugain)      # A Voltage rms gain
        # A line current gain
        self._spi_rw(SPI_WRITE, IgainA, self._igainA)
        self._spi_rw(SPI_WRITE, UoffsetA, 0x0000)    # A Voltage offset
        self._spi_rw(SPI_WRITE, IoffsetA, 0x0000)    # A line current offset
        self._spi_rw(SPI_WRITE, UgainB, self._ugain)      # B Voltage rms gain
        # B line current gain
        self._spi_rw(SPI_WRITE, IgainB, self._igainB)
        self._spi_rw(SPI_WRITE, UoffsetB, 0x0000)    # B Voltage offset
        self._spi_rw(SPI_WRITE, IoffsetB, 0x0000)    # B line current offset
        self._spi_rw(SPI_WRITE, UgainC, self._ugain)      # C Voltage rms gain
        # C line current gain
        self._spi_rw(SPI_WRITE, IgainC, self._igainC)
        self._spi_rw(SPI_WRITE, UoffsetC, 0x0000)    # C Voltage offset
        self._spi_rw(SPI_WRITE, IoffsetC, 0x0000)    # C line current offset

        self._spi_rw(SPI_WRITE, CfgRegAccEn, 0x0000)  # end configuration
        # In order to get correct results, I needed to insert a 'significant' delay.
        time.sleep(1)
    #####################################################################################
    @property
    def lastSpiData(self):
        reading = self._spi_rw(SPI_READ, LastSPIData, 0xFFFF)
        return reading
    #####################################################################################
    @property
    def sys_status0(self):
        reading = self._spi_rw(SPI_READ, EMMIntState0, 0xFFFF)
        return reading
    #####################################################################################
    @property
    def sys_status1(self):
        reading = self._spi_rw(SPI_READ, EMMIntState1, 0xFFFF)
        return reading
     #####################################################################################

    @property
    def meter_status0(self):
        reading = self._spi_rw(SPI_READ, EMMState0, 0xFFFF)
        return reading

    #####################################################################################
    @property
    def en_status0(self):
        reading = self._spi_rw(SPI_READ, ENStatus0, 0xFFFF)
        return reading
    #####################################################################################
    @property
    def meter_status1(self):
        reading = self._spi_rw(SPI_READ, EMMState1, 0xFFFF)
        return reading
    #####################################################################################
    @property
    def line_voltageA(self):
        reading = self._spi_rw(SPI_READ, UrmsA, 0xFFFF)
        return reading / 100.0
    #####################################################################################
    @property
    def line_voltageB(self):
        reading = self._spi_rw(SPI_READ, UrmsB, 0xFFFF)
        return reading / 100.0
    #####################################################################################
    @property
    def line_voltageC(self):
        reading = self._spi_rw(SPI_READ, UrmsC, 0xFFFF)
        return reading / 100.0
    #####################################################################################
    @property
    def line_currentA(self):
        reading = self._spi_rw(SPI_READ, IrmsA, 0xFFFF)
        return reading / 1000.0
    #####################################################################################
    @property
    def line_currentC(self):
        reading = self._spi_rw(SPI_READ, IrmsC, 0xFFFF)
        return reading / 1000.0
    #####################################################################################
    @property
    def frequency(self):
        reading = self._spi_rw(SPI_READ, Freq, 0xFFFF)
        return reading / 100.0
    #####################################################################################
    @property
    def total_active_power(self):
        reading = self._read32Register(PmeanT, PmeanTLSB)
        return reading * 0.00032
    #####################################################################################

    @property
    def active_power_A(self):
        reading = self._read32Register(PmeanA, PmeanALSB)
        return reading * 0.00032
        #####################################################################################

    @property
    def active_power_C(self):
        reading = self._read32Register(PmeanC, PmeanCLSB)
        return reading * 0.00032
        #####################################################################################

    @property
    def total_reactive_power(self):
        reading = self._read32Register(QmeanT, PmeanTLSB)
        return reading * 0.00032
    #####################################################################################

    @property
    def reactive_power_A(self):
        reading = self._read32Register(QmeanA, PmeanALSB)
        return reading * 0.00032
        #####################################################################################

    @property
    def reactive_power_C(self):
        reading = self._read32Register(QmeanC, PmeanCLSB)
        return reading * 0.00032
    ######################################################
    # Support reading a register
    ######################################################

    def read(self, address):
        reading = self._spi_rw(SPI_READ, address, 0xFFFF)
        return reading

    ######################################################
    # Support writing to a register
    ######################################################
    def write(self, address, val):
        print('in write')
        return self._spi_rw(SPI_WRITE, address, val)
    #####################################################################################
    # do the SPI read or write request.
    #####################################################################################
    def _spi_rw(self, rw, address, val):

        address |= rw << 15

        if(rw):  # read
            return self._readSPI(address)

        else:
            for i in range(3):  # for robustness try a few times.
                bWriteSuccess = self._writeSPI(address, val)
                if (bWriteSuccess or address == SoftReset):
                    # time.sleep_us(3000)
                    # start = time.ticks_us()
                    # print(
                    #     'reading = value. Write successful.  It took {} tries.'.format(i))
                    # print('us ticks: {}'.format(
                    #     time.ticks_diff(time.ticks_us(), start)))
                    return True
            # Write to register didn't work.
            self.num_write_failed += 1
            # print(
            #     'Calibration write to address {:#04x} not successful.'.format(address))
            return False
    ###################################################################################

    def _readSPI(self, address):
        self.cs.off()
        time.sleep_us(4)
        # pack the address into a the bytearray.  It is an unsigned short(H) that needs to be in MSB(>)
        two_byte_buf = bytearray(2)
        results_buf = bytearray(2)
        struct.pack_into('>H', two_byte_buf, 0, address)
        self.device.write(two_byte_buf)
        time.sleep_us(4)
        self.device.readinto(results_buf)
        result = struct.unpack('>H', results_buf)[0]
        self.cs.on()
        return result
    ##################################################################################

    def _writeSPI(self, address, val):
        self.cs.off()
        time.sleep_us(4)
        four_byte_buf = bytearray(4)
        # pack the address into a the bytearray.  It is an unsigned short(H) that needs to be in MSB(>)

        struct.pack_into('>H', four_byte_buf, 0, address)
        struct.pack_into('>H', four_byte_buf, 2, val)

        self.device.write(four_byte_buf)
        self.cs.on()
        time.sleep_us(4)
        reading = self._spi_rw(SPI_READ, LastSPIData, 0xFFFF)
        if (reading == val):
            return True

        return False

    ##################################################################################
    def _round_number(self, f_num):
        if f_num - math.floor(f_num) < 0.5:
            return math.floor(f_num)
        return math.ceil(f_num)

    ###################################################################################
    def _read32Register(self, regh_addr, regl_addr):
        val_h = self._spi_rw(SPI_READ, regh_addr, 0xFFFF)
        val_l = self._spi_rw(SPI_READ, regl_addr, 0xFFFF)
        val = val_h << 16
        val |= val_l  # concatenate the 2 registers to make 1 32 bit number
        if ((val & 0x80000000) != 0):  # if val is negative,
            val = (0xFFFFFFFF - val) + 1  # 2s compliment + 1
        return (val)
