// RPC functions for the DTB emulator
#include "rpc_calls.h"
#include "generator.h"
#include "helper.h"
#include "config.h"
#include "constants.h"
#include <vector>

using namespace pxar;

void CTestboard::GetInfo(std::string &message) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  message = " pxarCore DTB Emulator \n "
    + std::string(PACKAGE_STRING)
    + "\n";
}

uint16_t CTestboard::GetBoardId() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  return 0x0;
}

void CTestboard::GetHWVersion(std::string &rpc_par1) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  rpc_par1 = "Hardware Revision 0";
}

uint16_t CTestboard::GetFWVersion() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  return 0x0;
}

uint16_t CTestboard::GetSWVersion() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  return 0x0;
}

uint16_t CTestboard::UpgradeGetVersion() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  return 0x0100;
}

uint8_t CTestboard::UpgradeStart(uint16_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  return 0;
}

uint8_t CTestboard::UpgradeData(std::string &) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  return 0;
}

uint8_t CTestboard::UpgradeError() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  return 0;
}

void CTestboard::UpgradeErrorMsg(std::string &rpc_par1) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  rpc_par1 = "No error.";
}

void CTestboard::UpgradeExec(uint16_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::Init() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::Welcome() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::SetLed(uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::cDelay(uint16_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::uDelay(uint16_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  pxar::mDelay(1);
}

// Emulator always has the same clock:
void CTestboard::SetClockSource(uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

bool CTestboard::IsClockPresent() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  return true;
}

void CTestboard::SetClock(uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::SetClockStretch(uint8_t, uint16_t, uint16_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::Sig_SetMode(uint8_t, uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::Sig_SetPRBS(uint8_t, uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::Sig_SetDelay(uint8_t, uint16_t, int8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::Sig_SetLevel(uint8_t, uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::Sig_SetOffset(uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::Sig_SetLVDS() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::Sig_SetLCDS() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::Sig_SetRdaToutDelay(uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::SignalProbeD1(uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::SignalProbeD2(uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::SignalProbeA1(uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::SignalProbeA2(uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::SignalProbeADC(uint8_t, uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::Pon() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::Poff() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::_SetVD(uint16_t voltage) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  vd = voltage;
}

void CTestboard::_SetVA(uint16_t voltage) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  va = voltage;
}

void CTestboard::_SetID(uint16_t current) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  id = current;
}

void CTestboard::_SetIA(uint16_t current) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  ia = current;
}

uint16_t CTestboard::_GetVD() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  return vd;
}

uint16_t CTestboard::_GetVA() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  return va;
}

uint16_t CTestboard::_GetID() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  return id;
}

uint16_t CTestboard::_GetIA() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  return ia;
}

uint16_t CTestboard::_GetVD_Reg() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  return vd;
}

uint16_t CTestboard::_GetVDAC_Reg() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  return vd;
}

uint16_t CTestboard::_GetVD_Cap() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  return vd;
}

void CTestboard::HVon() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::HVoff() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::ResetOn() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::ResetOff() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

uint8_t CTestboard::GetStatus() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  return 0;
}

void CTestboard::SetRocAddress(uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::Pg_SetCmd(uint16_t, uint16_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

// FIXME PG could be used for real.
void CTestboard::Pg_SetCmdAll(std::vector<uint16_t> &) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::Pg_SetSum(uint16_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::Pg_Stop() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::Pg_Single() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::Pg_Trigger() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

// Receiving triggers for PG:
void CTestboard::Pg_Triggers(uint32_t nTriggers, uint16_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");

  // Check how many open DAQ channels we have:
  size_t channels = std::count(daq_status.begin(), daq_status.end(), true);
  // Distribute the ROCs evenly:
  size_t roc_per_ch = roci2c.size()/channels;

  for(size_t i = 0; i < nTriggers; i++) {
    for(size_t ch = 0; ch < channels; ch++) {
      fillRawData(i,daq_buffer.at(ch),tbmtype,roc_per_ch,false,true,0,0);
    }
  }
}

// FIXME Receiving loop command
void CTestboard::Pg_Loop(uint16_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  // Set DAQ into state where it always returns events.
}

// Trigger selection
void CTestboard::Trigger_Select(uint16_t src) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  // Store trigger:
  trigger = src;
  // Triggers via TBM Emulator:
  if((src & 0x00f0) != 0 || src == 0x0100) tbmtype = TBM_EMU;
}

void CTestboard::Trigger_Delay(uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::Trigger_Timeout(uint16_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::Trigger_SetGenPeriodic(uint32_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::Trigger_SetGenRandom(uint32_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::Trigger_Send(uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

// DAQ Open
uint32_t CTestboard::Daq_Open(uint32_t buffersize, uint8_t channel) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");

  if(channel > daq_buffer.size()) return 0;
  
  // Reserve some memory (not necessary but nice...)
  daq_buffer.at(channel).reserve(buffersize/2);

  return daq_buffer.at(channel).capacity();
}

void CTestboard::Daq_Close(uint8_t channel) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  // Clear DAQ buffer
  daq_buffer.at(channel).clear();
}

void CTestboard::Daq_Start(uint8_t channel) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  daq_status.at(channel) = true;
  daq_event.at(channel) = 0;
}

void CTestboard::Daq_Stop(uint8_t channel) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  daq_status.at(channel) = false;
}

uint32_t CTestboard::Daq_GetSize(uint8_t channel) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  if(daq_status.at(channel)) return daq_buffer.at(channel).size();
  else return 0;
}

uint8_t CTestboard::Daq_FillLevel(uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  // We are always on 30%:
  return 30;
}

uint8_t CTestboard::Daq_FillLevel() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  // We are always on 30%:
  return 30;
}

uint8_t CTestboard::Daq_Read(std::vector<uint16_t> &data, uint32_t blocksize, uint8_t channel) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  uint32_t available = 0;
  return Daq_Read(data, blocksize, available, channel);
}

uint8_t CTestboard::Daq_Read(std::vector<uint16_t> &data, uint32_t blocksize, uint32_t &available, uint8_t channel) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  data.clear();

  // If we are on external triggers, just deliver one event per channel:
  if(trigger == TRG_SEL_ASYNC || trigger == TRG_SEL_ASYNC_DIR) {
    if(!daq_status.at(channel)) { available = 0; return 0; }
    fillRawData(daq_event.at(channel)++,daq_buffer.at(channel),tbmtype,roci2c.size(),false,true,0,0);
    mDelay(10);
  }
  
  // Return correct blocksize. Since this is given in Bytes,
  // we deliver blocksize/2 16bit words:

  std::vector<uint16_t>::iterator copy_end =
    (blocksize/2 < daq_buffer.at(channel).size() ? (daq_buffer.at(channel).begin() + blocksize/2) : daq_buffer.at(channel).end());

  data.insert(data.end(),daq_buffer.at(channel).begin(),copy_end);
  daq_buffer.at(channel).erase(daq_buffer.at(channel).begin(),copy_end);
  
  return 0;
}

void CTestboard::Daq_Select_ADC(uint16_t, uint8_t, uint8_t, uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::Daq_Select_Deser160(uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::Daq_Select_Deser400() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  // Produce TBM headers!
}

void CTestboard::Daq_Deser400_Reset(uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::Daq_Deser400_OldFormat(bool) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::Daq_Select_Datagenerator(uint16_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::Daq_DeselectAll() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

// Collect all ROCs that have ever been programmed:
void CTestboard::roc_I2cAddr(uint8_t i2c) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  std::vector<uint8_t>::iterator thisroc = std::find(roci2c.begin(),roci2c.end(),i2c);
  if(thisroc == roci2c.end()) roci2c.push_back(i2c);
}

void CTestboard::roc_ClrCal() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::roc_SetDAC(uint8_t, uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::roc_Pix(uint8_t, uint8_t, uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::roc_Pix_Trim(uint8_t, uint8_t, uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::roc_Pix_Mask(uint8_t, uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::roc_Pix_Cal(uint8_t, uint8_t, bool) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::roc_Col_Enable(uint8_t, bool) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::roc_AllCol_Enable(bool) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::roc_Col_Mask(uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::roc_Chip_Mask() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

bool CTestboard::TBM_Present() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  return (tbmtype != TBM_NONE);
}

void CTestboard::tbm_Enable(bool tbm) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  if(tbm) tbmtype = TBM_08;
  else tbmtype = TBM_NONE;
}

void CTestboard::tbm_Addr(uint8_t, uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::mod_Addr(uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::tbm_Set(uint8_t, uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

bool CTestboard::tbm_Get(uint8_t, uint8_t &) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  return true;
}

bool CTestboard::tbm_GetRaw(uint8_t, uint32_t &) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  return true;
}

int16_t CTestboard::TrimChip(std::vector<int16_t> &) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  return 0;
}

// FIXME do we emulate loop interrupts?
void CTestboard::LoopInterruptReset() {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

void CTestboard::SetLoopTriggerDelay(uint16_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
}

bool CTestboard::SetI2CAddresses(std::vector<uint8_t> &rpc_par1) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  nrocs_loops = rpc_par1.size();
  return true;
}

// FIXME here we could implement masked pixels
bool CTestboard::SetTrimValues(uint8_t, std::vector<uint8_t> &) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  return true;
}

bool CTestboard::LoopMultiRocAllPixelsCalibrate(std::vector<uint8_t> &roci2cs, uint16_t nTriggers, uint16_t flags) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");

  // Check how many open DAQ channels we have:
  size_t channels = std::count(daq_status.begin(), daq_status.end(), true);
  // Distribute the ROCs evenly:
  size_t roc_per_ch = roci2cs.size()/channels;

  uint32_t event = 0;
  for(size_t i = 0; i < ROC_NUMCOLS; i++) {
    for(size_t j = 0; j < ROC_NUMROWS; j++) {
      for(size_t k = 0; k < nTriggers; k++) {
	for(size_t ch = 0; ch < channels; ch++) {
	  fillRawData(event,daq_buffer.at(ch),tbmtype,roc_per_ch,false,false,i,j,flags);
	}
	event++;
      }
    }
  }
  
  return 1;
}

bool CTestboard::LoopMultiRocOnePixelCalibrate(std::vector<uint8_t> &roci2cs, uint8_t column, uint8_t row, uint16_t nTriggers, uint16_t flags) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");

  // Check how many open DAQ channels we have:
  size_t channels = std::count(daq_status.begin(), daq_status.end(), true);
  // Distribute the ROCs evenly:
  size_t roc_per_ch = roci2cs.size()/channels;

  uint32_t event = 0;
  for(size_t k = 0; k < nTriggers; k++) {
    for(size_t ch = 0; ch < channels; ch++) {
      fillRawData(event,daq_buffer.at(ch),tbmtype,roc_per_ch,false,false,column,row,flags);
    }
    event++;
  }
  
  return 1;
}

bool CTestboard::LoopSingleRocAllPixelsCalibrate(uint8_t, uint16_t nTriggers, uint16_t flags) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  
  uint32_t event = 0;
  for(size_t i = 0; i < ROC_NUMCOLS; i++) {
    for(size_t j = 0; j < ROC_NUMROWS; j++) {
      for(size_t k = 0; k < nTriggers; k++) {
	fillRawData(event,daq_buffer.at(0),tbmtype,1,false,false,i,j,flags);
	event++;
      }
    }
  }
  
  return 1;
}

bool CTestboard::LoopSingleRocOnePixelCalibrate(uint8_t, uint8_t column, uint8_t row, uint16_t nTriggers, uint16_t flags) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");

  uint32_t event = 0;
  for(size_t k = 0; k < nTriggers; k++) {
    fillRawData(event,daq_buffer.at(0),tbmtype,1,false,false,column,row,flags);
    event++;
  }
  
  return 1;
}

bool CTestboard::LoopMultiRocAllPixelsDacScan(std::vector<uint8_t> &roci2cs, uint16_t nTriggers, uint16_t flags, uint8_t dacreg, uint8_t dacmin, uint8_t dacmax) {
  return LoopMultiRocAllPixelsDacScan(roci2cs, nTriggers, flags, dacreg, 1, dacmin, dacmax);
}

bool CTestboard::LoopMultiRocAllPixelsDacScan(std::vector<uint8_t> &roci2cs, uint16_t nTriggers, uint16_t flags, uint8_t, uint8_t dacstep, uint8_t dacmin, uint8_t dacmax) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");

  // Check how many open DAQ channels we have:
  size_t channels = std::count(daq_status.begin(), daq_status.end(), true);
  // Distribute the ROCs evenly:
  size_t roc_per_ch = roci2cs.size()/channels;

  uint8_t dachalf = static_cast<uint8_t>(dacmax-dacmin)/2;
  uint32_t event = 0;

  for(size_t i = 0; i < ROC_NUMCOLS; i++) {
    for(size_t j = 0; j < ROC_NUMROWS; j++) {
      for(size_t dac = 0; dac < static_cast<size_t>(dacmax-dacmin+1); dac += dacstep) {
	for(size_t k = 0; k < nTriggers; k++) {
	  for(size_t ch = 0; ch < channels; ch++) {
	    // Mimic some edge at 50% of the DAC range:
	    if(((flags&FLAG_RISING_EDGE) && dac > dachalf) || (!(flags&FLAG_RISING_EDGE) && dac < dachalf)) {
	      fillRawData(event,daq_buffer.at(ch),tbmtype,roc_per_ch,false,false,i,j,flags);
	    }
	    else { fillRawData(event,daq_buffer.at(ch),tbmtype,roc_per_ch,true, false,i,j,flags); }
	  }
	  event++;
	}
      }
    }
  }
  
  return 1;
}

bool CTestboard::LoopMultiRocOnePixelDacScan(std::vector<uint8_t> &roci2cs, uint8_t column, uint8_t row, uint16_t nTriggers, uint16_t flags, uint8_t dacreg, uint8_t dacmin, uint8_t dacmax) {
  return LoopMultiRocOnePixelDacScan(roci2cs, column, row, nTriggers, flags, dacreg, 1, dacmin, dacmax);
}

bool CTestboard::LoopMultiRocOnePixelDacScan(std::vector<uint8_t> &roci2cs, uint8_t column, uint8_t row, uint16_t nTriggers, uint16_t flags, uint8_t, uint8_t dacstep, uint8_t dacmin, uint8_t dacmax) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  
  // Check how many open DAQ channels we have:
  size_t channels = std::count(daq_status.begin(), daq_status.end(), true);
  // Distribute the ROCs evenly:
  size_t roc_per_ch = roci2cs.size()/channels;

  uint8_t dachalf = static_cast<uint8_t>(dacmax-dacmin)/2;
  uint32_t event = 0;

  for(size_t dac = 0; dac < static_cast<size_t>(dacmax-dacmin+1); dac += dacstep) {
    for(size_t k = 0; k < nTriggers; k++) {
      for(size_t ch = 0; ch < channels; ch++) {
	// Mimic some edge at 50% of the DAC range:
	if(((flags&FLAG_RISING_EDGE) && dac > dachalf) || (!(flags&FLAG_RISING_EDGE) && dac < dachalf)) {
	  fillRawData(event,daq_buffer.at(ch),tbmtype,roc_per_ch,false,false,column,row,flags);
	}
	else { fillRawData(event,daq_buffer.at(ch),tbmtype,roc_per_ch,true, false,column,row,flags); }
      }
      event++;
    }
  }
  
  return 1;
}

bool CTestboard::LoopSingleRocAllPixelsDacScan(uint8_t roci2c, uint16_t nTriggers, uint16_t flags, uint8_t dacreg, uint8_t dacmin, uint8_t dacmax) {
  return LoopSingleRocAllPixelsDacScan(roci2c, nTriggers, flags, dacreg, 1, dacmin, dacmax);
}

bool CTestboard::LoopSingleRocAllPixelsDacScan(uint8_t, uint16_t nTriggers, uint16_t flags, uint8_t, uint8_t dacstep, uint8_t dacmin, uint8_t dacmax) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");

  uint8_t dachalf = static_cast<uint8_t>(dacmax-dacmin)/2;
  uint32_t event = 0;

  for(size_t i = 0; i < ROC_NUMCOLS; i++) {
    for(size_t j = 0; j < ROC_NUMROWS; j++) {
      for(size_t dac = 0; dac < static_cast<size_t>(dacmax-dacmin+1); dac += dacstep) {
	for(size_t k = 0; k < nTriggers; k++) {
	  // Mimic some edge at 50% of the DAC range:
	  if(((flags&FLAG_RISING_EDGE) && dac > dachalf) || (!(flags&FLAG_RISING_EDGE) && dac < dachalf)) {
	    fillRawData(event,daq_buffer.at(0),tbmtype,1,false,false,i,j,flags);
	  }
	  else { fillRawData(event,daq_buffer.at(0),tbmtype,1,true, false,i,j,flags); }
	  event++;
	}
      }
    }
  }
  
  return 1;
}

