/**
 * pxar dictionary header
 * This file contains all dictionaries for parameter name lookup:
 *
 * DAC registers, their range and names
 * TBM parameters
 * DTB parameters
 */

#ifndef PXAR_DICTIONARIES_H
#define PXAR_DICTIONARIES_H

/** Cannot use stdint.h when running rootcint on WIN32 */
#if ((defined WIN32) && (defined __CINT__))
typedef unsigned char uint8_t;
#else
#include <stdint.h>
#endif

#include <string>
#include <map>
#include "constants.h"
#include <iostream>

#define DTB_REG 0xFF
#define TBM_REG 0x0F
#define ROC_REG 0x00
#define TRG_ERR 0xF000

#define PROBE_ANALOG  PROBEA_OFF
#define PROBE_DIGITAL PROBE_OFF
#define PROBE_NONE    0xFF

#define PATTERN_NONE 0x00
#define PATTERN_PG   0x01
#define PATTERN_TRG  0x02
#define PATTERN_ERR  0xFF00

namespace pxar {

  /** class to store a DAC config
   *  contains register id and valid range of the DAC
   */
  class dacConfig {
  public:
    dacConfig() {}
  dacConfig(uint8_t id, uint8_t size) : _type(0), _id(id), _size(size), _preferred(true) {}
  dacConfig(uint8_t id, uint8_t size, uint8_t type) : _type(type), _id(id), _size(size), _preferred(true) {}
  dacConfig(uint8_t id, uint8_t size, uint8_t type, bool preferred) : _type(type), _id(id), _size(size), _preferred(preferred) {}
    uint8_t _type;
    uint8_t _id;
    uint8_t _size;
    bool _preferred;
  };


  /** Map for generic register name lookup
   *  All register names are lower case, register selection is case-insensitive.
   *  Singleton class, only one object of this floating around.
   */
  class RegisterDictionary {
  public:
    static RegisterDictionary * getInstance() {
      static RegisterDictionary instance; // Guaranteed to be destroyed.
      // Instantiated on first use.
      return &instance;
    }

    // Return the register id for the name in question:
    inline uint8_t getRegister(std::string name, uint8_t type) {
      if(_registers.find(name)->second._type == type) {
	return _registers.find(name)->second._id;
      }
      else { return type;}
    }

    // Return the register size for the register in question:
    inline uint8_t getSize(std::string name, uint8_t type) {
	if(_registers.find(name)->second._type == type) {
	  return _registers.find(name)->second._size;
	}
	else { return type;}
    }

    // Return the register size for the register in question:
    inline uint8_t getSize(uint8_t id, uint8_t type) {
      for(std::map<std::string, dacConfig>::iterator iter = _registers.begin(); iter != _registers.end(); ++iter) {
	if((*iter).second._type == type && (*iter).second._id == id) {
	  return (*iter).second._size;
	}
      }
      return type;
    }

    // Return the register name for the register in question:
    inline std::string getName(uint8_t id, uint8_t type) {
      for(std::map<std::string, dacConfig>::iterator iter = _registers.begin(); iter != _registers.end(); ++iter) {
	if((*iter).second._type == type && (*iter).second._id == id && (*iter).second._preferred == true) {
	  return (*iter).first;}
      }
      return "";
    }

    // Return all (preferred) register names for the type in question:
    inline std::vector<std::string> getAllNames(uint8_t type) {
      std::vector<std::string> names;
      for(std::map<std::string, dacConfig>::iterator iter = _registers.begin(); iter != _registers.end(); ++iter) {
	if((*iter).second._type == type && (*iter).second._preferred == true) {
	  names.push_back((*iter).first);
	}
      }
      return names;
    }

    // Return all (preferred) register names for a single type:
    inline std::vector<std::string> getAllROCNames() {return getAllNames(ROC_REG);}
    inline std::vector<std::string> getAllDTBNames() {return getAllNames(DTB_REG);}
    inline std::vector<std::string> getAllTBMNames() {return getAllNames(TBM_REG);}

