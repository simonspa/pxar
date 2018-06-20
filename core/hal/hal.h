#ifndef PXAR_HAL_H
#define PXAR_HAL_H

#include "rpc_calls.h"
#include "api.h"
#include "datapipe.h"
#include "datasource_dtb.h"
#include "constants.h"
#include "timer.h"

namespace pxar {

  class hal
  {

  public:
    /** Default constructor for creating a new HAL instance. Takes
     *  a testboard USB ID name as parameter and tries to connect to
     *  the board. Exception is thrown if connection fails.
     */
    hal(std::string name = "*");

    /** Default destructor for HAL objects. Testboard USB connection is
     *  closed and RPC object destroyed.
     */
    ~hal();


    /** Function to check the status of the HAL
     */
    bool status();

    /** Function to check the compatibility of the HAL with the DTB
     */
    bool compatible() { return _compatible; }


    // DEVICE INITIALIZATION

    /** Initialize the testboard with the signal delay settings:
     */
    void initTestboard(std::map<uint8_t,uint8_t> sig_delays, std::vector<std::pair<uint16_t, uint8_t> > pg_setup, uint16_t delaysum,  double va, double vd, double ia, double id);

    /** Set/change the testboard voltages and current limits:
     */
    void setTestboardPower(double va, double vd, double ia, double id);

    /** Set/change the testboard signal delay settings:
     */
    void setTestboardDelays(std::map<uint8_t,uint8_t> sig_delays);

    /** Flashes the given firmware file to the testboard FPGA
     *  Powers down the DUT first.
     */
    bool flashTestboard(std::ifstream& flashFile);

    /** Initialize attached TBMs with their settings and configuration
     */
    void initTBMCore(tbmCoreConfig tbm);

    /** Change the type of the TBM type member in HAL
     */
    void setTBMType(uint8_t type);

    /** Initialize attached ROCs with their settings and configuration
     *  This is the startup-routine for single ROCs. It first powers up the
     *  testboard output if necessary, sets the ROC's I2C address and then
     *  programs all DAC registers for the given ROC.
     */
    void initROC(uint8_t roci2c, uint8_t type, std::map< uint8_t,uint8_t > dacVector);

    /** turn off HV
     */
    void HVoff();

    /** turn on HV
     */
    void HVon();

    /** turn on power
     */
    void Pon();

    /** turn off power
     */
    void Poff();

    /** select signal mode
     */
    void SigSetMode(uint8_t signal, uint8_t mode);

    /** set signal to random output PRBS
     */
    void SigSetPRBS(uint8_t signal, uint8_t speed);

    /** select termination for RDA/TOUT to LCDS (for modules)
     */
    void SigSetLCDS();

    /** select termination for RDA/TOUT to LVDS (for single ROCs)
     */
    void SigSetLVDS();

    /** Set HubID
     */
    void setHubId(uint8_t hubid);

    /** Set dual HubID for Layer 1 modules:
     */
    void setHubId(uint8_t hub0, uint8_t hub1);
    
    /** Set a DAC on a specific ROC with I2C address roci2c
     */
    bool rocSetDAC(uint8_t roci2c, uint8_t dacId, uint8_t dacValue);

    /** Set all DACs on a specific ROC with I2C address roci2c
     *  DACs are provided as map of uint8_t,uint8_t pairs  with DAC Id and DAC value.
     */
    bool rocSetDACs(uint8_t roci2c, std::map< uint8_t, uint8_t > dacPairs);

    /** Select the RDA channel of a layer 1 module for tbm readback
    */
    void tbmSelectRDA(uint8_t rda_id);

    /** Set a register on a specific TBM at hubid
     */
    bool tbmSetReg(uint8_t hubid, uint8_t regId, uint8_t regValue, bool flush = true);

    /** Set all registers on a specific TBM tbmId
     *  registers are provided as map of uint8_t,uint8_t pairs with Reg Id and value.
     */
    bool tbmSetRegs(uint8_t hubid, uint8_t core, std::map< uint8_t, uint8_t > regPairs);