bool CTestboard::LoopSingleRocOnePixelDacScan(uint8_t roci2c, uint8_t column, uint8_t row, uint16_t nTriggers, uint16_t flags, uint8_t dacreg, uint8_t dacmin, uint8_t dacmax) {
  return LoopSingleRocOnePixelDacScan(roci2c, column, row, nTriggers, flags, dacreg, 1, dacmin, dacmax);
}

bool CTestboard::LoopSingleRocOnePixelDacScan(uint8_t, uint8_t column, uint8_t row, uint16_t nTriggers, uint16_t flags, uint8_t, uint8_t dacstep, uint8_t dacmin, uint8_t dacmax) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  
  uint8_t dachalf = static_cast<uint8_t>(dacmax-dacmin)/2;
  uint32_t event = 0;

  for(size_t dac = 0; dac < static_cast<size_t>(dacmax-dacmin+1); dac += dacstep) {
    for(size_t k = 0; k < nTriggers; k++) {
      // Mimic some edge at 50% of the DAC range:
      if(((flags&FLAG_RISING_EDGE) && dac > dachalf) || (!(flags&FLAG_RISING_EDGE) && dac < dachalf)) {
	fillRawData(event,daq_buffer.at(0),tbmtype,1,false,false,column,row,flags);
      }
      else { fillRawData(event,daq_buffer.at(0),tbmtype,1,true, false,column,row,flags); }
    }
    event++;
  }
  
  return 1;
}