  private:
    RegisterDictionary() {
      //------- DTB registers -----------------------------
      _registers["clk"]            = dacConfig(SIG_CLK,255,DTB_REG);
      _registers["ctr"]            = dacConfig(SIG_CTR,255,DTB_REG);
      _registers["sda"]            = dacConfig(SIG_SDA,255,DTB_REG);
      _registers["tin"]            = dacConfig(SIG_TIN,255,DTB_REG);
      _registers["level"]          = dacConfig(SIG_LEVEL,15,DTB_REG);
      _registers["triggerdelay"]   = dacConfig(SIG_LOOP_TRIGGER_DELAY,255,DTB_REG);
      _registers["trimdelay"]      = dacConfig(SIG_LOOP_TRIM_DELAY,255,DTB_REG);
      _registers["deser160phase"]  = dacConfig(SIG_DESER160PHASE,7,DTB_REG);

      _registers["deser400rate"]   = dacConfig(SIG_DESER400RATE,3,DTB_REG);
      _registers["deser400phase0"] = dacConfig(SIG_DESER400PHASE0,15,DTB_REG);
      _registers["deser400phase1"] = dacConfig(SIG_DESER400PHASE1,15,DTB_REG);
      _registers["deser400phase2"] = dacConfig(SIG_DESER400PHASE2,15,DTB_REG);
      _registers["deser400phase3"] = dacConfig(SIG_DESER400PHASE3,15,DTB_REG);

      _registers["triggerlatency"] = dacConfig(SIG_TRIGGER_LATENCY,255,DTB_REG);
      _registers["triggertimeout"] = dacConfig(SIG_TRIGGER_TIMEOUT,255,DTB_REG);

      _registers["tindelay"]       = dacConfig(SIG_ADC_TINDELAY,63,DTB_REG);
      _registers["toutdelay"]      = dacConfig(SIG_ADC_TOUTDELAY,63,DTB_REG);
      _registers["adctimeout"]     = dacConfig(SIG_ADC_TIMEOUT,255,DTB_REG);

      _registers["tout"]          = dacConfig(SIG_RDA_TOUT,19,DTB_REG);
      _registers["rda"]           = dacConfig(SIG_RDA_TOUT,19,DTB_REG);


      //------- TBM registers -----------------------------
      _registers["counters"]      = dacConfig(TBM_REG_COUNTER_SWITCHES,255,TBM_REG,false);
      _registers["base0"]         = dacConfig(TBM_REG_COUNTER_SWITCHES,255,TBM_REG);

      _registers["mode"]          = dacConfig(TBM_REG_SET_MODE,255,TBM_REG,false);
      _registers["base2"]         = dacConfig(TBM_REG_SET_MODE,255,TBM_REG);

      _registers["clear"]         = dacConfig(TBM_REG_CLEAR_INJECT,255,TBM_REG,false);
      _registers["inject"]        = dacConfig(TBM_REG_CLEAR_INJECT,255,TBM_REG,false);
      _registers["base4"]         = dacConfig(TBM_REG_CLEAR_INJECT,255,TBM_REG);

      _registers["pkam_set"]      = dacConfig(TBM_REG_SET_PKAM_COUNTER,255,TBM_REG,false);
      _registers["base8"]         = dacConfig(TBM_REG_SET_PKAM_COUNTER,255,TBM_REG);

      _registers["delays"]        = dacConfig(TBM_REG_SET_DELAYS,255,TBM_REG,false);
      _registers["basea"]         = dacConfig(TBM_REG_SET_DELAYS,255,TBM_REG);

      _registers["autoreset"]     = dacConfig(TBM_REG_AUTORESET,255,TBM_REG,false);
      _registers["basec"]         = dacConfig(TBM_REG_AUTORESET,255,TBM_REG);
      // Outdated name, since temperature register has moved to 0x0E
      // name kept for legacy reasons so old configuration files still work:
      _registers["temperature"]   = dacConfig(TBM_REG_AUTORESET,255,TBM_REG,false);
      
      _registers["cores"]         = dacConfig(TBM_REG_CORES_A_B,255,TBM_REG,false);
      _registers["basee"]         = dacConfig(TBM_REG_CORES_A_B,255,TBM_REG);

      // Special TBM settings:
      _registers["nrocs"]         = dacConfig(TBM_TOKENCHAIN_0,8,TBM_REG);
      _registers["nrocs1"]        = dacConfig(TBM_TOKENCHAIN_0,8,TBM_REG);
      _registers["nrocs2"]        = dacConfig(TBM_TOKENCHAIN_1,8,TBM_REG);

      //------- ROC registers -----------------------------
      // DAC name, register and size reference:
      // http://cms.web.psi.ch/phase1/psi46dig/index.html

      _registers["vdig"]       = dacConfig(ROC_DAC_Vdig,15,ROC_REG);
      _registers["vdd"]        = dacConfig(ROC_DAC_Vdig,15,ROC_REG,false);

      _registers["vana"]       = dacConfig(ROC_DAC_Vana,255,ROC_REG);
      _registers["iana"]       = dacConfig(ROC_DAC_Vana,255,ROC_REG,false);

      _registers["vsf"]        = dacConfig(ROC_DAC_Vsh,255,ROC_REG,false);
      _registers["vsh"]        = dacConfig(ROC_DAC_Vsh,255,ROC_REG);

      _registers["vcomp"]      = dacConfig(ROC_DAC_Vcomp,15,ROC_REG);

      _registers["vwllpr"]     = dacConfig(ROC_DAC_VwllPr,255,ROC_REG);
      _registers["fbpre"]      = dacConfig(ROC_DAC_VwllPr,255,ROC_REG,false);

      _registers["vwllsh"]     = dacConfig(ROC_DAC_VwllSh,255,ROC_REG);
      _registers["fbsh"]       = dacConfig(ROC_DAC_VwllSh,255,ROC_REG,false);

      _registers["vhlddel"]    = dacConfig(ROC_DAC_VhldDel,255,ROC_REG);
      _registers["holddel"]    = dacConfig(ROC_DAC_VhldDel,255,ROC_REG,false);

      _registers["vtrim"]      = dacConfig(ROC_DAC_Vtrim,255,ROC_REG);
      _registers["trimscale"]  = dacConfig(ROC_DAC_Vtrim,255,ROC_REG,false);

      _registers["vthrcomp"]   = dacConfig(ROC_DAC_VthrComp,255,ROC_REG);
      _registers["globalthr"]  = dacConfig(ROC_DAC_VthrComp,255,ROC_REG,false);

      _registers["vibias_bus"] = dacConfig(ROC_DAC_VIBias_Bus,255,ROC_REG);

      _registers["voffsetro"]  = dacConfig(ROC_DAC_VoffsetRO,255,ROC_REG,false);
      _registers["voffsetr0"]  = dacConfig(ROC_DAC_VoffsetRO,255,ROC_REG,false);
      _registers["phoffset"]   = dacConfig(ROC_DAC_VoffsetRO,255,ROC_REG);

      _registers["vcomp_adc"]  = dacConfig(ROC_DAC_VIbias_PH,255,ROC_REG);
      _registers["vibias_ph"]  = dacConfig(ROC_DAC_VIbias_PH,255,ROC_REG,false);
      _registers["adcpower"]   = dacConfig(ROC_DAC_VIbias_PH,255,ROC_REG,false);

      _registers["viref_adc"]  = dacConfig(ROC_DAC_VIbias_DAC,255,ROC_REG,false);
      _registers["vibias_dac"] = dacConfig(ROC_DAC_VIbias_DAC,255,ROC_REG,false);
      _registers["ibias_dac"]  = dacConfig(ROC_DAC_VIbias_DAC,255,ROC_REG,false);
      _registers["phscale"]    = dacConfig(ROC_DAC_VIbias_DAC,255,ROC_REG);

      _registers["vicolor"]    = dacConfig(ROC_DAC_VIColOr,255,ROC_REG);

      _registers["vcal"]       = dacConfig(ROC_DAC_Vcal,255,ROC_REG);

      _registers["caldel"]     = dacConfig(ROC_DAC_CalDel,255,ROC_REG);

      _registers["ctrlreg"]    = dacConfig(ROC_DAC_CtrlReg,255,ROC_REG);
      _registers["ccr"]        = dacConfig(ROC_DAC_CtrlReg,255,ROC_REG,false);

      _registers["wbc"]        = dacConfig(ROC_DAC_WBC,255,ROC_REG);

      _registers["readback"]   = dacConfig(ROC_DAC_Readback,15,ROC_REG);
      _registers["rbreg"]      = dacConfig(ROC_DAC_Readback,15,ROC_REG,false);

      // DACs removed from psi46digV3 (?):
      _registers["vbias_sf"]   = dacConfig(ROC_DAC_Vbias_sf,15,ROC_REG);
      _registers["voffsetop"]  = dacConfig(ROC_DAC_VoffsetOp,255,ROC_REG);
      _registers["vion"]       = dacConfig(ROC_DAC_VIon,255,ROC_REG);

      // DACs removed from psi46digV2:
      _registers["vleak_comp"] = dacConfig(ROC_DAC_Vleak_comp,255,ROC_REG);
      _registers["vleak"] = dacConfig(ROC_DAC_Vleak_comp,255,ROC_REG);

      _registers["vrgpr"]      = dacConfig(ROC_DAC_VrgPr,255,ROC_REG);
      _registers["vrgsh"]      = dacConfig(ROC_DAC_VrgSh,255,ROC_REG);

      _registers["vibiasop"]   = dacConfig(ROC_DAC_VIbiasOp,255,ROC_REG);
      _registers["vbias_op"]   = dacConfig(ROC_DAC_VIbiasOp,255,ROC_REG,false);

      _registers["vibias_roc"] = dacConfig(ROC_DAC_VIbias_roc,255,ROC_REG);

      // DAC only present in the PROC600, same address as old VIBias_Bus:
      _registers["vcolorbias"] = dacConfig(ROC_DAC_VIBias_Bus,255,ROC_REG);

      // DACs only relevant for analog chips:
      _registers["vnpix"]      = dacConfig(ROC_DAC_Vnpix,255,ROC_REG);
      _registers["vsumcol"]    = dacConfig(ROC_DAC_VsumCol,255,ROC_REG);

      _registers["rangetemp"]  = dacConfig(ROC_DAC_RangeTemp,255,ROC_REG);
    }