    /** Function to set and update the pattern generator command list on the DTB
     */
    void SetupPatternGenerator(std::vector<std::pair<uint16_t,uint8_t> > pg_setup, uint16_t delaysum);

    /** Set the clock source
     */
    void SetClockSource(uint8_t src);

    /** Check if external clock is present
     */
    bool IsClockPresent();

    /** Set the clock stretch
    */
    void SetClockStretch(uint8_t src, uint16_t delay, uint16_t width);


    // TESTBOARD GET COMMANDS
    /** Read the testboard analog current
     */
    double getTBia();

    /** Read the testboard analog voltage
     */
    double getTBva();

    /** Read the testboard digital current
     */
    double getTBid();

    /** Read the testboard digital voltage
     */
    double getTBvd();


    // Testboard probe channel commands:
    /** Selects "signal" as output for the DTB probe channel D1 (digital)
     */
    void SignalProbeD1(uint8_t signal);

    /** Selects "signal" as output for the DTB probe channel D2 (digital)
     */
    void SignalProbeD2(uint8_t signal);

    /** Selects DESER400 "signal" as output for the DTB probe channel D2 (digital) 
     */
    void SignalProbeDeserD1(uint8_t deser, uint8_t signal);

    /** Selects DESER400 "signal" as output for the DTB probe channel D2 (digital) 
     */
    void SignalProbeDeserD2(uint8_t deser, uint8_t signal);

    /** Selects "signal" as output for the DTB probe channel A1 (analog) 
     */
    void SignalProbeA1(uint8_t signal);

    /** Selects "signal" as output for the DTB probe channel A2 (analog)
     */
    void SignalProbeA2(uint8_t signal);

    /** Selects input for the ADC
     */
    void SignalProbeADC(uint8_t signal, uint8_t gain);

    /** Record data using the DTB ADC. The following parameters are available:
	analog_probe = signal to be sampled
	gain = adc gain  (higher values = higher gain but also slower)
	nSample = max. number of samples to be taken
	source  = start signal
	      0 = none (off)
	      1 = pg_sync
	      2 = i2c
	      3 = token in
	start   = delay after start signal
	stop    = not sure, takes nSample samples when stop is 0
      */
    std::vector<uint16_t> daqADC(uint8_t analog_probe, uint8_t gain, uint16_t nSample, uint8_t source, uint8_t start, uint8_t stop = 0);

    // TEST COMMANDS

    /** Function to return Module maps of calibration pulses
     *  Public flags contain possibility to route the calibrate pulse via the sensor (FLAG_CALS) and
     *  possibility for cross-talk measurement (FLAG_XTALK)
     *
     *  The roci2c vector parameter allows to select ROCs with arbitrary I2C addresses. Usually module
     *  I2C addresses range from 0-15 but for special purposes this might be different.
     */
    std::vector<Event> MultiRocAllPixelsCalibrate(std::vector<uint8_t> roci2cs, bool efficiency, std::vector<int32_t> parameter);

    /** Function to return ROC maps of calibration pulses
     *  Public flags contain possibility to route the calibrate pulse via the sensor (FLAG_CALS) and
     *  possibility for cross-talk measurement (FLAG_XTALK)
     */
    std::vector<Event> SingleRocAllPixelsCalibrate(uint8_t roci2c, bool efficiency, std::vector<int32_t> parameter);

    /** Function to return "Pixel maps" of calibration pulses, i.e. pinging a single pixel on multiple ROCs.
     *  Public flags contain possibility to route the calibrate pulse via the sensor (FLAG_CALS) and
     *  possibility for cross-talk measurement (FLAG_XTALK)
     */
    std::vector<Event> MultiRocOnePixelCalibrate(std::vector<uint8_t> roci2cs, uint8_t column, uint8_t row, bool efficiency, std::vector<int32_t> parameter);