bool CTestboard::LoopMultiRocAllPixelsDacDacScan(std::vector<uint8_t> &roci2cs, uint16_t nTriggers, uint16_t flags, uint8_t dac1reg, uint8_t dac1min, uint8_t dac1max, uint8_t dac2reg, uint8_t dac2min, uint8_t dac2max) {
  return LoopMultiRocAllPixelsDacDacScan(roci2cs, nTriggers, flags, dac1reg, 1, dac1min, dac1max, dac2reg, 1, dac2min, dac2max);
}

bool CTestboard::LoopMultiRocAllPixelsDacDacScan(std::vector<uint8_t> &roci2cs, uint16_t nTriggers, uint16_t flags, uint8_t, uint8_t dac1step, uint8_t dac1min, uint8_t dac1max, uint8_t, uint8_t dac2step, uint8_t dac2min, uint8_t dac2max) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");

  // Check how many open DAQ channels we have:
  size_t channels = std::count(daq_status.begin(), daq_status.end(), true);
  // Distribute the ROCs evenly:
  size_t roc_per_ch = roci2cs.size()/channels;

  uint32_t event = 0;

  for(size_t i = 0; i < ROC_NUMCOLS; i++) {
    for(size_t j = 0; j < ROC_NUMROWS; j++) {
      for(size_t dac1 = 0; dac1 < static_cast<size_t>(dac1max-dac1min+1); dac1 += dac1step) {
	for(size_t dac2 = 0; dac2 < static_cast<size_t>(dac2max-dac2min+1); dac2 += dac2step) {
	  for(size_t k = 0; k < nTriggers; k++) {
	    for(size_t ch = 0; ch < channels; ch++) {
	      // Mimic some working band of the two DACs:
	      if(isInTornadoRegion(dac1min, dac1max, dac1, dac2min, dac2max, dac2)) {
		fillRawData(event,daq_buffer.at(ch),tbmtype,roc_per_ch,false,false,i,j,flags);
	      }
	      else { fillRawData(event,daq_buffer.at(ch),tbmtype,roc_per_ch,true, false,i,j,flags); }
	    }
	    event++;
	  }
	}
      }
    }
  }
  
  return 1;
}