    std::map<std::string, dacConfig> _registers;
    // Dont forget to declare these two. You want to make sure they
    // are unaccessable otherwise you may accidently get copies of
    // your singleton appearing.
    RegisterDictionary(RegisterDictionary const&); // Don't Implement
    void operator=(RegisterDictionary const&); // Don't implement
  };


  /** Map for device name lookup
   *  All device names are lower case, check is case-insensitive.
   *  Singleton class, only one object of this floating around.
   */
  class DeviceDictionary {
  public:
    static DeviceDictionary * getInstance() {
      static DeviceDictionary instance; // Guaranteed to be destroyed.
      // Instantiated on first use.
      return &instance;
    }

    // Return the register id for the name in question:
    inline uint8_t getDevCode(std::string name) {
      if(_devices.find(name) != _devices.end()) { return _devices[name]; }
      else { return 0x0; }
    }

    // Return the signal name for the probe signal in question:
    inline std::string getName(uint8_t devCode) {
      for(std::map<std::string, uint8_t>::iterator iter = _devices.begin(); iter != _devices.end(); ++iter) {
	if((*iter).second == devCode) { return (*iter).first; }
      }
      return "";
    }
    // returns true if the roc is analog, todo: check if entry exist
    inline bool isAnalogROC(std::string name){
    	return (getDevCode(name) > 0 && getDevCode(name) < ROC_PSI46DIG);
    }

