# distutils: language = c++
from libc.stdint cimport uint8_t, int8_t, uint16_t, int16_t, int32_t, uint32_t
from libcpp.vector cimport vector
from libcpp.map cimport map
from libcpp.pair cimport pair
from libcpp.string cimport string
from libcpp cimport bool

cdef extern from "api.h" namespace "pxar":
    cdef int _flag_force_serial   "FLAG_FORCE_SERIAL"
    cdef int _flag_cals           "FLAG_CALS"
    cdef int _flag_xtalk          "FLAG_XTALK"
    cdef int _flag_rising_edge    "FLAG_RISING_EDGE"
    cdef int _flag_disable_daccal "FLAG_DISABLE_DACCAL"
    cdef int _flag_nosort         "FLAG_NOSORT"
    cdef int _flag_check_order    "FLAG_CHECK_ORDER"
    cdef int _flag_force_unmasked "FLAG_FORCE_UNMASKED"
    cdef int _flag_dump_flawed_events "FLAG_DUMP_FLAWED_EVENTS"
    cdef int _flag_disable_readback_collection "FLAG_DISABLE_READBACK_COLLECTION"
    cdef int _flag_disable_eventid_check "FLAG_DISABLE_EVENTID_CHECK"
    cdef int _flag_enable_xorsum_logging "FLAG_ENABLE_XORSUM_LOGGING"

cdef extern from "api.h" namespace "pxar":
    cdef cppclass pixel:
        uint8_t roc()
        uint8_t column()
        uint8_t row()
        uint8_t bufferCorruption()
        uint8_t invalidAddress()
        uint8_t invalidPulseHeight()
        pixel()
        pixel(int32_t address, int32_t data)
        double value()
        void setValue(double val)
        void setRoc(uint8_t roc)
        void setColumn(uint8_t column)
        void setRow(uint8_t row)
        void setBufferCorruption(bool bufcor)
        void setInvalidAddress(bool invaladd)
        void setInvalidPulseHeight(bool invalph)

cdef extern from "api.h" namespace "pxar":
    cdef cppclass Event:
        vector[uint16_t] getHeaders()
        vector[uint16_t] getTrailers()
        void printHeader()
        void printTrailer()
        void addHeader(uint16_t data)
        void addTrailer(uint16_t data)
        vector[pixel] pixels
        vector[bool] haveNoTokenPass()
        vector[bool] haveTokenPass()
        vector[bool] haveResetTBM()
        vector[bool] haveResetROC()
        vector[bool] haveSyncError()
        vector[bool] haveSyncTrigger()
        vector[bool] haveClearTriggerCount()
        vector[bool] haveCalTrigger()
        vector[bool] stacksFull()
        vector[bool] haveAutoReset()
        vector[bool] havePkamReset()
        vector[uint8_t] stackCounts()
        vector[uint8_t] triggerCounts()
        vector[uint8_t] triggerPhases()
        vector[uint8_t] dataIDs()
        vector[uint8_t] dataValues()
        vector[bool] incomplete_data
        vector[bool] missing_roc_headers
        vector[bool] roc_readback
        vector[bool] no_data
        vector[bool] eventid_mismatch
        Event()
        Event(Event &) except +

cdef extern from "api.h" namespace "pxar":
    cdef cppclass pixelConfig:
        uint8_t roc()
        uint8_t trim()
        uint8_t column()
        uint8_t row()
        bool mask()
        bool enable()
        void setColumn(uint8_t column)
        void setRoc(uint8_t roc)
        void setRow(uint8_t row)
        void setMask(bool mask)
        void setEnable(bool enable)
        void setTrim(uint8_t trim)
        pixelConfig()
        pixelConfig(uint8_t column, uint8_t row, uint8_t trim)

cdef extern from "api.h" namespace "pxar":
    cdef cppclass rocConfig:
        vector[pixelConfig] pixels
        map[uint8_t, uint8_t] dacs
        uint8_t type
        bool enable()
        void setEnable(bool enable)
        rocConfig()

cdef extern from "api.h" namespace "pxar":
    cdef cppclass tbmConfig:
        map[uint8_t, uint8_t] dacs
        uint8_t type
        bool enable
        tbmConfig()