bool CTestboard::LoopMultiRocOnePixelDacDacScan(std::vector<uint8_t> &roci2cs, uint8_t column, uint8_t row, uint16_t nTriggers, uint16_t flags, uint8_t dac1reg, uint8_t dac1min, uint8_t dac1max, uint8_t dac2reg, uint8_t dac2min, uint8_t dac2max) {
  return LoopMultiRocOnePixelDacDacScan(roci2cs, column, row, nTriggers, flags, dac1reg, 1, dac1min, dac1max, dac2reg, 1, dac2min, dac2max);
}

bool CTestboard::LoopMultiRocOnePixelDacDacScan(std::vector<uint8_t> &roci2cs, uint8_t column, uint8_t row, uint16_t nTriggers, uint16_t flags, uint8_t, uint8_t dac1step, uint8_t dac1min, uint8_t dac1max, uint8_t, uint8_t dac2step, uint8_t dac2min, uint8_t dac2max) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");

  // Check how many open DAQ channels we have:
  size_t channels = std::count(daq_status.begin(), daq_status.end(), true);
  // Distribute the ROCs evenly:
  size_t roc_per_ch = roci2cs.size()/channels;

  uint32_t event = 0;

  for(size_t dac1 = 0; dac1 < static_cast<size_t>(dac1max-dac1min+1); dac1 += dac1step) {
    for(size_t dac2 = 0; dac2 < static_cast<size_t>(dac2max-dac2min+1); dac2 += dac2step) {
      for(size_t k = 0; k < nTriggers; k++) {
	for(size_t ch = 0; ch < channels; ch++) {
	  // Mimic some working band of the two DACs:
	  if(isInTornadoRegion(dac1min, dac1max, dac1, dac2min, dac2max, dac2)) {
	    fillRawData(event,daq_buffer.at(ch),tbmtype,roc_per_ch,false,false,column,row,flags);
	  }
	  else { fillRawData(event,daq_buffer.at(ch),tbmtype,roc_per_ch,true, false,column,row,flags); }
	}
	event++;
      }
    }
  }
  
  return 1;
}