  private:
    DeviceDictionary() {
      // Device name and types

      // ROC flavors:
      _devices["psi46v2"]           = ROC_PSI46V2;
      _devices["psi46xdb"]          = ROC_PSI46XDB;
      _devices["psi46dig"]          = ROC_PSI46DIG;
      _devices["psi46dig_trig"]     = ROC_PSI46DIG_TRIG;
      _devices["psi46digv2_b"]      = ROC_PSI46DIGV2_B;
      _devices["psi46digv2"]        = ROC_PSI46DIGV2;
      _devices["psi46digv2.1"]      = ROC_PSI46DIGV21;
      _devices["psi46digv21"]       = ROC_PSI46DIGV21;
      _devices["psi46digv21respin"] = ROC_PSI46DIGV21RESPIN;
      _devices["proc600"]           = ROC_PROC600;
      _devices["psi46digplus"]      = ROC_PROC600;
      _devices["psi46digl1"]        = ROC_PROC600;
      _devices["proc600v2"]         = ROC_PROC600V2;
      _devices["proc600_v2"]        = ROC_PROC600V2;

      // TBM flavors:
      _devices["notbm"]         = TBM_NONE;
      _devices["tbmemulator"]   = TBM_EMU;
      _devices["tbm08"]         = TBM_08;
      _devices["tbm08a"]        = TBM_08A;
      _devices["tbm08b"]        = TBM_08B;
      _devices["tbm08c"]        = TBM_08C;
      _devices["tbm09"]         = TBM_09;
      _devices["tbm09c"]        = TBM_09C;
      _devices["tbm10c"]        = TBM_10C;
    }