cdef extern from "api.h" namespace "pxar":
    cdef cppclass statistics:
        void clear()
        void dump()
        statistics()
        uint32_t errors()
        uint32_t info_words_read()
        uint32_t errors_event()
        uint32_t errors_tbm()
        uint32_t errors_roc()
        uint32_t errors_pixel()
        uint32_t info_pixels_valid()
        uint32_t info_events_valid()
        uint32_t info_events_total()
        uint32_t info_events_empty()
        uint32_t errors_event_start()
        uint32_t errors_event_stop()
        uint32_t errors_event_overflow()
        uint32_t errors_event_invalid_words()
        uint32_t errors_event_invalid_xor()
        uint32_t errors_event_frame()
        uint32_t errors_event_idledata()
        uint32_t errors_event_nodata()
        uint32_t errors_event_pkam()
        uint32_t errors_tbm_header()
        uint32_t errors_tbm_eventid_mismatch()
        uint32_t errors_tbm_trailer()
        uint32_t errors_roc_missing()
        uint32_t errors_roc_readback()
        uint32_t errors_pixel_incomplete()
        uint32_t errors_pixel_address()
        uint32_t errors_pixel_pulseheight()
        uint32_t errors_pixel_buffer_corrupt()


cdef extern from "api.h" namespace "pxar":
    cdef cppclass dut:
        dut()
        void info()
        int32_t getNEnabledPixels(uint8_t rocid)
        int32_t getNEnabledPixels()
        int32_t getNMaskedPixels(uint8_t rocid)
        int32_t getNMaskedPixels()
        int32_t getNEnabledTbms()
        int32_t getNTbmCores()
        string getTbmType()
        int32_t getNEnabledRocs()
        int32_t getNRocs()
        string getRocType()
        vector[pixelConfig] getEnabledPixels(size_t rocid)
        vector[pixelConfig] getEnabledPixels()
        vector[pixelConfig] getMaskedPixels(size_t rocid)
        vector[pixelConfig] getMaskedPixels()
        vector[rocConfig] getEnabledRocs()
        vector[uint8_t] getEnabledRocI2Caddr()
        vector[uint8_t] getEnabledRocIDs()
        vector[tbmConfig] getEnabledTbms()
        bool getPixelEnabled(uint8_t column, uint8_t row)
        bool getAllPixelEnable()
        bool getModuleEnable()
        pixelConfig getPixelConfig(size_t rocid, uint8_t column, uint8_t row)
        uint8_t getDAC(size_t rocId, string dacName)
        vector[pair[string,uint8_t]] getDACs(size_t rocId)
        vector[pair[string,uint8_t]] getTbmDACs(size_t tbmId)
        void printDACs(size_t rocId)
        void setROCEnable(size_t rocId, bool enable)
        void setTBMEnable(size_t tbmId, bool enable)
        void testPixel(uint8_t column, uint8_t row, bool enable)
        void testPixel(uint8_t column, uint8_t row, bool enable, uint8_t rocid)
        void maskPixel(uint8_t column, uint8_t row, bool mask)
        void maskPixel(uint8_t column, uint8_t row, bool mask, uint8_t rocid)
        void testAllPixels(bool enable)
        void testAllPixels(bool enable, uint8_t rocid)
        void maskAllPixels(bool mask, uint8_t rocid)
        void maskAllPixels(bool mask)
        bool updateTrimBits(vector[pixelConfig] trimming, uint8_t rocid)
        bool updateTrimBits(uint8_t column, uint8_t row, uint8_t trim, uint8_t rocid)
        bool updateTrimBits(pixelConfig trim, uint8_t rocid)
        bool status()
        bool _initialized
        bool _programmed
        vector[bool] getEnabledColumns(size_t rocid)
        vector[rocConfig] roc
        vector[tbmConfig] tbm
        map[uint8_t,uint8_t] sig_delays
        double va, vd, ia, id
        vector[pair[uint16_t,uint8_t]] pg_setup

cdef extern from "api.h" namespace "pxar":
    cdef cppclass Event:
        Event()
        void Clear()
        uint16_t header
        uint16_t trailer
        vector[pixel] pixels

cdef extern from "api.h" namespace "pxar":
    cdef cppclass rawEvent:
        rawEvent()
        void SetStartError()
        void SetEndError()
        void SetOverflow()
        void ResetStartError()
        void ResetEndError()
        void ResetOverflow()
        void Clear()
        bool IsStartError()
        bool IsEndError()
        bool IsOverflow()
        unsigned int GetSize()
        void Add(uint16_t value)
        vector[uint16_t] data