    /** Function to return "Pixel maps" of calibration pulses, i.e. pinging a single pixel on one ROC.
     *  Public flags contain possibility to route the calibrate pulse via the sensor (FLAG_CALS) and
     *  possibility for cross-talk measurement (FLAG_XTALK)
     */
    std::vector<Event> SingleRocOnePixelCalibrate(uint8_t roci2c, uint8_t column, uint8_t row, bool efficiency, std::vector<int32_t> parameter);

    /** Function to return ROC maps of thresholds
     *  Public flags contain possibility to route the calibrate pulse via the sensor (FLAG_CALS), cross-talk
     *  settings (FLAG_XTALK) and the possibility to reverse the scanning (FLAG_RISING).
     *  The parameters additionally contain the DAC register to be scanned for threshold setting.
     */
    std::vector<Event> RocThresholdMap(uint8_t roci2c, bool efficiency, std::vector<int32_t> parameter);

    /** Function to return "Pixel maps" of threshold values, i.e. measuring the threshold for a single pixel.
     *  Public flags contain possibility to route the calibrate pulse via the sensor (FLAG_CALS), cross-talk
     *  settings (FLAG_XTALK) and the possibility to reverse the scanning (FLAG_RISING).
     *  The parameters additionally contain the DAC register to be scanned for threshold setting.
     */
    std::vector<Event> PixelThresholdMap(uint8_t roci2c, uint8_t column, uint8_t row, bool efficiency, std::vector<int32_t> parameter);

    /** Function to scan a given DAC for all pixels on multiple ROCs, selected via their I2C address
     *  Public flags contain possibility to route the calibrate pulse via the sensor (FLAG_CALS) and
     *  possibility for cross-talk measurement (FLAG_XTALK)
     */
    std::vector<Event> MultiRocAllPixelsDacScan(std::vector<uint8_t> roci2cs, bool efficiency, std::vector<int32_t> parameter);

    /** Function to scan a given DAC for all pixels on one ROC
     *  Public flags contain possibility to route the calibrate pulse via the sensor (FLAG_CALS) and
     *  possibility for cross-talk measurement (FLAG_XTALK)
     */
    std::vector<Event> SingleRocAllPixelsDacScan(uint8_t roci2c, bool efficiency, std::vector<int32_t> parameter);

    /** Function to scan a given DAC for a pixel on multiple ROCs, selected via their I2C address
     *  Public flags contain possibility to route the calibrate pulse via the sensor (FLAG_CALS) and
     *  possibility for cross-talk measurement (FLAG_XTALK)
     */
    std::vector<Event> MultiRocOnePixelDacScan(std::vector<uint8_t> roci2cs, uint8_t column, uint8_t row, bool efficiency, std::vector<int32_t> parameter);

    /** Function to scan a given DAC for a pixel on one ROC
     *  Public flags contain possibility to route the calibrate pulse via the sensor (FLAG_CALS) and
     *  possibility for cross-talk measurement (FLAG_XTALK)
     */
    std::vector<Event> SingleRocOnePixelDacScan(uint8_t roci2c, uint8_t column, uint8_t row, bool efficiency, std::vector<int32_t> parameter);


    /** Function to scan two given DAC ranges for all pixels on multiple ROCs, selected via their I2C address
     *  Public flags contain possibility to route the calibrate pulse via the sensor (FLAG_CALS) and
     *  possibility for cross-talk measurement (FLAG_XTALK)
     */
    std::vector<Event> MultiRocAllPixelsDacDacScan(std::vector<uint8_t> roci2cs, bool efficiency, std::vector<int32_t> parameter);

    /** Function to scan two given DAC ranges for all pixels on one ROC
     *  Public flags contain possibility to route the calibrate pulse via the sensor (FLAG_CALS) and
     *  possibility for cross-talk measurement (FLAG_XTALK)
     */
    std::vector<Event> SingleRocAllPixelsDacDacScan(uint8_t roci2c, bool efficiency, std::vector<int32_t> parameter);