    std::map<std::string, uint8_t> _devices;
    DeviceDictionary(DeviceDictionary const&); // Don't Implement
    void operator=(DeviceDictionary const&); // Don't implement
  };

  
  /** Map for DTB analog & digital probe signal name lookup
   *  All signal names are lower case, check is case-insensitive.
   *  Singleton class, only one object of this floating around.
   */
  class ProbeDictionary {
  public:
    static ProbeDictionary * getInstance() {
      static ProbeDictionary instance; // Guaranteed to be destroyed.
      // Instantiated on first use.
      return &instance;
    }

    // Return the signal id for the probe signal in question:
    inline uint8_t getSignal(std::string name, uint8_t type) {
      // Looking for digital probe signal:
      if(type == PROBE_DIGITAL && _signals.find(name)->second._signal_dig != PROBE_NONE) {
	return _signals.find(name)->second._signal_dig;
      }
      // Looking for analog probe signal:
      else if(type == PROBE_ANALOG && _signals.find(name)->second._signal_ana != PROBE_NONE) {
	return _signals.find(name)->second._signal_ana;
      }
      // Couldn't find any matching signal:
      else { return type; }
    }

    // Return the signal name for the probe signal in question:
    inline std::string getName(uint8_t signal, uint8_t type) {
      for(std::map<std::string, probeConfig>::iterator iter = _signals.begin(); iter != _signals.end(); ++iter) {
	if(type == PROBE_DIGITAL && iter->second._signal_dig == signal && iter->second._preferred == true) {
	  return (*iter).first;
	}
	else if(type == PROBE_ANALOG && iter->second._signal_ana == signal && iter->second._preferred == true) {
	  return (*iter).first;
	}
      }
      return "";
    }

    // Return all (preferred) signal names for the type in question:
    inline std::vector<std::string> getAllNames(uint8_t type) {
      std::vector<std::string> names;
      for(std::map<std::string, probeConfig>::iterator iter = _signals.begin(); iter != _signals.end(); ++iter) {
	if(((type == PROBE_DIGITAL && iter->second._signal_dig != PROBE_NONE)
	    || (type == PROBE_ANALOG && iter->second._signal_ana != PROBE_NONE))
	   && (*iter).second._preferred == true) {
	  names.push_back((*iter).first);
	}
      }
      return names;
    }

    // Return all (preferred) signal names for a single type:
    inline std::vector<std::string> getAllAnalogNames() {return getAllNames(PROBE_ANALOG);}
    inline std::vector<std::string> getAllDigitalNames() {return getAllNames(PROBE_DIGITAL);}

  private:

    /** class to store a probe signal config
     */
    class probeConfig {
    public:
      probeConfig() {}
    probeConfig(uint8_t signal_dig, uint8_t signal_ana, bool preferred = true) : _signal_dig(signal_dig), _signal_ana(signal_ana), _preferred(preferred) {}
      uint8_t _signal_dig;
      uint8_t _signal_ana;
      bool _preferred;
    };