bool CTestboard::LoopSingleRocAllPixelsDacDacScan(uint8_t roci2c, uint16_t nTriggers, uint16_t flags, uint8_t dac1reg, uint8_t dac1min, uint8_t dac1max, uint8_t dac2reg, uint8_t dac2min, uint8_t dac2max) {
  return LoopSingleRocAllPixelsDacDacScan(roci2c, nTriggers, flags, dac1reg, 1, dac1min, dac1max, dac2reg, 1, dac2min, dac2max);
}

bool CTestboard::LoopSingleRocAllPixelsDacDacScan(uint8_t, uint16_t nTriggers, uint16_t flags, uint8_t, uint8_t dac1step, uint8_t dac1min, uint8_t dac1max, uint8_t, uint8_t dac2step, uint8_t dac2min, uint8_t dac2max) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");

  uint32_t event = 0;

  for(size_t i = 0; i < ROC_NUMCOLS; i++) {
    for(size_t j = 0; j < ROC_NUMROWS; j++) {
      for(size_t dac1 = 0; dac1 < static_cast<size_t>(dac1max-dac1min+1); dac1 += dac1step) {
	for(size_t dac2 = 0; dac2 < static_cast<size_t>(dac2max-dac2min+1); dac2 += dac2step) {
	  for(size_t k = 0; k < nTriggers; k++) {
	    // Mimic some working band of the two DACs:
	    if(isInTornadoRegion(dac1min, dac1max, dac1, dac2min, dac2max, dac2)) {
	      fillRawData(event,daq_buffer.at(0),tbmtype,1,false,false,i,j,flags);
	    }
	    else { fillRawData(event,daq_buffer.at(0),tbmtype,1,true, false,i,j,flags); }
	  }
	  event++;
	}
      }
    }
  }
  
  return 1;
}