cdef extern from "api.h" namespace "pxar":
    cdef cppclass pxarCore:
        pxarCore(string usbId, string logLevel) except +
        dut* _dut
        string getVersion()
        bool initTestboard(vector[pair[string, uint8_t] ] sig_delays, 
                           vector[pair[string, double] ] power_settings, 
                           vector[pair[string, uint8_t]] pg_setup) except +
        void setTestboardPower(vector[pair[string, double] ] power_settings) except +
        vector[pair[string,uint8_t]] getTestboardDelays()
        void setTestboardDelays(vector[pair[string, uint8_t] ] sig_delays) except +
        void setPatternGenerator(vector[pair[string, uint8_t] ] pg_setup) except +
        void setDecodingOffset(uint8_t offset)

        bool initDUT(vector[uint8_t] hubId,
	             string tbmtype,
                     vector[vector[pair[string,uint8_t]]] tbmDACs,
                     string roctype,
                     vector[vector[pair[string,uint8_t]]] rocDACs,
                     vector[vector[pixelConfig]] rocPixels) except +

        bool initDUT(vector[uint8_t] hubId,
	             string tbmtype,
                     vector[vector[pair[string,uint8_t]]] tbmDACs,
                     string roctype,
                     vector[vector[pair[string,uint8_t]]] rocDACs,
                     vector[vector[pixelConfig]] rocPixels,
                     vector[uint8_t] rocI2C) except +

        bool programDUT() except +
        bool status()
        bool flashTB(string filename) except +
        double getTBia()
        double getTBva()
        double getTBid()
        double getTBvd()
        void HVoff()
        void HVon()
        void Poff()
        void Pon()
        bool SignalProbe(string probe, string name, uint8_t channel) except +
        bool setDAC(string dacName, uint8_t dacValue, uint8_t rocid) except +
        bool setDAC(string dacName, uint8_t dacValue) except +
        uint8_t getDACRange(string dacName) except +
        bool setTbmReg(string regName, uint8_t regValue, uint8_t tbmid) except +
        bool setTbmReg(string regName, uint8_t regValue) except +
        vector[pair[uint8_t, vector[pixel]]] getPulseheightVsDAC(string dacName, uint8_t dacStep, uint8_t dacMin, uint8_t dacMax, uint16_t flags, uint16_t nTriggers)  except +
        vector[pair[uint8_t, vector[pixel]]] getEfficiencyVsDAC(string dacName, uint8_t dacStep, uint8_t dacMin, uint8_t dacMax, uint16_t flags, uint16_t nTriggers) except +
        vector[pair[uint8_t, vector[pixel]]] getThresholdVsDAC(string dac1Name, uint8_t dac1Step, uint8_t dac1Min, uint8_t dac1Max, string dac2Name, uint8_t dac2Step, uint8_t dac2Min, uint8_t dac2Max, uint8_t threshold, uint16_t flags, uint16_t nTriggers) except +
        vector[pair[uint8_t, pair[uint8_t, vector[pixel]]]] getPulseheightVsDACDAC(string dac1name, uint8_t dac1Step, uint8_t dac1min, uint8_t dac1max, string dac2name, uint8_t dac2Step, uint8_t dac2min, uint8_t dac2max, uint16_t flags, uint16_t nTriggers) except +
        vector[pair[uint8_t, pair[uint8_t, vector[pixel]]]] getEfficiencyVsDACDAC(string dac1name, uint8_t dac1Step, uint8_t dac1min, uint8_t dac1max, string dac2name, uint8_t dac2Step, uint8_t dac2min, uint8_t dac2max, uint16_t flags, uint16_t nTriggers) except +
        vector[pixel] getPulseheightMap(uint16_t flags, uint16_t nTriggers) except +
        vector[pixel] getEfficiencyMap(uint16_t flags, uint16_t nTriggers) except +
        vector[pixel] getThresholdMap(string dacName, uint8_t dacStep, uint8_t dacMin, uint8_t dacMax, uint8_t threshold, uint16_t flags, uint16_t nTriggers) except +
        int32_t getReadbackValue(string parameterName) except +
        bool setExternalClock(bool enable) except +
        void setClockStretch(uint8_t src, uint16_t delay, uint16_t width) except +
        void setSignalMode(string signal, uint8_t mode, uint8_t speed) except +
        void setSignalMode(string signal, string mode, uint8_t speed) except +
        bool daqStart(uint16_t flags) except +
        bool daqStatus() except +
        bool daqTriggerSource(string triggerSource, uint32_t period) except +
        bool daqSingleSignal(string triggerSignal) except +
        void daqTrigger(uint32_t nTrig, uint16_t period) except +
        void daqTriggerLoop(uint16_t period) except +
        void daqTriggerLoopHalt() except +
        Event daqGetEvent() except +
        rawEvent daqGetRawEvent() except +
        vector[rawEvent] daqGetRawEventBuffer() except +
        vector[Event] daqGetEventBuffer() except +
        vector[uint16_t] daqGetBuffer() except +
        vector[vector[uint16_t]] daqGetReadback() except +
        vector[uint8_t] daqGetXORsum(uint8_t channel) except +
        statistics getStatistics() except +
        void setReportingLevel(string logLevel) except +
        string getReportingLevel() except +
        bool daqStop() except +