    ProbeDictionary() {
      // Probe name and values

      // Signals accessible via both analog and digital ports:
      _signals["tin"]    = probeConfig(PROBE_TIN,PROBEA_TIN);
      _signals["ctr"]    = probeConfig(PROBE_CTR,PROBEA_CTR);
      _signals["clk"]    = probeConfig(PROBE_CLK,PROBEA_CLK);
      _signals["sda"]    = probeConfig(PROBE_SDA,PROBEA_SDA);
      _signals["tout"]   = probeConfig(PROBE_TOUT,PROBEA_TOUT);
      _signals["rda"]    = probeConfig(PROBE_TOUT,PROBEA_TOUT);
      _signals["off"]    = probeConfig(PROBE_OFF,PROBEA_OFF);

      // Purely digital signals:
      _signals["sdasend"]    = probeConfig(PROBE_SDA_SEND,PROBE_NONE);
      _signals["pgtok"]      = probeConfig(PROBE_PG_TOK,PROBE_NONE);
      _signals["pgtrg"]      = probeConfig(PROBE_PG_TRG,PROBE_NONE);
      _signals["pgcal"]      = probeConfig(PROBE_PG_CAL,PROBE_NONE);

      _signals["pgresr"]     = probeConfig(PROBE_PG_RES_ROC,PROBE_NONE,false);
      _signals["pgresroc"]   = probeConfig(PROBE_PG_RES_ROC,PROBE_NONE);

      _signals["pgrest"]     = probeConfig(PROBE_PG_RES_TBM,PROBE_NONE,false);
      _signals["pgrestbm"]   = probeConfig(PROBE_PG_RES_TBM,PROBE_NONE);

      _signals["pgsync"]     = probeConfig(PROBE_PG_SYNC,PROBE_NONE);

      _signals["clkp"]       = probeConfig(PROBE_CLK_PRESEN,PROBE_NONE);
      _signals["clkpresent"] = probeConfig(PROBE_CLK_PRESEN,PROBE_NONE,false);

      _signals["clkg"]       = probeConfig(PROBE_CLK_GOOD,PROBE_NONE);
      _signals["clkgood"]    = probeConfig(PROBE_CLK_GOOD,PROBE_NONE,false);

      _signals["daq0wr"]     = probeConfig(PROBE_DAQ0_WR,PROBE_NONE);
      _signals["crc"]        = probeConfig(PROBE_CRC,PROBE_NONE);
      _signals["adcrunning"] = probeConfig(PROBE_ADC_RUNNING,PROBE_NONE);
      _signals["adcrun"]     = probeConfig(PROBE_ADC_RUN,PROBE_NONE);
      _signals["adcpgate"]   = probeConfig(PROBE_ADC_PGATE,PROBE_NONE);
      _signals["adcstart"]   = probeConfig(PROBE_ADC_START,PROBE_NONE);
      _signals["adcsgate"]   = probeConfig(PROBE_ADC_SGATE,PROBE_NONE);
      _signals["adcs"]       = probeConfig(PROBE_ADC_S,PROBE_NONE);

      _signals["ds_gate"]      = probeConfig(PROBE_DS_GATE,PROBE_NONE);
      
      _signals["deser_frameerror"] = probeConfig(PROBE_FRAME_ERROR,PROBE_NONE);
      _signals["deser_codeerror"]  = probeConfig(PROBE_CODE_ERROR,PROBE_NONE);
      _signals["deser_error"]      = probeConfig(PROBE_ERROR,PROBE_NONE);

      _signals["deser_header"]       = probeConfig(PROBE_A_HEADER,PROBE_NONE);
      _signals["deser_packet"]       = probeConfig(PROBE_A_PACKET,PROBE_NONE);
      _signals["deser_tbmhdr"]       = probeConfig(PROBE_A_TBM_HDR,PROBE_NONE);
      _signals["deser_rochdr"]       = probeConfig(PROBE_A_ROC_HDR,PROBE_NONE);
      _signals["deser_tbmtrl"]       = probeConfig(PROBE_A_TBM_TRL,PROBE_NONE);
      _signals["deser_idle_error"]   = probeConfig(PROBE_A_IDLE_ERROR,PROBE_NONE);
      _signals["deser_header_error"] = probeConfig(PROBE_A_HDR_ERROR,PROBE_NONE);

      // Purely analog signals:
      _signals["sdata1"] = probeConfig(PROBE_NONE,PROBEA_SDATA1);
      _signals["sdata2"] = probeConfig(PROBE_NONE,PROBEA_SDATA2);
    }

    std::map<std::string, probeConfig> _signals;
    ProbeDictionary(ProbeDictionary const&); // Don't Implement
    void operator=(ProbeDictionary const&); // Don't implement
  };


  /** Map for pattern generator and direct trigger signal name lookup
   *  All signal names are lower case, check is case-insensitive.
   *  Singleton class, only one object of this floating around.
   */
  class PatternDictionary {
  public:
    static PatternDictionary * getInstance() {
      static PatternDictionary instance; // Guaranteed to be destroyed.
      // Instantiated on first use.
      return &instance;
    }

    // Return the register id for the name in question:
    inline uint16_t getSignal(std::string name, uint8_t type) {
      // Looking for pattern generator signal:
      if(type == PATTERN_PG && _signals.find(name)->second._signal_pg != PATTERN_ERR) {
	return _signals.find(name)->second._signal_pg;
      }
      // Looking for single trigger signal:
      else if(type == PATTERN_TRG && _signals.find(name)->second._signal_trg != PATTERN_ERR) {
	return _signals.find(name)->second._signal_trg;
      }
      // Couldn't find any matching signal:
      else { return PATTERN_ERR; }
    }