bool CTestboard::LoopSingleRocOnePixelDacDacScan(uint8_t roci2c, uint8_t column, uint8_t row, uint16_t nTriggers, uint16_t flags, uint8_t dac1reg, uint8_t dac1min, uint8_t dac1max, uint8_t dac2reg, uint8_t dac2min, uint8_t dac2max) {
  return LoopSingleRocOnePixelDacDacScan(roci2c, column, row, nTriggers, flags, dac1reg, 1, dac1min, dac1max, dac2reg, 1, dac2min, dac2max);
}

bool CTestboard::LoopSingleRocOnePixelDacDacScan(uint8_t, uint8_t column, uint8_t row, uint16_t nTriggers, uint16_t flags, uint8_t, uint8_t dac1step, uint8_t dac1min, uint8_t dac1max, uint8_t, uint8_t dac2step, uint8_t dac2min, uint8_t dac2max) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");

  uint32_t event = 0;

  for(size_t dac1 = 0; dac1 < static_cast<size_t>(dac1max-dac1min+1); dac1 += dac1step) {
    for(size_t dac2 = 0; dac2 < static_cast<size_t>(dac2max-dac2min+1); dac2 += dac2step) {
      for(size_t k = 0; k < nTriggers; k++) {
	// Mimic some working band of the two DACs:
	if(isInTornadoRegion(dac1min, dac1max, dac1, dac2min, dac2max, dac2)) {
	  fillRawData(event,daq_buffer.at(0),tbmtype,1,false,false,column,row,flags);
	}
	else { fillRawData(event,daq_buffer.at(0),tbmtype,1,true, false,column,row,flags); }
      }
      event++;
    }
  }
  
  return 1;
}

uint16_t CTestboard::GetADC(uint8_t) {
  LOG4CPLUS_DEBUG(rpcLogger, "called.");
  return 0;
}