    /** Function to scan two given DAC ranges for a pixel on multiple ROCs, selected via their I2C address
     *  Public flags contain possibility to route the calibrate pulse via the sensor (FLAG_CALS) and
     *  possibility for cross-talk measurement (FLAG_XTALK)
     */
    std::vector<Event> MultiRocOnePixelDacDacScan(std::vector<uint8_t> roci2cs, uint8_t column, uint8_t row, bool efficiency, std::vector<int32_t> parameter);

    /** Function to scan two given DAC ranges for a pixel on one ROC
     *  Public flags contain possibility to route the calibrate pulse via the sensor (FLAG_CALS) and
     *  possibility for cross-talk measurement (FLAG_XTALK)
     */
    std::vector<Event> SingleRocOnePixelDacDacScan(uint8_t roci2c, uint8_t column, uint8_t row, bool efficiency, std::vector<int32_t> parameter);


    // DAQ functions:
    /** Starting a new data acquisition session
     */
    void daqStart(uint16_t flags, uint8_t deser160phase, uint32_t buffersize = DTB_SOURCE_BUFFER_SIZE);

    /** Select the trigger source as given in "source":
     */
    void daqTriggerSource(uint16_t source);

    /** Send a single signal via the DTB to the DUT. This function
     *  first configures the trigger source TRG_SEL_SINGLE_DIR
     *  (direct sending of signals, no softTBM), then sends the
     *  signal and finally resets the trigger source to the previous
     *  setting (from hal::_currentTrgSrc)
     */
    void daqTriggerSingleSignal(uint8_t signal);

    void daqTriggerGenRandom(uint32_t rate);
    void daqTriggerGenPeriodic(uint32_t period);
    
    /** Firing the pattern generator nTrig times with the programmed patterns
     */
    void daqTrigger(uint32_t nTrig, uint16_t period);

    /** Firing the pattern generator continuously every "period" clock cycles
     */
    void daqTriggerLoop(uint16_t period);

    /** Halt the pattern generator loop - no more triggers
     */
    void daqTriggerLoopHalt();

    /** Activating the external trigger input of the pattern generator
     */
    void daqTriggerPgExtern();

    /** Stopping the current DAQ session. This is not resetting the data buffers.
     *  All DAQ channels are stopped.
     */
    void daqStop();

    /**
     */
    uint32_t daqBufferStatus();

    /** Reading just the DTB buffer and returning
     */
    std::vector<uint16_t> daqBuffer();

    /** Reading out the full undecoded DAQ buffer
     */
    std::vector<rawEvent> daqAllRawEvents();

    /** Read the next decoded Event from the FIFO buffer
     */
    Event daqEvent();

    /** Read the next raw (undecoded) Event from the FIFO buffer
     */
    rawEvent daqRawEvent();

    /** Return an Event and an rawEvent from the same data
     */
    void daqCombinedEvent(Event &event, rawEvent &rawevent);
    void daqBothEvents(Event &event, rawEvent &rawevent);

    /** Read all remaining decoded Events from the FIFO buffer
     */
    std::vector<Event> daqAllEvents();

    /** Return the current decoding statistics for all channels:
     */
    statistics daqStatistics();

    /** Return all readback values for the last readout. Return format is a vector containing
     *  one vector of uint16_t radback values for every ROC in the readout chain.
     */
    std::vector<std::vector<uint16_t> > daqReadback();

    /** Return all XOR sum values for the selected channel. Return format is a vector containing
     *  all samples XOR sums for the respective DESER400 channel.
     */
    std::vector<uint8_t> daqXORsum(uint8_t channel);

    /** Clears the DAQ buffer on the DTB, deletes all previously taken and not yet read out data!
     */
    void daqClear();


    // Functions to access NIOS storage of trim values:

    /** Set the available I2C device addresses
     */
    void SetupI2CValues(std::vector<uint8_t> roci2cs);

    /** Set all trim bits for the ROC with specified I2C address
     */
    void SetupTrimValues(uint8_t roci2c, std::vector<pixelConfig> pixels);


    // Functions to set bits somewhere on the ROC:

    /** Mask all pixels on a specific ROC I2C address
     */
    void RocSetMask(uint8_t roci2c, bool mask, std::vector<pixelConfig> pixels = std::vector<pixelConfig>());

    /** Set the Calibrate bit and CALS setting of a pixel
     */
    void PixelSetCalibrate(uint8_t roci2c, uint8_t column, uint8_t row, uint16_t flags);

    /** Set the Calibrate bit and CALS setting of a full ROC, read from avector of pxar::pixelConfig
     */
    void RocSetCalibrate(uint8_t roci2c, std::vector<pixelConfig> pixels, uint16_t flags);

    /** Reset all Calibrate bits and clear the ROC I2C address:
     */
    void RocClearCalibrate(uint8_t roci2c);

    /** Set the Column Enable bit for all columns
     */
    void AllColumnsSetEnable(uint8_t roci2c, bool enable);

    /** Get ADC value
     */
    uint16_t GetADC(uint8_t rpc_par1);

    void setOffset(uint8_t offsetDec) { m_decoder[0].setOffset(offsetDec); }

  private:

    /** Private instance of the testboard RPC interface, routes all
     *  hardware access:
     */
    CTestboard * _testboard;

    /** Initialization status of the HAL instance, marks the "ready for
     *  operations" status
     */
    bool _initialized;

    /** Compatibility status of the HAL RPC calls with the DTB. If not set the
     *  DTB cannot be initialized, only flashing is allowed then.
     */
    bool _compatible;

    // FIXME can't we find a smarter solution to this?!
    uint8_t m_tbmtype;
    uint16_t m_adctimeout;
    uint8_t m_tindelay;
    uint8_t m_toutdelay;
    uint8_t deser160phase;
    uint8_t m_roctype;
    uint8_t m_roccount;
    std::vector<uint8_t> m_tokenchains;
    // Store which channels are active:
    std::vector<bool> m_daqstatus;

    uint16_t _currentTrgSrc;

    /** Print the info block with software and firmware versions,
     *  MAC and USB ids etc. read from the connected testboard
     */
    void PrintInfo();

    /** Check for matching pxar / DTB firmware RPC call hashes
     * and scan the RPC commands one by one if ion doubt.
     */
    bool CheckCompatibility();

    /** Find attached USB devices that match the DTB naming scheme.
     *
     *  If usbId = "*" check for all attached devices and list them,
     *  if a specific USB ID is given check that device and return.
     */
    bool FindDTB(std::string &usbId);

    /** Internal helper function to calculate an estimate of the data volume to be
     *  expected for the upcoming test. This function only supplies debug output
     *  and has no further effect on the data transmission or similar.
     */
    void estimateDataVolume(uint32_t events, uint8_t nROCs);

    /** Merges all consecutive triggers into one pxar::Event. This function deletes the original event data after
     *  merging! 
     */
    std::vector<Event> condenseTriggers(std::vector<Event> &data, uint16_t nTriggers, bool efficiency);

    /** Helper function reading data, passing it to the condenser and then returns it to the test function
     */
    void addCondensedData(std::vector<Event> &data, uint16_t nTriggers, bool efficiency, timer t);

    // TESTBOARD SET COMMANDS
    /** Set the testboard analog current limit
     */
    void setTBia(double IA);

    /** Set the testboard analog voltage
     */
    void setTBva(double VA);

    /** Set the testboard digital current limit
     */
    void setTBid(double ID);

    /** Set the testboard digital voltage
     */
    void setTBvd(double VD);

    /** Hash calculation for RPC string vector
     */
    uint32_t GetHashForStringVector(const std::vector<std::string> & v);

    /** Simple hashing for one string
     */
    uint32_t GetHashForString(const char* s);

    /** Read all data from one TBM channel data stream
     */
    std::vector<uint16_t> * daqReadChannel(uint8_t channel);

    // Our default pipe work buffers:
    std::vector<dtbSource> m_src;
    std::vector<dtbEventSplitter> m_splitter;
    std::vector<dtbEventDecoder> m_decoder;
  };
}
#endif