    // Return the signal name for the signal in question:
    inline std::string getName(uint16_t signal, uint8_t type) {
      for(std::map<std::string, patternConfig>::iterator iter = _signals.begin(); iter != _signals.end(); ++iter) {
	if(type == PATTERN_PG && iter->second._signal_pg == signal && iter->second._preferred == true) {
	  return (*iter).first;
	}
	else if(type == PATTERN_TRG && iter->second._signal_trg == signal && iter->second._preferred == true) {
	  return (*iter).first;
	}
      }
      return "";
    }

  private:

    /** class to store a probe signal config
     */
    class patternConfig {
    public:
      patternConfig() {}
    patternConfig(uint16_t signal_pg, uint16_t signal_trg, bool preferred = true) : _signal_pg(signal_pg), _signal_trg(signal_trg), _preferred(preferred) {}
      uint16_t _signal_pg;  // Register for Pattern Generator
      uint16_t _signal_trg; // Register for Single Signal Direct
      bool _preferred;
    };

    PatternDictionary() {
      // None (empty cycle):
      _signals["none"]      = patternConfig(PATTERN_NONE,PATTERN_NONE);
      _signals["empty"]     = patternConfig(PATTERN_NONE,PATTERN_NONE,false);
      _signals["delay"]     = patternConfig(PATTERN_NONE,PATTERN_NONE,false);
      
      // Token:
      _signals["pg_tok"]    = patternConfig(PG_TOK,PATTERN_ERR);
      _signals["tok"]       = patternConfig(PG_TOK,PATTERN_ERR,false);
      _signals["token"]     = patternConfig(PG_TOK,PATTERN_ERR,false);

      // Trigger:
      _signals["pg_trg"]    = patternConfig(PG_TRG,TRG_SEND_TRG,false);
      _signals["trg"]       = patternConfig(PG_TRG,TRG_SEND_TRG,false);
      _signals["trigger"]   = patternConfig(PG_TRG,TRG_SEND_TRG);

      // Calibrate signal
      _signals["pg_cal"]    = patternConfig(PG_CAL,TRG_SEND_CAL,false);
      _signals["cal"]       = patternConfig(PG_CAL,TRG_SEND_CAL,false);
      _signals["calibrate"] = patternConfig(PG_CAL,TRG_SEND_CAL);

      // ROC Reset Signal
      _signals["pg_resr"]   = patternConfig(PG_RESR,TRG_SEND_RSR,false);
      _signals["resr"]      = patternConfig(PG_RESR,TRG_SEND_RSR,false);
      _signals["resetroc"]  = patternConfig(PG_RESR,TRG_SEND_RSR);

      // TBM Reset Signal
      _signals["pg_rest"]   = patternConfig(PG_REST,TRG_SEND_RST,false);
      _signals["rest"]      = patternConfig(PG_REST,TRG_SEND_RST,false);
      _signals["resettbm"]  = patternConfig(PG_REST,TRG_SEND_RST);

      // PG Sync Signal
      _signals["pg_sync"]   = patternConfig(PG_SYNC,TRG_SEND_SYN,false);
      _signals["sync"]      = patternConfig(PG_SYNC,TRG_SEND_SYN);
    }

    std::map<std::string, patternConfig> _signals;
    PatternDictionary(PatternDictionary const&); // Don't Implement
    void operator=(PatternDictionary const&); // Don't implement
  };

  /** Map for trigger signal name lookup
   *  All signal names are lower case, check is case-insensitive.
   *  Singleton class, only one object of this floating around.
   */
  class TriggerDictionary {
  public:
    static TriggerDictionary * getInstance() {
      static TriggerDictionary instance; // Guaranteed to be destroyed.
      // Instantiated on first use.
      return &instance;
    }

    // Return the register id for the name in question:
    inline uint16_t getSignal(std::string name) {
      if(_signals.find(name) != _signals.end()) { return _signals.find(name)->second._trigger_type; }
      else { return TRG_ERR; }
    }

    // Return the emulation status for the name in question:
    inline bool getEmulationState(std::string name) {
      if(_signals.find(name) != _signals.end()) { return _signals.find(name)->second._tbm_emulation; }
      else { return 0; }
    }

    // Return the emulation status for the trigger register in question:
    inline bool getEmulationState(uint16_t signal) {
      for(std::map<std::string, triggerConfig>::iterator iter = _signals.begin(); iter != _signals.end(); ++iter) {
	if(iter->second._trigger_type == signal) { return iter->second._tbm_emulation; }
      }
      return 0;
    }

    // Return the signal name for the trigger type in question:
    inline std::string getName(uint16_t signal) {
      for(std::map<std::string, triggerConfig>::iterator iter = _signals.begin(); iter != _signals.end(); ++iter) {
	if(iter->second._trigger_type == signal && iter->second._preferred == true) { return iter->first; }
      }
      return "";
    }

    // Return all (preferred) trigger source names:
    inline std::vector<std::string> getAllNames() {
      std::vector<std::string> names;
      for(std::map<std::string, triggerConfig>::iterator iter = _signals.begin(); iter != _signals.end(); ++iter) {
	if(iter->second._preferred == true) { names.push_back(iter->first); }
      }
      return names;
    }

  private:
    /** class to store a trigger config
     */
    class triggerConfig {
    public:
      triggerConfig() {};
    triggerConfig(uint16_t trigger_type, bool tbm_emulation = false, bool preferred = true) : _trigger_type(trigger_type), _tbm_emulation(tbm_emulation), _preferred(preferred) {};
      uint16_t _trigger_type;  // Register for trigger type
      bool _tbm_emulation; // Store if this trigger is routed via the soft TBM and adds its header/trailer
      bool _preferred;
    };

    TriggerDictionary() {
      // No trigger source selected:
      _signals["none"]             = triggerConfig(TRG_SEL_NONE,false);

      // Asynchronous external triggers:
      _signals["async"]            = triggerConfig(TRG_SEL_ASYNC,true);
      _signals["extern"]           = triggerConfig(TRG_SEL_ASYNC,true,false);
      _signals["async_dir"]        = triggerConfig(TRG_SEL_ASYNC_DIR,false);
      _signals["extern_dir"]       = triggerConfig(TRG_SEL_ASYNC_DIR,false,false);

      // Synchronous external triggers:
      _signals["sync"]             = triggerConfig(TRG_SEL_SYNC,true);
      _signals["sync_dir"]         = triggerConfig(TRG_SEL_SYNC_DIR,false);

      // External triggered Pattern Generator:
      _signals["async_pg"]         = triggerConfig(TRG_SEL_ASYNC_PG, false);
      _signals["extern_pg"]        = triggerConfig(TRG_SEL_ASYNC_PG, false, false);

      // Single event injection:
      _signals["single"]           = triggerConfig(TRG_SEL_SINGLE,true);
      _signals["single_dir"]       = triggerConfig(TRG_SEL_SINGLE_DIR,false);
      _signals["single_direct"]    = triggerConfig(TRG_SEL_SINGLE_DIR,false,false);

      // Internal Trigger Generator
      _signals["random"]           = triggerConfig(TRG_SEL_GEN,true);
      _signals["random_dir"]       = triggerConfig(TRG_SEL_GEN_DIR,false);
      _signals["periodic"]         = triggerConfig(TRG_SEL_GEN,true);
      _signals["periodic_dir"]     = triggerConfig(TRG_SEL_GEN_DIR,false);
      
      // Pattern Generator
      _signals["pg"]               = triggerConfig(TRG_SEL_PG,true);
      _signals["patterngenerator"] = triggerConfig(TRG_SEL_PG,true,false);
      _signals["pg_dir"]           = triggerConfig(TRG_SEL_PG_DIR,false);
      _signals["pg_direct"]        = triggerConfig(TRG_SEL_PG_DIR,false,false);

      _signals["chain"]            = triggerConfig(TRG_SEL_CHAIN,false);
      _signals["sync_out"]         = triggerConfig(TRG_SEL_SYNC_OUT,false);
    }

    std::map<std::string, triggerConfig> _signals;
    TriggerDictionary(TriggerDictionary const&); // Don't Implement
    void operator=(TriggerDictionary const&); // Don't implement
  };

} //namespace pxar

#endif /* PXAR_DICTIONARIES_H */
