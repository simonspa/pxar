/**
 * pxar API class implementation
 */
#include "api.h"
#include "dut.h"
#include "hal.h"
#include "log.h"
#include "timer.h"
#include "helper.h"
#include "dictionaries.h"
#include <algorithm>
#include <fstream>
#include <cmath>
#include "constants.h"
#include "config.h"

using namespace pxar;

pxarCore::pxarCore(std::string usbId, std::string logLevel, bool do_Daq_MemReset) :
  _daq_running(false),
  _daq_buffersize(DTB_SOURCE_BUFFER_SIZE),
  _daq_startstop_warning(false)
{

  LOG(logQUIET) << "Instanciating API for " << PACKAGE_STRING;

  // Set up the libpxar API/HAL logging mechanism:
  Log::ReportingLevel() = Log::FromString(logLevel);
  LOG(logINFO) << "Log level: " << logLevel;

  // Get a new HAL instance with the DTB USB ID passed to the API constructor:
  _hal = new hal(usbId, do_Daq_MemReset);

  // Get the DUT up and running:
  _dut = new dut();
}

pxarCore::~pxarCore() {
  delete _dut;
  delete _hal;
}

std::string pxarCore::getVersion() { return PACKAGE_STRING; }

bool pxarCore::initTestboard(std::vector<std::pair<std::string,uint8_t> > sig_delays,
			std::vector<std::pair<std::string,double> > power_settings,
			std::vector<std::pair<std::string,uint8_t> > pg_setup) {

  // Check the HAL status before doing anything else:
  if(!_hal->compatible()) return false;

  // Collect and check the testboard configuration settings

  // Power settings:
  checkTestboardPower(power_settings);

  // Signal Delays:
  checkTestboardDelays(sig_delays);

  // Prepare Pattern Generator:
  verifyPatternGenerator(pg_setup);

  // Call the HAL to do the job:
  _hal->initTestboard(_dut->sig_delays,_dut->pg_setup,_dut->pg_sum,_dut->va,_dut->vd,_dut->ia,_dut->id);
  return true;
}

void pxarCore::setTestboardDelays(std::vector<std::pair<std::string,uint8_t> > sig_delays) {
  if(!_hal->status()) {
    LOG(logERROR) << "Signal delays not updated!";
    return;
  }
  checkTestboardDelays(sig_delays);
  _hal->setTestboardDelays(_dut->sig_delays);
  LOG(logDEBUGAPI) << "Testboard signal delays updated.";
}

void pxarCore::setPatternGenerator(std::vector<std::pair<std::string,uint8_t> > pg_setup) {
  if(!_hal->status()) {
    LOG(logERROR) << "Pattern generator not updated!";
    return;
  }
  verifyPatternGenerator(pg_setup);
  _hal->SetupPatternGenerator(_dut->pg_setup,_dut->pg_sum);
  LOG(logDEBUGAPI) << "Pattern generator verified and updated.";
}

void pxarCore::setTestboardPower(std::vector<std::pair<std::string,double> > power_settings) {
  if(!_hal->status()) {
    LOG(logERROR) << "Voltages/current limits not upated!";
    return;
  }
  checkTestboardPower(power_settings);
  _hal->setTestboardPower(_dut->va,_dut->vd,_dut->ia,_dut->id);
  LOG(logDEBUGAPI) << "Voltages/current limits updated.";
}

bool pxarCore::initDUT(uint8_t hubid,
		       std::string tbmtype,
		       std::vector<std::vector<std::pair<std::string,uint8_t> > > tbmDACs,
		       std::string roctype,
		       std::vector<std::vector<std::pair<std::string,uint8_t> > > rocDACs,
		       std::vector<std::vector<pixelConfig> > rocPixels) {
  std::vector<uint8_t> rocI2Cs;
  return initDUT(std::vector<uint8_t>(1,hubid), tbmtype, tbmDACs, roctype, rocDACs, rocPixels, rocI2Cs);
}

bool pxarCore::initDUT(std::vector<uint8_t> hubids,
		       std::string tbmtype,
		       std::vector<std::vector<std::pair<std::string,uint8_t> > > tbmDACs,
		       std::string roctype,
		       std::vector<std::vector<std::pair<std::string,uint8_t> > > rocDACs,
		       std::vector<std::vector<pixelConfig> > rocPixels) {
  std::vector<uint8_t> rocI2Cs;
  return initDUT(hubids, tbmtype, tbmDACs, roctype, rocDACs, rocPixels, rocI2Cs);
}

bool pxarCore::initDUT(uint8_t hubid,
		       std::string tbmtype,
		       std::vector<std::vector<std::pair<std::string,uint8_t> > > tbmDACs,
		       std::string roctype,
		       std::vector<std::vector<std::pair<std::string,uint8_t> > > rocDACs,
		       std::vector<std::vector<pixelConfig> > rocPixels,
		       std::vector<uint8_t> rocI2Cs) {
  return initDUT(std::vector<uint8_t>(1,hubid), tbmtype, tbmDACs, roctype, rocDACs, rocPixels, rocI2Cs);
}

bool pxarCore::initDUT(std::vector<uint8_t> hubids,
		       std::string tbmtype,
		       std::vector<std::vector<std::pair<std::string,uint8_t> > > tbmDACs,
		       std::string roctype,
		       std::vector<std::vector<std::pair<std::string,uint8_t> > > rocDACs,
		       std::vector<std::vector<pixelConfig> > rocPixels,
		       std::vector<uint8_t> rocI2Cs) {

  // Check if the HAL is ready:
  if(!_hal->status()) return false;

  // Verification/sanity checks of supplied DUT configuration values

  // Check if the number of hub ids and TBM core settings match:
  if(tbmDACs.size() <= 2) {
    // We need to set the global hub ID once, take the first, ignore the rest:
    LOG(logDEBUGAPI) << "Setting global HUB id " << static_cast<int>(hubids.front());
    _hal->setHubId(hubids.front());
  }
  // We only support maximum two hubs connected:
  else if(hubids.size() > 2) {
    LOG(logCRITICAL) << "Too many hub ids supplied. Only two hubs supported for Layer 1 modules...";
    throw InvalidConfig("Too many hub ids supplied.");
  }
  else if(2*hubids.size() != tbmDACs.size()) {
    LOG(logCRITICAL) << "Hm, we have " << tbmDACs.size() << " TBM Cores but " << hubids.size() << " HUB ids.";
    LOG(logCRITICAL) << "This cannot end well...";
    throw InvalidConfig("Mismatch between number of HUB addresses and TBM Cores");
  }
  else {
    // We have two hub ids - this calls for a Layer 1 module initialization:
    _hal->setHubId(hubids.front(), hubids.back());
  }

  // Check if I2C addresses were supplied - if so, check size agains sets of DACs:
  if(!rocI2Cs.empty()) {
    if(rocI2Cs.size() != rocDACs.size()) {
      LOG(logCRITICAL) << "Hm, we have " << rocI2Cs.size() << " I2C addresses but " << rocDACs.size() << " DAC configs.";
      LOG(logCRITICAL) << "This cannot end well...";
      throw InvalidConfig("Mismatch between number of I2C addresses and DAC configurations");
    }
    LOG(logDEBUGAPI) << "I2C addresses for all ROCs are provided as user input.";
  }
  else { LOG(logDEBUGAPI) << "I2C addresses will be automatically generated."; }

  // Check size of rocDACs and rocPixels against each other
  if(rocDACs.size() != rocPixels.size()) {
    LOG(logCRITICAL) << "Hm, we have " << rocDACs.size() << " DAC configs but " << rocPixels.size() << " pixel configs.";
    LOG(logCRITICAL) << "This cannot end well...";
    throw InvalidConfig("Mismatch between number of DAC and pixel configurations");
  }
  // check for presence of DAC/pixel configurations
  if (rocDACs.size() == 0 || rocPixels.size() == 0){
    LOG(logCRITICAL) << "No DAC/pixel configurations for any ROC supplied!";
    throw InvalidConfig("No DAC/pixel configurations for any ROC supplied");
  }
  // check individual pixel configs
  for(std::vector<std::vector<pixelConfig> >::iterator rocit = rocPixels.begin();rocit != rocPixels.end(); rocit++){
    // check pixel configuration sizes
    if ((*rocit).size() == 0){
      LOG(logWARNING) << "No pixel configured for ROC "<< static_cast<int>(rocit - rocPixels.begin()) << "!";
    }
    if ((*rocit).size() > 4160){
      LOG(logCRITICAL) << "Too many pixels (N_pixel="<< rocit->size() <<" > 4160) configured for ROC "<< static_cast<int>(rocit - rocPixels.begin()) << "!";
      throw InvalidConfig("Too many pixels (>4160) configured");
    }
    // check individual pixel configurations
    int nduplicates = 0;
    for(std::vector<pixelConfig>::iterator pixit = rocit->begin(); pixit != rocit->end(); pixit++){
      if (std::count_if(rocit->begin(),rocit->end(),findPixelXY(pixit->column(),pixit->row())) > 1){
	LOG(logCRITICAL) << "Config for pixel in column " << static_cast<int>(pixit->column()) << " and row "<< static_cast<int>(pixit->row()) << " present multiple times in ROC " << static_cast<int>(rocit-rocPixels.begin()) << "!";
	nduplicates++;
      }
    }
    if (nduplicates>0){
      throw InvalidConfig("Duplicate pixel configurations present");
    }

    // check for pixels out of range
    if (std::count_if((*rocit).begin(),(*rocit).end(),findPixelBeyondXY(51,79)) > 0) {
      LOG(logCRITICAL) << "Found pixels with values for column and row outside of valid address range on ROC "<< static_cast<int>(rocit - rocPixels.begin()) << "!";
      throw InvalidConfig("Found pixels with values for column and row outside of valid address range");
    }
  }
  // Check the DAC vectors:
  for(std::vector<std::vector<std::pair<std::string,uint8_t> > >::iterator it = rocDACs.begin(); it != rocDACs.end(); it++) {
    // check for enough DACs being supplied, set 10 DACs minimum as threshold.
    if(it->size() < 10) {
      LOG(logCRITICAL) << "Found only " << it->size() << " DAC settings for ROC "<< static_cast<int>(it - rocDACs.begin()) << "!";
      throw InvalidConfig("Found not enough DAC settings");
    }
  }

  LOG(logDEBUGAPI) << "We have " << rocDACs.size() << " DAC configs and " << rocPixels.size() << " pixel configs, with " << rocDACs.at(0).size() << " and " << rocPixels.at(0).size() << " entries for the first ROC, respectively.";

  // First initialized the API's DUT instance with the information supplied.

  // Initialize TBMs:
  LOG(logDEBUGAPI) << "Received settings for " << tbmDACs.size() << " TBM cores.";

  // Tampered flag for token chains:
  bool token_chains_tampered = false;

  for(std::vector<std::vector<std::pair<std::string,uint8_t> > >::iterator tbmIt = tbmDACs.begin(); tbmIt != tbmDACs.end(); ++tbmIt) {

    LOG(logDEBUGAPI) << "Processing TBM Core " << static_cast<int>(tbmIt - tbmDACs.begin());

    // Prepare a new TBM configuration of the given type:
    tbmConfig newtbm(stringToDeviceCode(tbmtype));

    // Set the hub id for this TBM core (same hub id for two cores):
    newtbm.hubid = hubids.at((tbmIt - tbmDACs.begin())/2);

    // Check if this is core alpha or beta and store it:
    if((tbmIt - tbmDACs.begin())%2 == 0) { newtbm.core = 0xE0; } // alpha core
    else { newtbm.core = 0xF0; } // beta core

    // Loop over all the DAC settings supplied and fill them into the TBM dacs
    for(std::vector<std::pair<std::string,uint8_t> >::iterator dacIt = (*tbmIt).begin(); dacIt != (*tbmIt).end(); ++dacIt) {

      // Fill the register pairs with the register id from the dictionary:
      uint8_t tbmregister, value = dacIt->second;
      if(!verifyRegister(dacIt->first, tbmregister, value, TBM_REG)) continue;

      // Check if this is a token chain length and store it:
      if(newtbm.tokenchains.size() > 0 && tbmregister == TBM_TOKENCHAIN_0) {
	newtbm.tokenchains.at(0) = value;
	LOG(logDEBUGAPI) << "TBM Core " << static_cast<int>(tbmIt - tbmDACs.begin())
			 << " data stream 1 configured to have a token chain with "
			 << static_cast<int>(value) << " ROCs.";
	token_chains_tampered = true;
	continue;
      }
      if(newtbm.tokenchains.size() > 1 && tbmregister == TBM_TOKENCHAIN_1) {
	newtbm.tokenchains.at(1) = value;
	LOG(logDEBUGAPI) << "TBM Core " << static_cast<int>(tbmIt - tbmDACs.begin())
			 << " data stream 2 configured to have a token chain with "
			 << static_cast<int>(value) << " ROCs.";
	token_chains_tampered = true;
	continue;
      }

      std::pair<std::map<uint8_t,uint8_t>::iterator,bool> ret;
      ret = newtbm.dacs.insert( std::make_pair(tbmregister,value) );
      if(ret.second == false) {
	LOG(logWARNING) << "Overwriting existing DAC \"" << dacIt->first
			<< "\" value " << static_cast<int>(ret.first->second)
			<< " with " << static_cast<int>(value);
	newtbm.dacs[tbmregister] = value;
      }
    }

    // Done. Enable bit is already set by tbmConfig constructor.
    _dut->tbm.push_back(newtbm);
  }

  // Check number of configured TBM cores. If we only got one register vector, we re-use it for the second TBM core:
  if(_dut->tbm.size() == 1) {
    LOG(logDEBUGAPI) << "Only register settings for one TBM core supplied. Duplicating to second core.";
    // Prepare a new TBM configuration and copy over all settings:
    tbmConfig newtbm(_dut->tbm.at(0).type);
    newtbm.tokenchains = _dut->tbm.at(0).tokenchains;
    // Flip the last bit of the TBM core identifier:
    newtbm.core = _dut->tbm.at(0).core ^ (1u << 4);

    // Copy  the register settings:
    for(std::map<uint8_t,uint8_t>::iterator reg = _dut->tbm.at(0).dacs.begin(); reg != _dut->tbm.at(0).dacs.end(); ++reg) {
      newtbm.dacs.insert(std::make_pair(reg->first,reg->second));
    }
    _dut->tbm.push_back(newtbm);
  }

  // Check if we have any TBM present to select termination for the DTB RDA/Tout input:
  if(!_dut->tbm.empty()) {
    // We have RDA input from a TBM, this needs LCDS termination:
    _hal->SigSetLCDS();
    LOG(logDEBUGAPI) << "RDA/Tout DTB input termination set to LCDS.";
  }
  else {
    // We expect the direct TokenOut signal from a ROC which needs LVDS termination:
    _hal->SigSetLVDS();
    LOG(logDEBUGAPI) << "RDA/Tout DTB input termination set to LVDS.";
  }


  // Initialize ROCs:
  for(std::vector<std::vector<std::pair<std::string,uint8_t> > >::iterator rocIt = rocDACs.begin(); rocIt != rocDACs.end(); ++rocIt){

    // Prepare a new ROC configuration
    rocConfig newroc;
    // Set the ROC type (get value from dictionary)
    newroc.type = stringToDeviceCode(roctype);
    if(newroc.type == 0x0) {
      LOG(logCRITICAL) << "Invalid ROC type \"" << roctype << "\"";
      throw InvalidConfig("Invalid ROC type.");
    }

    // If no I2C addresses have been supplied, we just assume they are consecutively numbered:
    if(rocI2Cs.empty()) { newroc.i2c_address = static_cast<uint8_t>(rocIt - rocDACs.begin()); }
    // if we have adresses, let's pick the right one and assign it:
    else { newroc.i2c_address = static_cast<uint8_t>(rocI2Cs.at(rocIt - rocDACs.begin())); }
    LOG(logDEBUGAPI) << "I2C address for the next ROC is: " << static_cast<int>(newroc.i2c_address);

    // Loop over all the DAC settings supplied and fill them into the ROC dacs
    for(std::vector<std::pair<std::string,uint8_t> >::iterator dacIt = (*rocIt).begin(); dacIt != (*rocIt).end(); ++dacIt){
      // Fill the DAC pairs with the register from the dictionary:
      uint8_t dacRegister, dacValue = dacIt->second;
      if(!verifyRegister(dacIt->first, dacRegister, dacValue, ROC_REG)) continue;

      std::pair<std::map<uint8_t,uint8_t>::iterator,bool> ret;
      ret = newroc.dacs.insert( std::make_pair(dacRegister,dacValue) );
      if(ret.second == false) {
	LOG(logWARNING) << "Overwriting existing DAC \"" << dacIt->first
			<< "\" value " << static_cast<int>(ret.first->second)
			<< " with " << static_cast<int>(dacValue);
	newroc.dacs[dacRegister] = dacValue;
      }
    }

    // Loop over all pixelConfigs supplied:
    for(std::vector<pixelConfig>::iterator pixIt = rocPixels.at(rocIt - rocDACs.begin()).begin(); pixIt != rocPixels.at(rocIt - rocDACs.begin()).end(); ++pixIt) {
      // Check the trim value to be within boundaries:
      if((*pixIt).trim() > 15) {
	LOG(logWARNING) << "Pixel "
			<< static_cast<int>((*pixIt).column()) << ", "
			<< static_cast<int>((*pixIt).row())<< " trim value "
			<< static_cast<int>((*pixIt).trim()) << " exceeds limit. Set to 15.";
	(*pixIt).setTrim(15);
      }
      // Push the pixelConfigs into the rocConfig:
      newroc.pixels.push_back(*pixIt);
    }

    // Done. Enable bit is already set by rocConfig constructor.
    _dut->roc.push_back(newroc);
  }

  // Printout for final token chain lengths selected for each TBM channel and calculate the sum:
  uint16_t nrocs_total = 0;
  for(std::vector<tbmConfig>::iterator tbm = _dut->tbm.begin(); tbm != _dut->tbm.end(); tbm++) {
    for(size_t i = 0; i < tbm->tokenchains.size(); i++) { nrocs_total += tbm->tokenchains.at(i); }
  }

  // Check number of ROCs agains total token chain length:
  if(!_dut->tbm.empty() && _dut->roc.size() != nrocs_total) {
    // Apparently we have a longer total token chain than we have ROCs.
    // Let's check if the user has tampered with the token chain lengths:
    if(!token_chains_tampered) {
      // No, it's the default token chain lengths.
      // Let's try to figure out where the ROC is missing using the standard I2C assignment

      // Reset the default token chain lengths:
      for(std::vector<tbmConfig>::iterator tbm = _dut->tbm.begin(); tbm != _dut->tbm.end(); tbm++) {
	for(size_t i = 0; i < tbm->tokenchains.size(); i++) { tbm->tokenchains.at(i) = 0; }
      }

      // Add every ROC to the token chain where it should belong according to standard module I2C assignment:
      for(std::vector<uint8_t>::iterator i2c = rocI2Cs.begin(); i2c != rocI2Cs.end(); i2c++) {
	// TBM 08: two token chains
	if(_dut->tbm.front().type < TBM_09) {
	  LOG(logDEBUGAPI) << "ROC@I2C " << static_cast<int>(*i2c) << " belongs to TBM Core " << (*i2c)/8 << ", readout channel " << (*i2c)/8;
	  _dut->tbm.at((*i2c)/8).tokenchains.at(0)++;
	}
	// single TBM 09: four token chains:
	else if(_dut->tbm.size() < 3) {
	  LOG(logDEBUGAPI) << "ROC@I2C " << static_cast<int>(*i2c) << " belongs to TBM Core " << (*i2c)/8 << ", readout channel " << (*i2c)%8/4;
	  _dut->tbm.at((*i2c)/8).tokenchains.at((*i2c)%8/4)++;
	}
	else { throw InvalidConfig("Mismatch between number of ROC configurations and total token chain length."); }
      }
    }
    else {
      // The user has changed the token lengths by hand, this has to be corrected...
      LOG(logCRITICAL) << "Hm, we have " << _dut->roc.size() << " ROC configurations but a total token chain length of " << nrocs_total << " ROCs.";
      LOG(logCRITICAL) << "This cannot end well...";
      throw InvalidConfig("Mismatch between number of ROC configurations and total token chain length.");
    }
  }

  for(std::vector<tbmConfig>::iterator tbm = _dut->tbm.begin(); tbm != _dut->tbm.end(); tbm++) {
    LOG(logDEBUGAPI) << "TBM Core " << tbm->corename()
		     << " Token Chains: " << listVector(tbm->tokenchains);
  }


  // All data is stored in the DUT struct, now programming it.
  _dut->_initialized = true;
  return programDUT();
}

bool pxarCore::programDUT() {

  if(!_dut->_initialized) {
    LOG(logERROR) << "DUT not initialized, unable to program it.";
    return false;
  }

  // First thing to do: startup DUT power if not yet done
  _hal->Pon();

  // Start programming the devices here!

  std::vector<tbmConfig> enabledTbms = _dut->getEnabledTbms();
  if(!enabledTbms.empty()) { LOG(logDEBUGAPI) << "Programming TBMs..."; }
  for (std::vector<tbmConfig>::iterator tbmit = enabledTbms.begin(); tbmit != enabledTbms.end(); ++tbmit){
    _hal->initTBMCore((*tbmit));
  }

  std::vector<rocConfig> enabledRocs = _dut->getEnabledRocs();
  if(!enabledRocs.empty()) {LOG(logDEBUGAPI) << "Programming ROCs...";}
  for (std::vector<rocConfig>::iterator rocit = enabledRocs.begin(); rocit != enabledRocs.end(); ++rocit){
    _hal->initROC(rocit->i2c_address,(*rocit).type, (*rocit).dacs);
  }

  // As last step, mask all pixels in the device and detach all double column readouts:
  MaskAndTrim(false);
  for (std::vector<rocConfig>::iterator rocit = _dut->roc.begin(); rocit != _dut->roc.end(); ++rocit) {
    _hal->AllColumnsSetEnable(rocit->i2c_address,true);
  }

  // Also clear all calibrate signals:
  SetCalibrateBits(false);

  // The DUT is programmed, everything all right:
  _dut->_programmed = true;

  return true;
}

// API status function, checks HAL and DUT statuses
bool pxarCore::status() {
  if(_hal->status() && _dut->status()) return true;
  return false;
}

// Lookup register and check value range
bool pxarCore::verifyRegister(std::string name, uint8_t &id, uint8_t &value, uint8_t type) {

  // Convert the name to lower case for comparison:
  std::transform(name.begin(), name.end(), name.begin(), ::tolower);

  // Get singleton DAC dictionary object:
  RegisterDictionary * _dict = RegisterDictionary::getInstance();

  // And get the register value from the dictionary object:
  id = _dict->getRegister(name,type);

  // Check if it was found:
  if(id == type) {
    LOG(logERROR) << "Invalid register name \"" << name << "\".";
    return false;
  }

  // Read register value limit:
  uint8_t regLimit = _dict->getSize(id, type);
  if(value > regLimit) {
    LOG(logWARNING) << "Register range overflow, set register \""
		    << name << "\" (" << static_cast<int>(id) << ") to "
		    << static_cast<int>(regLimit) << " (was: " << static_cast<int>(value) << ")";
    value = static_cast<uint8_t>(regLimit);
  }

  return true;
}

// Return the device code for the given name, return 0x0 if invalid:
uint8_t pxarCore::stringToDeviceCode(std::string name) {

  // Convert the name to lower case for comparison:
  std::transform(name.begin(), name.end(), name.begin(), ::tolower);
  LOG(logDEBUGAPI) << "Looking up device type for \"" << name << "\"";

  // Get singleton device dictionary object:
  DeviceDictionary * _devices = DeviceDictionary::getInstance();

  // And get the device code from the dictionary object:
  uint8_t _code = _devices->getDevCode(name);
  LOG(logDEBUGAPI) << "Device type return: " << static_cast<int>(_code);

  if(_code == 0x0) {LOG(logERROR) << "Unknown device: \"" << name << "\" could not be found in the dictionary!";}
  return _code;
}


// DTB functions

bool pxarCore::flashTB(std::string filename) {

  if(_hal->status() || _dut->status()) {
    LOG(logERROR) << "The testboard should only be flashed without initialization"
		  << " and with all attached DUTs powered down.";
    LOG(logERROR) << "Please power cycle the testboard and flash directly after startup!";
    return false;
  }

  // Try to open the flash file
  std::ifstream flashFile;

  LOG(logINFO) << "Trying to open " << filename;
  flashFile.open(filename.c_str(), std::ifstream::in);
  if(!flashFile.is_open()) {
    LOG(logERROR) << "Could not open specified DTB flash file \"" << filename<< "\"!";
    return false;
  }

  // Call the HAL routine to do the flashing:
  bool status = false;
  status = _hal->flashTestboard(flashFile);
  flashFile.close();

  return status;
}

double pxarCore::getTBia() {
  if(!_hal->status()) {return 0;}
  return _hal->getTBia();
}

double pxarCore::getTBva() {
  if(!_hal->status()) {return 0;}
  return _hal->getTBva();
}

double pxarCore::getTBid() {
  if(!_hal->status()) {return 0;}
  return _hal->getTBid();
}

double pxarCore::getTBvd() {
  if(!_hal->status()) {return 0;}
  return _hal->getTBvd();
}


void pxarCore::HVoff() {
  _hal->HVoff();
}

void pxarCore::HVon() {
  _hal->HVon();
}

void pxarCore::Poff() {
  _hal->Poff();
  // Reset the programmed state of the DUT (lost by turning off power)
  _dut->_programmed = false;
}

void pxarCore::Pon() {
  // Power is turned on when programming the DUT.
  // Re-program the DUT after power has been switched on:
  programDUT();
}

bool pxarCore::SignalProbe(std::string probe, std::string name, uint8_t channel) {

  if(!_hal->status()) {return false;}

  // Check selected channel to be within range of valid DAQ channels:
  if(channel >= DTB_DAQ_CHANNELS) throw InvalidConfig("No DAQ available for selected channel.");

  // Get singleton Probe dictionary object:
  ProbeDictionary * _dict = ProbeDictionary::getInstance();

  // Convert the probe name to lower case for comparison:
  std::transform(probe.begin(), probe.end(), probe.begin(), ::tolower);

  // Convert the name to lower case for comparison:
  std::transform(name.begin(), name.end(), name.begin(), ::tolower);

  // Digital signal probes:
  if(probe.compare(0,1,"d") == 0) {

    // And get the register value from the dictionary object:
    uint8_t signal = _dict->getSignal(name,PROBE_DIGITAL);
    LOG(logDEBUGAPI) << "Digital probe signal lookup for \"" << name
		     << "\" returned signal: " << static_cast<int>(signal);

    // Check if this is a DESER400 probe signal:
    if(name.compare(0,5,"deser") == 0) {
      // Distinguish between DESER channel A (even DAQ channels) and B (odd DAQ channels)
      // and shift the signal registers accordingly:
      if(channel%2 != 0) signal += (PROBE_B_HEADER - PROBE_A_HEADER);

      // Divide channel count by two, since one DESER400 holds two DAQ channels:
      if(probe.compare("d1") == 0) { _hal->SignalProbeDeserD1(channel/2, signal); return true; }
      else if(probe.compare("d2") == 0) { _hal->SignalProbeDeserD2(channel/2, signal); return true; }
    }
    else {
      // Select the correct probe for the output:
      if(probe.compare("d1") == 0) { _hal->SignalProbeD1(signal); return true; }
      else if(probe.compare("d2") == 0) {  _hal->SignalProbeD2(signal); return true; }
    }
  }
  // Analog signal probes:
  else if(probe.compare(0,1,"a") == 0) {

    // And get the register value from the dictionary object:
    uint8_t signal = _dict->getSignal(name, PROBE_ANALOG);
    LOG(logDEBUGAPI) << "Analog probe signal lookup for \"" << name
		     << "\" returned signal: " << static_cast<int>(signal);

    // Select the correct probe for the output:
    if(probe.compare("a1") == 0) {
      _hal->SignalProbeA1(signal);
      return true;
    }
    else if(probe.compare("a2") == 0) {
      _hal->SignalProbeA2(signal);
      return true;
    }
    else if (probe.compare("adc") == 0) {
       _hal->SignalProbeADC(signal, 0);
      return true;
    }
  }

  LOG(logERROR) << "Invalid probe name \"" << probe << "\" selected!";
  return false;
}



std::vector<uint16_t> pxarCore::daqADC(std::string signalName, uint8_t gain, uint16_t nSample, uint8_t source, uint8_t start){

  std::vector<uint16_t> data;
  if(!_hal->status()) {return data;}

  ProbeDictionary * _dict = ProbeDictionary::getInstance();
  std::transform(signalName.begin(), signalName.end(), signalName.begin(), ::tolower);
  uint8_t signal = _dict->getSignal(signalName, PROBE_ANALOG);

  data = _hal->daqADC(signal, gain, nSample, source, start);
  return data;
}

statistics pxarCore::getStatistics() {
  LOG(logDEBUG) << "Fetched DAQ statistics. Counters are being reset now.";
  // Return the accumulated number of decoding errors:
  return _hal->daqStatistics();
}


// TEST functions

bool pxarCore::setDAC(std::string dacName, uint8_t dacValue, uint8_t rocID) {

  if(!status()) {return false;}

  // Get the register number and check the range from dictionary:
  uint8_t dacRegister;
  if(!verifyRegister(dacName, dacRegister, dacValue, ROC_REG)) return false;

  std::pair<std::map<uint8_t,uint8_t>::iterator,bool> ret;
  std::vector<rocConfig>::iterator rocit;
  for (rocit = _dut->roc.begin(); rocit != _dut->roc.end(); ++rocit) {

    // Set the DAC only in the given ROC (even if that is disabled!)
    // WE ARE NOT USING the I2C address to identify the ROC currently:
    //if(rocit->i2c_address == rocI2C) {
    // But its ROC ID being just counted up from the first:
    if(static_cast<int>(rocit - _dut->roc.begin()) == rocID) {

      // Update the DUT DAC Value:
      ret = rocit->dacs.insert(std::make_pair(dacRegister,dacValue));
      if(ret.second == true) {
	LOG(logWARNING) << "DAC \"" << dacName << "\" was not initialized. Created with value " << static_cast<int>(dacValue);
      }
      else {
	rocit->dacs[dacRegister] = dacValue;
	LOG(logDEBUGAPI) << "DAC \"" << dacName << "\" updated with value " << static_cast<int>(dacValue);
      }

      _hal->rocSetDAC(rocit->i2c_address,dacRegister,dacValue);
      break;
    }
  }

  // We might not have found this ROC:
  if(rocit == _dut->roc.end()) {
    LOG(logERROR) << "ROC@I2C " << static_cast<int>(rocID) << " does not exist in the DUT!";
    return false;
  }

  return true;
}

bool pxarCore::setDAC(std::string dacName, uint8_t dacValue) {

  if(!status()) {return false;}

  // Get the register number and check the range from dictionary:
  uint8_t dacRegister;
  if(!verifyRegister(dacName, dacRegister, dacValue, ROC_REG)) return false;

  std::pair<std::map<uint8_t,uint8_t>::iterator,bool> ret;
  // Set the DAC for all active ROCs:
  for (std::vector<rocConfig>::iterator rocit = _dut->roc.begin(); rocit != _dut->roc.end(); ++rocit) {

    // Check if this ROC is marked active:
    if(!rocit->enable()) { continue; }

    // Update the DUT DAC Value:
    ret = rocit->dacs.insert(std::make_pair(dacRegister,dacValue));
    if(ret.second == true) {
      LOG(logWARNING) << "DAC \"" << dacName << "\" was not initialized. Created with value " << static_cast<int>(dacValue);
    }
    else {
      rocit->dacs[dacRegister] = dacValue;
      LOG(logDEBUGAPI) << "DAC \"" << dacName << "\" updated with value " << static_cast<int>(dacValue);
    }

    _hal->rocSetDAC(rocit->i2c_address,dacRegister,dacValue);
  }

  return true;
}

void pxarCore::setVcalHighRange() {
  for (std::vector<rocConfig>::iterator rocit = _dut->roc.begin(); rocit != _dut->roc.end(); ++rocit) {
    setDAC("ctrlreg", (_dut->getDAC(rocit->i2c_address, "ctrlreg")) | 4, rocit->i2c_address );}
}

void pxarCore::setVcalLowRange() {
  for (std::vector<rocConfig>::iterator rocit = _dut->roc.begin(); rocit != _dut->roc.end(); ++rocit) {
    setDAC("ctrlreg", (_dut->getDAC(rocit->i2c_address, "ctrlreg")) & 0xfb, rocit->i2c_address);}
}

uint8_t pxarCore::getDACRange(std::string dacName) {

  // Get the register number and check the range from dictionary:
  uint8_t dacRegister;
  uint8_t val = 0;
  if(!verifyRegister(dacName, dacRegister, val, ROC_REG)) return 0;

  // Get singleton DAC dictionary object:
  RegisterDictionary * _dict = RegisterDictionary::getInstance();

  // Read register value limit:
  return _dict->getSize(dacRegister, ROC_REG);
}

bool pxarCore::setTbmReg(std::string regName, uint8_t regValue, uint8_t tbmid) {

  if(!status()) {return 0;}

  // Get the register number and check the range from dictionary:
  uint8_t _register;
  if(!verifyRegister(regName, _register, regValue, TBM_REG)) return false;

  std::pair<std::map<uint8_t,uint8_t>::iterator,bool> ret;
  if(_dut->tbm.size() > static_cast<size_t>(tbmid)) {
    // Set the register only in the given TBM (even if that is disabled!)

    // Update the DUT register Value:
    ret = _dut->tbm.at(tbmid).dacs.insert(std::make_pair(_register,regValue));
    if(ret.second == true) {
      LOG(logWARNING) << "Register \"" << regName << "\" (" << std::hex << static_cast<int>(_register) << std::dec << ") was not initialized. Created with value " << static_cast<int>(regValue);
    }
    else {
      _dut->tbm.at(tbmid).dacs[_register] = regValue;
      LOG(logDEBUGAPI) << "Register \"" << regName << "\" (" << std::hex << static_cast<int>(_register) << std::dec << ") updated with value " << static_cast<int>(regValue);
    }

    _hal->tbmSetReg(_dut->tbm.at(tbmid).hubid,_dut->tbm.at(tbmid).core | _register,regValue);
  }
  else {
    LOG(logERROR) << "TBM " << tbmid << " is not existing in the DUT!";
    return false;
  }
  return true;
}

bool pxarCore::setTbmReg(std::string regName, uint8_t regValue) {

  for(size_t tbms = 0; tbms < _dut->tbm.size(); ++tbms) {
    if(!setTbmReg(regName, regValue, tbms)) return false;
  }
  return true;
}

void pxarCore::selectTbmRDA(uint8_t tbmid) {
  if (tbmid < 2) {
    uint8_t hubid = _dut->getEnabledTbms().at(tbmid*2).hubid;
    setHubID(hubid);
    _hal->tbmSelectRDA(1 - tbmid); // FIXME: change mapping in firmware for better readability
  }
  else {
    LOG(logERROR) << "We don't have a TBM at RDA channel " << int(tbmid);
  }
}

void pxarCore::setHubID(uint8_t id) {
  // check if provided hubid is available
  std::vector<int> hubids;
  std::vector<tbmConfig> tbms = _dut->getEnabledTbms();
  for (unsigned int i = 0; i < tbms.size() / 2; i++) {
    hubids.push_back(tbms.at(i*2).hubid);
  }
  if (std::find(hubids.begin(), hubids.end(), id) != hubids.end()) {
    _hal->setHubId(id);
  }
  else {
    LOG(logERROR) << "This hubid does not exist in the dut: " << int(id);
  }
}

std::vector< std::pair<uint8_t, std::vector<pixel> > > pxarCore::getPulseheightVsDAC(std::string dacName, uint8_t dacMin, uint8_t dacMax, uint16_t flags, uint16_t nTriggers) {

  // No step size provided - scanning all DACs with step size 1:
  return getPulseheightVsDAC(dacName, 1, dacMin, dacMax, flags, nTriggers);
}

std::vector< std::pair<uint8_t, std::vector<pixel> > > pxarCore::getPulseheightVsDAC(std::string dacName, uint8_t dacStep, uint8_t dacMin, uint8_t dacMax, uint16_t flags, uint16_t nTriggers) {

  if(!status()) {return std::vector< std::pair<uint8_t, std::vector<pixel> > >();}

  // Check DAC range
  if(dacMin > dacMax) {
    // Swapping the range:
    LOG(logWARNING) << "Swapping upper and lower bound.";
    uint8_t temp = dacMin;
    dacMin = dacMax;
    dacMax = temp;
  }

  // Get the register number and check the range from dictionary:
  uint8_t dacRegister;
  if(!verifyRegister(dacName, dacRegister, dacMax, ROC_REG)) {
    return std::vector< std::pair<uint8_t, std::vector<pixel> > >();
  }

  // Setup the correct _hal calls for this test
  HalMemFnPixelSerial   pixelfn      = &hal::SingleRocOnePixelDacScan;
  HalMemFnPixelParallel multipixelfn = &hal::MultiRocOnePixelDacScan;
  HalMemFnRocSerial     rocfn        = &hal::SingleRocAllPixelsDacScan;
  HalMemFnRocParallel   multirocfn   = &hal::MultiRocAllPixelsDacScan;

  // We want the pulse height back from the Map function, no internal flag needed.

  // Load the test parameters into vector
  std::vector<int32_t> param;
  param.push_back(static_cast<int32_t>(dacRegister));
  param.push_back(static_cast<int32_t>(dacMin));
  param.push_back(static_cast<int32_t>(dacMax));
  param.push_back(static_cast<int32_t>(flags));
  param.push_back(static_cast<int32_t>(nTriggers));
  param.push_back(static_cast<int32_t>(dacStep));

  // check if the flags indicate that the user explicitly asks for serial execution of test:
  std::vector<Event> data = expandLoop(pixelfn, multipixelfn, rocfn, multirocfn, param, false, flags);
  // repack data into the expected return format
  std::vector< std::pair<uint8_t, std::vector<pixel> > > result = repackDacScanData(data,dacStep,dacMin,dacMax,flags);

  // Reset the original value for the scanned DAC:
  std::vector<rocConfig> enabledRocs = _dut->getEnabledRocs();
  for (std::vector<rocConfig>::iterator rocit = enabledRocs.begin(); rocit != enabledRocs.end(); ++rocit){
    uint8_t oldDacValue = _dut->getDAC(static_cast<size_t>(rocit - enabledRocs.begin()),dacName);
    LOG(logDEBUGAPI) << "Reset DAC \"" << dacName << "\" to original value " << static_cast<int>(oldDacValue);
    _hal->rocSetDAC(static_cast<uint8_t>(rocit - enabledRocs.begin()),dacRegister,oldDacValue);
  }

  return result;
}

std::vector< std::pair<uint8_t, std::vector<pixel> > > pxarCore::getEfficiencyVsDAC(std::string dacName, uint8_t dacMin, uint8_t dacMax, uint16_t flags, uint16_t nTriggers) {

  // No step size provided - scanning all DACs with step size 1:
  return getEfficiencyVsDAC(dacName, 1, dacMin, dacMax, flags, nTriggers);
}

std::vector< std::pair<uint8_t, std::vector<pixel> > > pxarCore::getEfficiencyVsDAC(std::string dacName, uint8_t dacStep, uint8_t dacMin, uint8_t dacMax, uint16_t flags, uint16_t nTriggers) {

  if(!status()) {return std::vector< std::pair<uint8_t, std::vector<pixel> > >();}

  // Check DAC range
  if(dacMin > dacMax) {
    // Swapping the range:
    LOG(logWARNING) << "Swapping upper and lower bound.";
    uint8_t temp = dacMin;
    dacMin = dacMax;
    dacMax = temp;
  }

  // Get the register number and check the range from dictionary:
  uint8_t dacRegister;
  if(!verifyRegister(dacName, dacRegister, dacMax, ROC_REG)) {
    return std::vector< std::pair<uint8_t, std::vector<pixel> > >();
  }

  // Setup the correct _hal calls for this test
  HalMemFnPixelSerial   pixelfn      = &hal::SingleRocOnePixelDacScan;
  HalMemFnPixelParallel multipixelfn = &hal::MultiRocOnePixelDacScan;
  HalMemFnRocSerial     rocfn        = &hal::SingleRocAllPixelsDacScan;
  HalMemFnRocParallel   multirocfn   = &hal::MultiRocAllPixelsDacScan;

  // Load the test parameters into vector
  std::vector<int32_t> param;
  param.push_back(static_cast<int32_t>(dacRegister));
  param.push_back(static_cast<int32_t>(dacMin));
  param.push_back(static_cast<int32_t>(dacMax));
  param.push_back(static_cast<int32_t>(flags));
  param.push_back(static_cast<int32_t>(nTriggers));
  param.push_back(static_cast<int32_t>(dacStep));

  // check if the flags indicate that the user explicitly asks for serial execution of test:
  std::vector<Event> data = expandLoop(pixelfn, multipixelfn, rocfn, multirocfn, param, true, flags);
  // repack data into the expected return format
  std::vector< std::pair<uint8_t, std::vector<pixel> > > result = repackDacScanData(data,dacStep,dacMin,dacMax,flags);

  // Reset the original value for the scanned DAC:
  std::vector<rocConfig> enabledRocs = _dut->getEnabledRocs();
  for (std::vector<rocConfig>::iterator rocit = enabledRocs.begin(); rocit != enabledRocs.end(); ++rocit){
    uint8_t oldDacValue = _dut->getDAC(static_cast<size_t>(rocit - enabledRocs.begin()),dacName);
    LOG(logDEBUGAPI) << "Reset DAC \"" << dacName << "\" to original value " << static_cast<int>(oldDacValue);
    _hal->rocSetDAC(static_cast<uint8_t>(rocit - enabledRocs.begin()),dacRegister,oldDacValue);
  }

  return result;
}

std::vector< std::pair<uint8_t, std::vector<pixel> > > pxarCore::getThresholdVsDAC(std::string dacName, std::string dac2name, uint8_t dac2min, uint8_t dac2max, uint16_t flags, uint16_t nTriggers) {
  // Get the full DAC range for scanning:
  uint8_t dac1min = 0;
  uint8_t dac1max = getDACRange(dacName);
  uint8_t dacStep = 1;
  return getThresholdVsDAC(dacName, dacStep, dac1min, dac1max, dac2name, dacStep, dac2min, dac2max, flags, nTriggers);
}

std::vector< std::pair<uint8_t, std::vector<pixel> > > pxarCore::getThresholdVsDAC(std::string dac1name, uint8_t dac1step, uint8_t dac1min, uint8_t dac1max, std::string dac2name, uint8_t dac2step, uint8_t dac2min, uint8_t dac2max, uint16_t flags, uint16_t nTriggers) {
  // No threshold level provided - set threshold to 50%:
  uint8_t threshold = 50;
  return getThresholdVsDAC(dac1name, dac1step, dac1min, dac1max, dac2name, dac2step, dac2min, dac2max, threshold, flags, nTriggers);
}

std::vector< std::pair<uint8_t, std::vector<pixel> > > pxarCore::getThresholdVsDAC(std::string dac1name, uint8_t dac1step, uint8_t dac1min, uint8_t dac1max, std::string dac2name, uint8_t dac2step, uint8_t dac2min, uint8_t dac2max, uint8_t threshold, uint16_t flags, uint16_t nTriggers) {

  if(!status()) {return std::vector< std::pair<uint8_t, std::vector<pixel> > >();}

  // Check DAC ranges
  if(dac1min > dac1max) {
    // Swapping the range:
    LOG(logWARNING) << "Swapping upper and lower bound.";
    uint8_t temp = dac1min;
    dac1min = dac1max;
    dac1max = temp;
  }
  if(dac2min > dac2max) {
    // Swapping the range:
    LOG(logWARNING) << "Swapping upper and lower bound.";
    uint8_t temp = dac2min;
    dac2min = dac2max;
    dac2max = temp;
  }

  // Get the register number and check the range from dictionary:
  uint8_t dac1register, dac2register;
  if(!verifyRegister(dac1name, dac1register, dac1max, ROC_REG)) {
    return std::vector< std::pair<uint8_t, std::vector<pixel> > >();
  }
  if(!verifyRegister(dac2name, dac2register, dac2max, ROC_REG)) {
    return std::vector< std::pair<uint8_t, std::vector<pixel> > >();
  }

  // Check the threshold percentage level provided:
  if(threshold == 0 || threshold > 100) {
    LOG(logCRITICAL) << "Threshold level of " << static_cast<int>(threshold) << "% is not possible!";
    return std::vector< std::pair<uint8_t, std::vector<pixel> > >();
  }

  // Setup the correct _hal calls for this test
  HalMemFnPixelSerial   pixelfn      = &hal::SingleRocOnePixelDacDacScan;
  HalMemFnPixelParallel multipixelfn = &hal::MultiRocOnePixelDacDacScan;
  // In Principle these functions exist, but they would take years to run and fill up the buffer
  HalMemFnRocSerial     rocfn        = NULL; // &hal::SingleRocAllPixelsDacDacScan;
  HalMemFnRocParallel   multirocfn   = NULL; // &hal::MultiRocAllPixelsDacDacScan;

  // Load the test parameters into vector
  std::vector<int32_t> param;
  param.push_back(static_cast<int32_t>(dac1register));
  param.push_back(static_cast<int32_t>(dac1min));
  param.push_back(static_cast<int32_t>(dac1max));
  param.push_back(static_cast<int32_t>(dac2register));
  param.push_back(static_cast<int32_t>(dac2min));
  param.push_back(static_cast<int32_t>(dac2max));
  param.push_back(static_cast<int32_t>(flags));
  param.push_back(static_cast<int32_t>(nTriggers));
  param.push_back(static_cast<int32_t>(dac1step));
  param.push_back(static_cast<int32_t>(dac2step));

  // check if the flags indicate that the user explicitly asks for serial execution of test:
  std::vector<Event> data = expandLoop(pixelfn, multipixelfn, rocfn, multirocfn, param, true, flags);
  // repack data into the expected return format
  std::vector< std::pair<uint8_t, std::vector<pixel> > > result = repackThresholdDacScanData(data,dac1step,dac1min,dac1max,dac2step,dac2min,dac2max,threshold,nTriggers,flags);

  // Reset the original value for the scanned DAC:
  std::vector<rocConfig> enabledRocs = _dut->getEnabledRocs();
  for (std::vector<rocConfig>::iterator rocit = enabledRocs.begin(); rocit != enabledRocs.end(); ++rocit){
    uint8_t oldDac1Value = _dut->getDAC(static_cast<size_t>(rocit - enabledRocs.begin()),dac1name);
    uint8_t oldDac2Value = _dut->getDAC(static_cast<size_t>(rocit - enabledRocs.begin()),dac2name);
    LOG(logDEBUGAPI) << "Reset DAC \"" << dac1name << "\" to original value " << static_cast<int>(oldDac1Value);
    LOG(logDEBUGAPI) << "Reset DAC \"" << dac2name << "\" to original value " << static_cast<int>(oldDac2Value);
    _hal->rocSetDAC(static_cast<uint8_t>(rocit - enabledRocs.begin()),dac1register,oldDac1Value);
    _hal->rocSetDAC(static_cast<uint8_t>(rocit - enabledRocs.begin()),dac2register,oldDac2Value);
  }

  return result;
}


std::vector< std::pair<uint8_t, std::pair<uint8_t, std::vector<pixel> > > > pxarCore::getPulseheightVsDACDAC(std::string dac1name, uint8_t dac1min, uint8_t dac1max, std::string dac2name, uint8_t dac2min, uint8_t dac2max, uint16_t flags, uint16_t nTriggers) {

  // No step size provided - scanning all DACs with step size 1:
  return getPulseheightVsDACDAC(dac1name, 1, dac1min, dac1max, dac2name, 1, dac2min, dac2max, flags, nTriggers);
}

std::vector< std::pair<uint8_t, std::pair<uint8_t, std::vector<pixel> > > > pxarCore::getPulseheightVsDACDAC(std::string dac1name, uint8_t dac1step, uint8_t dac1min, uint8_t dac1max, std::string dac2name, uint8_t dac2step, uint8_t dac2min, uint8_t dac2max, uint16_t flags, uint16_t nTriggers) {

  if(!status()) {return std::vector< std::pair<uint8_t, std::pair<uint8_t, std::vector<pixel> > > >();}

  // Check DAC ranges
  if(dac1min > dac1max) {
    // Swapping the range:
    LOG(logWARNING) << "Swapping upper and lower bound.";
    uint8_t temp = dac1min;
    dac1min = dac1max;
    dac1max = temp;
  }
  if(dac2min > dac2max) {
    // Swapping the range:
    LOG(logWARNING) << "Swapping upper and lower bound.";
    uint8_t temp = dac2min;
    dac2min = dac2max;
    dac2max = temp;
  }

  // Get the register number and check the range from dictionary:
  uint8_t dac1register, dac2register;
  if(!verifyRegister(dac1name, dac1register, dac1max, ROC_REG)) {
    return std::vector< std::pair<uint8_t, std::pair<uint8_t, std::vector<pixel> > > >();
  }
  if(!verifyRegister(dac2name, dac2register, dac2max, ROC_REG)) {
    return std::vector< std::pair<uint8_t, std::pair<uint8_t, std::vector<pixel> > > >();
  }

  // Setup the correct _hal calls for this test
  HalMemFnPixelSerial   pixelfn      = &hal::SingleRocOnePixelDacDacScan;
  HalMemFnPixelParallel multipixelfn = &hal::MultiRocOnePixelDacDacScan;
  HalMemFnRocSerial     rocfn        = &hal::SingleRocAllPixelsDacDacScan;
  HalMemFnRocParallel   multirocfn   = &hal::MultiRocAllPixelsDacDacScan;

  // Load the test parameters into vector
  std::vector<int32_t> param;
  param.push_back(static_cast<int32_t>(dac1register));
  param.push_back(static_cast<int32_t>(dac1min));
  param.push_back(static_cast<int32_t>(dac1max));
  param.push_back(static_cast<int32_t>(dac2register));
  param.push_back(static_cast<int32_t>(dac2min));
  param.push_back(static_cast<int32_t>(dac2max));
  param.push_back(static_cast<int32_t>(flags));
  param.push_back(static_cast<int32_t>(nTriggers));
  param.push_back(static_cast<int32_t>(dac1step));
  param.push_back(static_cast<int32_t>(dac2step));

  // check if the flags indicate that the user explicitly asks for serial execution of test:
  std::vector<Event> data = expandLoop(pixelfn, multipixelfn, rocfn, multirocfn, param, false, flags);
  // repack data into the expected return format
  std::vector< std::pair<uint8_t, std::pair<uint8_t, std::vector<pixel> > > > result = repackDacDacScanData(data,dac1step,dac1min,dac1max,dac2step,dac2min,dac2max,flags);

  // Reset the original value for the scanned DAC:
  std::vector<rocConfig> enabledRocs = _dut->getEnabledRocs();
  for (std::vector<rocConfig>::iterator rocit = enabledRocs.begin(); rocit != enabledRocs.end(); ++rocit){
    uint8_t oldDac1Value = _dut->getDAC(static_cast<size_t>(rocit - enabledRocs.begin()),dac1name);
    uint8_t oldDac2Value = _dut->getDAC(static_cast<size_t>(rocit - enabledRocs.begin()),dac2name);
    LOG(logDEBUGAPI) << "Reset DAC \"" << dac1name << "\" to original value " << static_cast<int>(oldDac1Value);
    LOG(logDEBUGAPI) << "Reset DAC \"" << dac2name << "\" to original value " << static_cast<int>(oldDac2Value);
    _hal->rocSetDAC(static_cast<uint8_t>(rocit - enabledRocs.begin()),dac1register,oldDac1Value);
    _hal->rocSetDAC(static_cast<uint8_t>(rocit - enabledRocs.begin()),dac2register,oldDac2Value);
  }

  return result;
}

std::vector< std::pair<uint8_t, std::pair<uint8_t, std::vector<pixel> > > > pxarCore::getEfficiencyVsDACDAC(std::string dac1name, uint8_t dac1min, uint8_t dac1max, std::string dac2name, uint8_t dac2min, uint8_t dac2max, uint16_t flags, uint16_t nTriggers) {

  // No step size provided - scanning all DACs with step size 1:
  return getEfficiencyVsDACDAC(dac1name, 1, dac1min, dac1max, dac2name, 1, dac2min, dac2max, flags, nTriggers);
}

std::vector< std::pair<uint8_t, std::pair<uint8_t, std::vector<pixel> > > > pxarCore::getEfficiencyVsDACDAC(std::string dac1name, uint8_t dac1step, uint8_t dac1min, uint8_t dac1max, std::string dac2name, uint8_t dac2step, uint8_t dac2min, uint8_t dac2max, uint16_t flags, uint16_t nTriggers) {

  if(!status()) {return std::vector< std::pair<uint8_t, std::pair<uint8_t, std::vector<pixel> > > >();}

  // Check DAC ranges
  if(dac1min > dac1max) {
    // Swapping the range:
    LOG(logWARNING) << "Swapping upper and lower bound.";
    uint8_t temp = dac1min;
    dac1min = dac1max;
    dac1max = temp;
  }
  if(dac2min > dac2max) {
    // Swapping the range:
    LOG(logWARNING) << "Swapping upper and lower bound.";
    uint8_t temp = dac2min;
    dac2min = dac2max;
    dac2max = temp;
  }

  // Get the register number and check the range from dictionary:
  uint8_t dac1register, dac2register;
  if(!verifyRegister(dac1name, dac1register, dac1max, ROC_REG)) {
    return std::vector< std::pair<uint8_t, std::pair<uint8_t, std::vector<pixel> > > >();
  }
  if(!verifyRegister(dac2name, dac2register, dac2max, ROC_REG)) {
    return std::vector< std::pair<uint8_t, std::pair<uint8_t, std::vector<pixel> > > >();
  }

  // Setup the correct _hal calls for this test
  HalMemFnPixelSerial   pixelfn      = &hal::SingleRocOnePixelDacDacScan;
  HalMemFnPixelParallel multipixelfn = &hal::MultiRocOnePixelDacDacScan;
  HalMemFnRocSerial     rocfn        = &hal::SingleRocAllPixelsDacDacScan;
  HalMemFnRocParallel   multirocfn   = &hal::MultiRocAllPixelsDacDacScan;

  // Load the test parameters into vector
  std::vector<int32_t> param;
  param.push_back(static_cast<int32_t>(dac1register));
  param.push_back(static_cast<int32_t>(dac1min));
  param.push_back(static_cast<int32_t>(dac1max));
  param.push_back(static_cast<int32_t>(dac2register));
  param.push_back(static_cast<int32_t>(dac2min));
  param.push_back(static_cast<int32_t>(dac2max));
  param.push_back(static_cast<int32_t>(flags));
  param.push_back(static_cast<int32_t>(nTriggers));
  param.push_back(static_cast<int32_t>(dac1step));
  param.push_back(static_cast<int32_t>(dac2step));

  // check if the flags indicate that the user explicitly asks for serial execution of test:
  std::vector<Event> data = expandLoop(pixelfn, multipixelfn, rocfn, multirocfn, param, true, flags);
  // repack data into the expected return format
  std::vector< std::pair<uint8_t, std::pair<uint8_t, std::vector<pixel> > > > result = repackDacDacScanData(data,dac1step,dac1min,dac1max,dac2step,dac2min,dac2max,flags);

  // Reset the original value for the scanned DAC:
  std::vector<rocConfig> enabledRocs = _dut->getEnabledRocs();
  for (std::vector<rocConfig>::iterator rocit = enabledRocs.begin(); rocit != enabledRocs.end(); ++rocit){
    uint8_t oldDac1Value = _dut->getDAC(static_cast<size_t>(rocit - enabledRocs.begin()),dac1name);
    uint8_t oldDac2Value = _dut->getDAC(static_cast<size_t>(rocit - enabledRocs.begin()),dac2name);
    LOG(logDEBUGAPI) << "Reset DAC \"" << dac1name << "\" to original value " << static_cast<int>(oldDac1Value);
    LOG(logDEBUGAPI) << "Reset DAC \"" << dac2name << "\" to original value " << static_cast<int>(oldDac2Value);
    _hal->rocSetDAC(static_cast<uint8_t>(rocit - enabledRocs.begin()),dac1register,oldDac1Value);
    _hal->rocSetDAC(static_cast<uint8_t>(rocit - enabledRocs.begin()),dac2register,oldDac2Value);
  }

  return result;
}

std::vector<pixel> pxarCore::getPulseheightMap(uint16_t flags, uint16_t nTriggers) {

  if(!status()) {return std::vector<pixel>();}

  // Setup the correct _hal calls for this test
  HalMemFnPixelSerial   pixelfn      = &hal::SingleRocOnePixelCalibrate;
  HalMemFnPixelParallel multipixelfn = &hal::MultiRocOnePixelCalibrate;
  HalMemFnRocSerial     rocfn        = &hal::SingleRocAllPixelsCalibrate;
  HalMemFnRocParallel   multirocfn   = &hal::MultiRocAllPixelsCalibrate;

  // Load the test parameters into vector
  std::vector<int32_t> param;
  param.push_back(static_cast<int32_t>(flags));
  param.push_back(static_cast<int32_t>(nTriggers));

  // check if the flags indicate that the user explicitly asks for serial execution of test:
  std::vector<Event> data = expandLoop(pixelfn, multipixelfn, rocfn, multirocfn, param, false, flags);

  // Repacking of all data segments into one long map vector:
  std::vector<pixel> result = repackMapData(data, flags);

  return result;
}

std::vector<pixel> pxarCore::getEfficiencyMap(uint16_t flags, uint16_t nTriggers) {

  if(!status()) {return std::vector<pixel>();}

  // Setup the correct _hal calls for this test
  HalMemFnPixelSerial   pixelfn      = &hal::SingleRocOnePixelCalibrate;
  HalMemFnPixelParallel multipixelfn = &hal::MultiRocOnePixelCalibrate;
  HalMemFnRocSerial     rocfn        = &hal::SingleRocAllPixelsCalibrate;
  HalMemFnRocParallel   multirocfn   = &hal::MultiRocAllPixelsCalibrate;

  // Load the test parameters into vector
  std::vector<int32_t> param;
  param.push_back(static_cast<int32_t>(flags));
  param.push_back(static_cast<int32_t>(nTriggers));

  // check if the flags indicate that the user explicitly asks for serial execution of test:
  std::vector<Event> data = expandLoop(pixelfn, multipixelfn, rocfn, multirocfn, param, true, flags);

  // Repacking of all data segments into one long map vector:
  std::vector<pixel> result = repackMapData(data, flags);

  return result;
}

std::vector<pixel> pxarCore::getThresholdMap(std::string dacName, uint16_t flags, uint16_t nTriggers) {
  // Get the full DAC range for scanning:
  uint8_t dacMin = 0;
  uint8_t dacMax = getDACRange(dacName);
  uint8_t dacStep = 1;
  return getThresholdMap(dacName, dacStep, dacMin, dacMax, flags, nTriggers);
}

std::vector<pixel> pxarCore::getThresholdMap(std::string dacName, uint8_t dacStep, uint8_t dacMin, uint8_t dacMax, uint16_t flags, uint16_t nTriggers) {
  // No threshold level provided - set threshold to 50%:
  uint8_t threshold = 50;
  return getThresholdMap(dacName, dacStep, dacMin, dacMax, threshold, flags, nTriggers);
}

std::vector<pixel> pxarCore::getThresholdMap(std::string dacName, uint8_t dacStep, uint8_t dacMin, uint8_t dacMax, uint8_t threshold, uint16_t flags, uint16_t nTriggers) {

  if(!status()) {return std::vector<pixel>();}

  // Scan the maximum DAC range for threshold:
  uint8_t dacRegister;
  if(!verifyRegister(dacName, dacRegister, dacMax, ROC_REG)) {
    return std::vector<pixel>();
  }

  // Check the threshold percentage level provided:
  if(threshold == 0 || threshold > 100) {
    LOG(logCRITICAL) << "Threshold level of " << static_cast<int>(threshold) << "% is not possible!";
    return std::vector<pixel>();
  }

  // Setup the correct _hal calls for this test, a threshold map is a 1D dac scan:
  HalMemFnPixelSerial   pixelfn      = &hal::SingleRocOnePixelDacScan;
  HalMemFnPixelParallel multipixelfn = &hal::MultiRocOnePixelDacScan;
  HalMemFnRocSerial     rocfn        = &hal::SingleRocAllPixelsDacScan;
  HalMemFnRocParallel   multirocfn   = &hal::MultiRocAllPixelsDacScan;

  // Load the test parameters into vector
  std::vector<int32_t> param;
  param.push_back(static_cast<int32_t>(dacRegister));
  param.push_back(static_cast<int32_t>(dacMin));
  param.push_back(static_cast<int32_t>(dacMax));
  param.push_back(static_cast<int32_t>(flags));
  param.push_back(static_cast<int32_t>(nTriggers));
  param.push_back(static_cast<int32_t>(dacStep));

  // check if the flags indicate that the user explicitly asks for serial execution of test:
  std::vector<Event> data = expandLoop(pixelfn, multipixelfn, rocfn, multirocfn, param, true, flags);

  // Repacking of all data segments into one long map vector:
  std::vector<pixel> result = repackThresholdMapData(data, dacStep, dacMin, dacMax, threshold, nTriggers, flags);

  return result;
}

std::vector<std::vector<uint16_t> > pxarCore::daqGetReadback() {

  std::vector<std::vector<uint16_t> > values;
  if(!status()) { return values; }

  values = _hal->daqReadback();
  LOG(logDEBUGAPI) << "Decoders provided readback values for " << values.size() << " ROCs.";
  return values;
}

std::vector<uint8_t> pxarCore::daqGetXORsum(uint8_t channel) {

  std::vector<uint8_t> values;
  if(!status() || channel >= DTB_DAQ_CHANNELS) { return values; }

  values = _hal->daqXORsum(channel);
  LOG(logDEBUGAPI) << "Decoder channel " << static_cast<int>(channel) << " provided " << values.size() << " XOR sum values.";
  return values;
}


// DAQ functions

bool pxarCore::daqStart() {
  return daqStart(0,_daq_buffersize,true);
}

bool pxarCore::daqStart(const uint16_t flags) {
  return daqStart(flags,_daq_buffersize,true);
}

bool pxarCore::daqStart(const int buffersize, const bool init) {
  return daqStart(0, buffersize, init);
}

bool pxarCore::daqStart(const uint16_t flags, const int buffersize, const bool init) {

  if(!status()) {return false;}
  if(daqStatus()) {return false;}

  LOG(logDEBUGAPI) << "Requested to start DAQ with flags: " << listFlags(flags);

  // Clearing previously initialized DAQ sessions:
  _hal->daqClear();

  // Check requested buffer size:
  if(buffersize > DTB_SOURCE_BUFFER_SIZE) {
    LOG(logWARNING) << "Requested buffer size too large, setting to max. " \
		    << DTB_SOURCE_BUFFER_SIZE;
    _daq_buffersize = DTB_SOURCE_BUFFER_SIZE;
  }
  else { _daq_buffersize = buffersize; }


  LOG(logDEBUGAPI) << "Starting new DAQ session...";

  // Check if we want to program the DUT or just leave it:
  if(init) {
    // Attaching all columns to the readout:
    for (std::vector<rocConfig>::iterator rocit = _dut->roc.begin(); rocit != _dut->roc.end(); ++rocit) {
      _hal->AllColumnsSetEnable(rocit->i2c_address,true);
    }

    // Setup the configured mask and trim state of the DUT:
    MaskAndTrim(true);

    // Set Calibrate bits in the PUCs (we use the testrange for that):
    SetCalibrateBits(true);

  }
  else if(!_daq_startstop_warning){
    LOG(logWARNING) << "Not unmasking DUT, not setting Calibrate bits!";
    _daq_startstop_warning = true;
  }

  // Now run over all existing ROCs and program an unphysical pixel
  LOG(logDEBUG) << "programming unphysical pixel on all rocs in pxarCore::daqStart";
  for (std::vector<rocConfig>::iterator rocit = _dut->roc.begin(); rocit != _dut->roc.end(); ++rocit) {
    _hal->RocUnphysicalPixel(rocit->i2c_address);
  }


  // And start the DAQ session:
  _hal->daqStart(flags, _dut->sig_delays[SIG_DESER160PHASE],buffersize);

  // Activate the selected trigger source
  _hal->daqTriggerSource(_dut->trigger_source);

  _daq_running = true;
  return true;
}

bool pxarCore::daqSingleSignal(std::string triggerSignal) {

  // We do NOT require a running DAQ session here!

  // Get singleton Trigger dictionary object:
  PatternDictionary * _dict = PatternDictionary::getInstance();

  // Convert the trigger source name to lower case for comparison:
  std::transform(triggerSignal.begin(), triggerSignal.end(), triggerSignal.begin(), ::tolower);

  // Get the signal from the dictionary object:
  uint16_t sig = _dict->getSignal(triggerSignal,PATTERN_TRG);
  if(sig == PATTERN_ERR) {
    LOG(logCRITICAL) << "Could not find trigger signal \"" << triggerSignal << "\" in the dictionary!";
    throw InvalidConfig("Wrong trigger signal provided.");
  }

  LOG(logDEBUGAPI) << "Found TRG signal " << triggerSignal << " (" << std::hex << sig << std::dec << ")";
  _hal->daqTriggerSingleSignal(static_cast<uint8_t>(sig));
  return true;
}


std::vector<rawEvent> pxarCore::Deser160PhaseScan(int Ntrig) {
   return _hal->Deser160PhaseScan(Ntrig);
}


bool pxarCore::daqTriggerSource(std::string triggerSource, uint32_t timing) {

  // Get singleton Trigger dictionary object:
  TriggerDictionary * _dict = TriggerDictionary::getInstance();

  // Convert the trigger source name to lower case for comparison:
  std::transform(triggerSource.begin(), triggerSource.end(), triggerSource.begin(), ::tolower);

  std::istringstream identifiers(triggerSource);
  std::string s;
  uint16_t signal = 0;
  // Tokenize the signal string into single trigger sources, separated by ";":
  while (std::getline(identifiers, s, ';')) {
    // Get the signal from the dictionary object:
    uint16_t sig = _dict->getSignal(s);
    if(sig != TRG_ERR) {
      LOG(logDEBUGAPI) << "Trigger Source Identifier " << s << ": " << sig << " (0x" << std::hex << sig << std::dec << ")";

      // If we are using the DTB generator, also set the rate/period:
      if(sig == TRG_SEL_GEN || sig == TRG_SEL_GEN_DIR) {

        if(s.compare(0,6,"random") == 0) {
          // Be gentle and convert to centi-Hertz for the DTB :)
          uint32_t rate = int(timing/40e6*4294967296 + 0.5);
          // FIXME better also take the user input as BC instead of Hz, reduces confusion...
          LOG(logDEBUGAPI) << "Setting random trigger generator, rate = " << rate << " cHz";
          _hal->daqTriggerGenRandom(rate);
        }
        else if(s.compare(0,6,"period") == 0) {
          LOG(logDEBUGAPI) << "Setting periodic trigger generator, period = " << timing << " BC";
          _hal->daqTriggerGenPeriodic(timing);
        }
      }
      else if(sig == TRG_SEL_ASYNC_PG)  {
          LOG(logDEBUGAPI) << "Setting externally triggered Pattern Generator";
          _hal->daqTriggerPgExtern();
          sig = TRG_SEL_PG_DIR;
      }

      // Logical or for all trigger sources
      signal |= sig;

    }
    else {
      LOG(logCRITICAL) << "Could not find trigger source identifier \"" << s << "\" in the dictionary!";
      throw InvalidConfig("Wrong trigger source identifier provided.");
    }
  }

  LOG(logDEBUGAPI) << "Selecting trigger source 0x" << std::hex << signal << std::dec;
  _dut->trigger_source = signal;

  // Check if we need to change the tbmtype for HAL:
  uint8_t newtype = 0x0;
  if(_dict->getEmulationState(signal)) {
    // If no TBM is configured in the DUT, we run a single ROC and everyting will be okay:
    if(_dut->getTbmType() == "") { _hal->setTBMType(TBM_EMU); newtype = TBM_EMU; }
    // FIXME: I don't know how the DTB behaves with a DESER400 request plus TBM emulation!
    else {
      throw InvalidConfig("Do not use SoftTBM (emulated) and DESER400 with real TBM together!");
    }
  }
  else {
    // If no TBM is configured in the DUT, we run a single ROC and everyting will be okay:
    if(_dut->getTbmType() == "") { _hal->setTBMType(TBM_NONE); newtype = TBM_NONE; }
    // TBM is programmed, pass type to HAL:
    else  { _hal->setTBMType(_dut->tbm.front().type); newtype = _dut->tbm.front().type; }
  }

  // Get singleton Trigger dictionary object:
  DeviceDictionary * _devdict = DeviceDictionary::getInstance();
  LOG(logDEBUGAPI) << "Updated TBM type to \"" << _devdict->getName(newtype) << "\".";
  return true;
}

bool pxarCore::daqStatus()
{

  uint8_t perFull;

  return daqStatus(perFull);

}

bool pxarCore::daqStatus(uint8_t & perFull) {

  // Check if a DAQ session is running:
  if(!_daq_running) {
    LOG(logDEBUGAPI) << "DAQ not running!";
    return false;
  }

  // Check if we still have enough buffer memory left (with some safety margin).
  // Only filling buffer up to 90% in order not to lose data.
  uint32_t filled_buffer = _hal->daqBufferStatus();
  perFull = static_cast<uint8_t>(static_cast<float>(filled_buffer)/_daq_buffersize*100.0);
  if(filled_buffer > 0.9*_daq_buffersize) {
    LOG(logWARNING) << "DAQ buffer about to overflow, buffer size " << filled_buffer
		    << "/" << _daq_buffersize;
    return false;
  }

  LOG(logDEBUGAPI) << "Everything alright, buffer size " << filled_buffer
		   << "/" << _daq_buffersize;
  return true;
}

uint16_t pxarCore::daqTrigger(uint32_t nTrig, uint16_t period) {

  if(!daqStatus()) { return 0; }
  uint16_t inputperiod=period;
  // Pattern Generator loop doesn't work for delay periods smaller than
  // the pattern generator duration, so limit it to that:
  if(period < _dut->pg_sum) {
    period = _dut->pg_sum;
    LOG(logWARNING) << "Loop period setting (" << inputperiod << ") too small for configured "
		    << "Pattern generator. "
		    << "Forcing loop delay to " << period << " clk";
    LOG(logWARNING) << "To suppress this warning supply a larger delay setting";
  }
  // Just passing the call to the HAL, not doing anything else here:
  _hal->daqTrigger(nTrig,period);
  return period;
}

uint16_t pxarCore::daqTriggerLoop(uint16_t period) {

  if(!daqStatus()) { return 0; }
  uint16_t inputperiod=period;
  // Pattern Generator loop doesn't work for delay periods smaller than
  // the pattern generator duration, so limit it to that:
  if(period < _dut->pg_sum) {
    period = _dut->pg_sum;
    LOG(logWARNING) << "Loop period setting (" << inputperiod << ") too small for configured "
		    << "Pattern generator. "
		    << "Forcing loop delay to " << period << " clk";
    LOG(logWARNING) << "To suppress this warning supply a larger delay setting";
  }
  _hal->daqTriggerLoop(period);
  LOG(logDEBUGAPI) << "Loop period set to " << period << " clk";
  return period;
}

void pxarCore::daqTriggerLoopHalt() {

  // Just halt the pattern generator loop:
  _hal->daqTriggerLoopHalt();
}

std::vector<uint16_t> pxarCore::daqGetBuffer() {

  // Reading out all data from the DTB and returning the raw blob.
  // The HAL function throws pxar::DataNoEvent if nothing to be
  // returned
  std::vector<uint16_t> buffer = _hal->daqBuffer();
  return buffer;
}

std::vector<rawEvent> pxarCore::daqGetRawEventBuffer() {

  // Reading out all data from the DTB and returning the raw blob.
  // Select the right readout channels depending on the number of TBMs
  // The HAL function throws pxar::DataNoEvent if nothing to be
  // returned
  return _hal->daqAllRawEvents();
}

std::vector<Event> pxarCore::daqGetEventBuffer() {

  // Reading out all data from the DTB and returning the decoded Event buffer.
  // Select the right readout channels depending on the number of TBMs
  // The HAL function throws pxar::DataNoEvent if nothing to be
  // returned
  return _hal->daqAllEvents();
}

Event pxarCore::daqGetEvent() {

  // Return the next decoded Event from the FIFO buffer.
  // The HAL function throws pxar::DataNoEvent if no event is available
  return _hal->daqEvent();
}

rawEvent pxarCore::daqGetRawEvent() {

  // Return the next raw data record from the FIFO buffer:
  // The HAL function throws pxar::DataNoEvent if no event is available
  return _hal->daqRawEvent();
}

bool pxarCore::daqStop() {
  return daqStop(true);
}

bool pxarCore::daqStop(const bool init) {

  if(!status()) {return false;}
  if(!_daq_running) {
    LOG(logINFO) << "No DAQ running, not executing daqStop command.";
    return false;
  }

  _daq_running = false;

  // Stop all active DAQ channels:
  _hal->daqStop();

  // If the init flag is set, mask and clear the DUT again:
  if(init) {
    // Mask all pixels in the device again:
    MaskAndTrim(false);

    // Reset all the Calibrate bits and signals:
    SetCalibrateBits(false);

    // Detaching all columns to the readout:
    for (std::vector<rocConfig>::iterator rocit = _dut->roc.begin(); rocit != _dut->roc.end(); ++rocit) {
      _hal->AllColumnsSetEnable(rocit->i2c_address,false);
    }
  }
  else if(!_daq_startstop_warning){
    LOG(logWARNING) << "Not unmasking DUT, not setting Calibrate bits!";
    _daq_startstop_warning = true;
  }

  return true;
}


std::vector<Event> pxarCore::expandLoop(HalMemFnPixelSerial pixelfn, HalMemFnPixelParallel multipixelfn, HalMemFnRocSerial rocfn, HalMemFnRocParallel multirocfn, std::vector<int32_t> param, bool efficiency, uint16_t flags) {

  // Ensure the pattern generator trigger is active:
  _hal->daqTriggerSource(TRG_SEL_PG_DIR);

  // pointer to vector to hold our data
  std::vector<Event> data = std::vector<Event>();

  // Start test timer:
  timer t;

  // Check if all pixels are configured the same way on all ROCs. If this is not the case, we need to run this in FLAG_FORCE_SERIAL mode:
  std::vector<uint8_t> enabledRocs = _dut->getEnabledRocIDs();
  for(std::vector<uint8_t>::iterator rc = enabledRocs.begin(); rc != enabledRocs.end(); ++rc) {
    // Compare the configuration of the first ROC with all others:
    if(!comparePixelConfiguration(_dut->getEnabledPixels(enabledRocs.at(0)),_dut->getEnabledPixels(*rc))) {
      flags |= FLAG_FORCE_SERIAL;
      LOG(logINFO) << "Not all ROCs have their pixels configured the same way. "
		   << "Running in FLAG_FORCE_SERIAL mode.";
      break;
    }
  }

  // Do the masking/unmasking&trimming for all ROCs first.
  // Unless we are running in FLAG_FORCE_UNMASKED mode, we need to transmit the new trim values to the NIOS core and mask the whole DUT:
  if((flags & FLAG_FORCE_UNMASKED) == 0) {
    MaskAndTrimNIOS();
    MaskAndTrim(false);
  }
  // If we run in FLAG_FORCE_SERIAL mode, mask the whole DUT:
  else if((flags & FLAG_FORCE_SERIAL) != 0) { MaskAndTrim(false); }
  // Else just trim all the pixels:
  else { MaskAndTrim(true); }

  // Now run over all existing ROCs and program an unphysical pixel
  LOG(logDEBUG) << "programming unphysical pixel on all rocs in pxarCore::expandLoop";
  for (std::vector<rocConfig>::iterator rocit = _dut->roc.begin(); rocit != _dut->roc.end(); ++rocit) {
    _hal->RocUnphysicalPixel(rocit->i2c_address);
  }


  // Check if we might use parallel routine on whole module: more than one ROC
  // must be enabled and parallel execution not disabled by user
  if ((_dut->getNEnabledRocs() > 1) && ((flags & FLAG_FORCE_SERIAL) == 0)) {

    // Get the I2C addresses for all enabled ROCs from the config:
    std::vector<uint8_t> rocs_i2c = _dut->getEnabledRocI2Caddr();

    // Check if all pixels are enabled:
    if (_dut->getAllPixelEnable() && multirocfn != NULL) {
      LOG(logDEBUGAPI) << "\"The Loop\" contains one call to \'multirocfn\'";

      // execute call to HAL layer routine
      data = CALL_MEMBER_FN(*_hal,multirocfn)(rocs_i2c, efficiency, param);
    } // ROCs parallel
    // Otherwise call the Pixel Parallel function several times:
    else if (multipixelfn != NULL) {

      // Get one of the enabled ROCs:
      std::vector<uint8_t> enabledRocs = _dut->getEnabledRocIDs();
      std::vector<Event> rocdata = std::vector<Event>();
      std::vector<pixelConfig> enabledPixels = _dut->getEnabledPixels(enabledRocs.front());

      LOG(logDEBUGAPI) << "\"The Loop\" contains "
		       << enabledPixels.size() << " calls to \'multipixelfn\'";

      for (std::vector<pixelConfig>::iterator px = enabledPixels.begin(); px != enabledPixels.end(); ++px) {
	// execute call to HAL layer routine and store data in buffer
	std::vector<Event> buffer = CALL_MEMBER_FN(*_hal,multipixelfn)(rocs_i2c, px->column(), px->row(), efficiency, param);

	// merge pixel data into roc data storage vector
	if (rocdata.empty()){
	  rocdata = buffer; // for first time call
	} else {
	  // Add buffer vector to the end of existing Event data:
	  rocdata.reserve(rocdata.size() + buffer.size());
	  rocdata.insert(rocdata.end(), buffer.begin(), buffer.end());
	}
      } // pixel loop
	// append rocdata to main data storage vector
      if (data.empty()) data = rocdata;
      else {
	data.reserve(data.size() + rocdata.size());
	data.insert(data.end(), rocdata.begin(), rocdata.end());
      }
    } // Pixels parallel
  } // Parallel functions

  // Either we only have one ROC enabled or we force serial test execution:
  else {

    // -> single ROC / ROC-by-ROC operation
    // check if all pixels are enabled
    // if so, use routine that accesses whole ROC
    if (_dut->getAllPixelEnable() && rocfn != NULL){

      // loop over all enabled ROCs
      std::vector<rocConfig> enabledRocs = _dut->getEnabledRocs();

      LOG(logDEBUGAPI) << "\"The Loop\" contains " << enabledRocs.size() << " calls to \'rocfn\'";

      for (std::vector<rocConfig>::iterator rocit = enabledRocs.begin(); rocit != enabledRocs.end(); ++rocit) {

	// If we have serial execution make sure to trim the ROC if we requested forceUnmasked:
	if(((flags & FLAG_FORCE_SERIAL) != 0) && ((flags & FLAG_FORCE_UNMASKED) != 0)) { MaskAndTrim(true,rocit); }

	// execute call to HAL layer routine and save returned data in buffer
	std::vector<Event> rocdata = CALL_MEMBER_FN(*_hal,rocfn)(rocit->i2c_address, efficiency, param);
	// append rocdata to main data storage vector
        if (data.empty()) data = rocdata;
	else {
	  data.reserve(data.size() + rocdata.size());
	  data.insert(data.end(), rocdata.begin(), rocdata.end());
	}
      } // roc loop
    }
    else if (pixelfn != NULL) {

      // -> we operate on single pixels
      // loop over all enabled ROCs
      std::vector<rocConfig> enabledRocs = _dut->getEnabledRocs();

      LOG(logDEBUGAPI) << "\"The Loop\" contains " << enabledRocs.size() << " enabled ROCs.";

      for (std::vector<rocConfig>::iterator rocit = enabledRocs.begin(); rocit != enabledRocs.end(); ++rocit){
	std::vector<Event> rocdata = std::vector<Event>();
	std::vector<pixelConfig> enabledPixels = _dut->getEnabledPixelsI2C(rocit->i2c_address);


	LOG(logDEBUGAPI) << "\"The Loop\" for the current ROC contains " \
			 << enabledPixels.size() << " calls to \'pixelfn\'";

	for (std::vector<pixelConfig>::iterator pixit = enabledPixels.begin(); pixit != enabledPixels.end(); ++pixit) {
	  // execute call to HAL layer routine and store data in buffer
	  std::vector<Event> buffer = CALL_MEMBER_FN(*_hal,pixelfn)(rocit->i2c_address, pixit->column(), pixit->row(), efficiency, param);
	  // merge pixel data into roc data storage vector
	  if (rocdata.empty()){
	    rocdata = buffer; // for first time call
	  } else {
	    // Add buffer vector to the end of existing Event data:
	    rocdata.reserve(rocdata.size() + buffer.size());
	    rocdata.insert(rocdata.end(), buffer.begin(), buffer.end());
	  }
	} // pixel loop
	// append rocdata to main data storage vector
        if (data.empty()) data = rocdata;
	else {
	  data.reserve(data.size() + rocdata.size());
	  data.insert(data.end(), rocdata.begin(), rocdata.end());
	}
      } // roc loop
    }// single pixel fnc
    else {
      LOG(logCRITICAL) << "LOOP EXPANSION FAILED -- NO MATCHING FUNCTION TO CALL?!";
      // do NOT throw an exception here: this is not a runtime problem
      // but can only be a bug in the code -> this could not be handled by unwinding the stack

      // Mask device, clear leftover calibrate signals:
      MaskAndTrim(false);
      SetCalibrateBits(false);
      return data;
    }
  } // single roc fnc

  // check that we ended up with data, otherwise print an error:
  if (data.empty()){ LOG(logCRITICAL) << "NO DATA FROM TEST FUNCTION -- are any TBMs/ROCs/PIXs enabled?!"; }

  // Test is over, mask the whole device again and clear leftover calibrate signals:
  MaskAndTrim(false);
  SetCalibrateBits(false);

  // Print timer value:
  LOG(logINFO) << "Test took " << t << "ms.";

  return data;
} // expandLoop()

std::vector<pixel> pxarCore::repackMapData(std::vector<Event> &data, uint16_t flags) {

  // Keep track of the pixel to be expected:
  uint8_t expected_column = 0, expected_row = 0;

  std::vector<pixel> result;
  LOG(logDEBUGAPI) << "Simple Map Repack of " << data.size() << " data blocks.";

  // Measure time:
  timer t;

  // Loop over all Events we have:
  for(std::vector<Event>::iterator Eventit = data.begin(); Eventit!= data.end(); ++Eventit) {

    // For every Event, loop over all contained pixels:
    for(std::vector<pixel>::iterator pixit = Eventit->pixels.begin(); pixit != Eventit->pixels.end(); ++pixit) {
      // Check for pulsed pixels being present:
      if((flags&FLAG_CHECK_ORDER) != 0) {
	if(pixit->column() != expected_column || pixit->row() != expected_row) {

	  // With the full chip unmasked we want to know if the pixel in question was amongst the ones recorded:
	  if((flags&FLAG_FORCE_UNMASKED) != 0) { LOG(logDEBUGPIPES) << "This is a background hit: " << (*pixit); }
	  else {
	    // With only the pixel in question unmasked we want to warn about other appeareances:
	    LOG(logERROR) << "This pixel doesn't belong here: " << (*pixit) << ". Expected [" << static_cast<int>(expected_column) << "," << static_cast<int>(expected_row) << ",x]";
	  }

	  // Convention: set a negative pixel value for out-of-order pixel hits:
	  pixit->setValue(-1*pixit->value());
	}
      }
      result.push_back(*pixit);
    } // loop over pixels

    if((flags&FLAG_CHECK_ORDER) != 0) {
      expected_row++;
      if(expected_row >= ROC_NUMROWS) { expected_row = 0; expected_column++; }
      if(expected_column >= ROC_NUMCOLS) { expected_row = 0; expected_column = 0; }
    }
  } // loop over Events

  // Sort the output map by ROC->col->row - just because we are so nice:
  if((flags&FLAG_NOSORT) == 0) { std::sort(result.begin(),result.end()); }

  // Cleanup temporary data:
  data.clear();

  LOG(logDEBUGAPI) << "Correctly repacked Map data for delivery.";
  LOG(logDEBUGAPI) << "Repacking took " << t << "ms.";
  return result;
}

std::vector< std::pair<uint8_t, std::vector<pixel> > > pxarCore::repackDacScanData (std::vector<Event> &data, uint8_t dacStep, uint8_t dacMin, uint8_t dacMax, uint16_t flags){

  // Keep track of the pixel to be expected:
  uint8_t expected_column = 0, expected_row = 0;

  std::vector< std::pair<uint8_t, std::vector<pixel> > > result;

  // Measure time:
  timer t;

  if(data.size() % static_cast<size_t>((dacMax-dacMin)/dacStep+1) != 0) {
    LOG(logCRITICAL) << "Data size not as expected! " << data.size() << " data blocks do not fit to " << static_cast<int>((dacMax-dacMin)/dacStep+1) << " DAC values!";
    return result;
  }

  LOG(logDEBUGAPI) << "Packing DAC range " << static_cast<int>(dacMin) << " - " << static_cast<int>(dacMax) << " (step size " << static_cast<int>(dacStep) << "), data has " << data.size() << " entries.";

  // Prepare the result vector
  for(size_t dac = dacMin; dac <= dacMax; dac += dacStep) { result.push_back(std::make_pair(dac,std::vector<pixel>())); }

  size_t currentDAC = dacMin;
  // Loop over the packed data and separate into DAC ranges, potentially several rounds:
  for(std::vector<Event>::iterator Eventit = data.begin(); Eventit!= data.end(); ++Eventit) {

    if(currentDAC > dacMax) { currentDAC = dacMin; }

    // For every Event, loop over all contained pixels:
    for(std::vector<pixel>::iterator pixit = Eventit->pixels.begin(); pixit != Eventit->pixels.end(); ++pixit) {
      // Check for pulsed pixels being present:
      if((flags&FLAG_CHECK_ORDER) != 0) {
	if(pixit->column() != expected_column || pixit->row() != expected_row) {

	  // With the full chip unmasked we want to know if the pixel in question was amongst the ones recorded:
	  if((flags&FLAG_FORCE_UNMASKED) != 0) { LOG(logDEBUGPIPES) << "This is a background hit: " << (*pixit); }
	  else {
	    // With only the pixel in question unmasked we want to warn about other appeareances:
	    LOG(logERROR) << "This pixel doesn't belong here: " << (*pixit) << ". Expected [" << static_cast<int>(expected_column) << "," << static_cast<int>(expected_row) << ",x]";
	  }

	  // Convention: set a negative pixel value for out-of-order pixel hits:
	  pixit->setValue(-1*pixit->value());
	}
      }

      // Add the pixel to the list:
      result.at((currentDAC-dacMin)/dacStep).second.push_back(*pixit);

    } // loop over all pixels

    // Advance the expected pixel address if we reached the upper DAC scan boundary:
    if((flags&FLAG_CHECK_ORDER) != 0 && currentDAC == dacMax) {
      expected_row++;
      if(expected_row >= ROC_NUMROWS) { expected_row = 0; expected_column++; }
      if(expected_column >= ROC_NUMCOLS) { expected_row = 0; expected_column = 0; }
    }

    // Move to next DAC setting:
    currentDAC += dacStep;

  } // loop over events

  // Cleanup temporary data:
  data.clear();

  LOG(logDEBUGAPI) << "Correctly repacked DacScan data for delivery.";
  LOG(logDEBUGAPI) << "Repacking took " << t << "ms.";
  return result;
}

std::vector<pixel> pxarCore::repackThresholdMapData (std::vector<Event> &data, uint8_t dacStep, uint8_t dacMin, uint8_t dacMax, uint8_t thresholdlevel, uint16_t nTriggers, uint16_t flags) {

  std::vector<pixel> result;
  // Vector of pixels for which a threshold has already been found
  std::vector<pixel> found;

  // Threshold is the the given efficiency level "thresholdlevel"
  // Using ceiling function to take higher threshold when in doubt.
  uint16_t threshold = static_cast<uint16_t>(ceil(static_cast<float>(nTriggers)*thresholdlevel/100));
  LOG(logDEBUGAPI) << "Scanning for threshold level " << threshold << ", "
		   << ((flags&FLAG_RISING_EDGE) == 0 ? "falling":"rising") << " edge";

  // Measure time:
  timer t;

  // First, pack the data as it would be a regular Dac Scan:
  std::vector<std::pair<uint8_t,std::vector<pixel> > > packed_dac = repackDacScanData(data, dacStep, dacMin, dacMax, flags);

  // Efficiency map:
  std::map<pixel,uint8_t> oldvalue;

  // Then loop over all pixels and DAC settings, start from the back if we are looking for falling edge.
  // This ensures that we end up having the correct edge, even if the efficiency suddenly changes from 0 to max.
  std::vector<std::pair<uint8_t,std::vector<pixel> > >::iterator it_start;
  std::vector<std::pair<uint8_t,std::vector<pixel> > >::iterator it_end;
  int increase_op;
  if((flags&FLAG_RISING_EDGE) != 0) { it_start = packed_dac.begin(); it_end = packed_dac.end(); increase_op = 1; }
  else { it_start = packed_dac.end()-1; it_end = packed_dac.begin()-1; increase_op = -1;  }

  for(std::vector<std::pair<uint8_t,std::vector<pixel> > >::iterator it = it_start; it != it_end; it += increase_op) {
    // For every DAC value, loop over all pixels:
    for(std::vector<pixel>::iterator pixit = it->second.begin(); pixit != it->second.end(); ++pixit) {
      // Check if for this pixel a threshold has been found already and we can skip the rest:
      std::vector<pixel>::iterator px_found = std::find_if(found.begin(),
							   found.end(),
							   findPixelXY(pixit->column(), pixit->row(), pixit->roc()));
      if(px_found != found.end()) continue;

      // Check if we have that particular pixel already in the result vector:
      std::vector<pixel>::iterator px = std::find_if(result.begin(),
						     result.end(),
						     findPixelXY(pixit->column(), pixit->row(), pixit->roc()));

      // Pixel is known:
      if(px != result.end()) {
	// Calculate efficiency deltas and slope:
	uint8_t delta_old = abs(oldvalue[*px] - threshold);
	uint8_t delta_new = abs(static_cast<uint8_t>(pixit->value()) - threshold);
	bool positive_slope = (static_cast<uint8_t>(pixit->value()) - oldvalue[*px] > 0 ? true : false);

	// Check which value is closer to the threshold. Only if the slope is positive AND
	// the new delta between value and threshold is *larger* then the old delta, we
	// found the threshold. If slope is negative, we just have a ripple in the DAC's
	// distribution:
	if(positive_slope && !(delta_new < delta_old)) {
	  found.push_back(*pixit);
	  continue;
	}

	// No threshold found yet, update the DAC threshold value for the pixel:
	px->setValue(it->first);
	// Update the oldvalue map:
	oldvalue[*px] = static_cast<uint8_t>(pixit->value());
      }
      // Pixel is new, just adding it:
      else {
        // If the pixel is above threshold at first appearance, the respective
	// DAC value is set as its threshold:
	if(pixit->value() >= threshold) { found.push_back(*pixit); }

	// Store the pixel with original efficiency
	oldvalue.insert(std::make_pair(*pixit,pixit->value()));

	// Push pixel to result vector with current DAC as value field:
	pixit->setValue(it->first);
	result.push_back(*pixit);
      }
    }
  }

  // Check for pixels that have not reached the threshold at all:
  for(std::vector<pixel>::iterator px = result.begin(); px != result.end(); ++px) {
    std::vector<pixel>::iterator px_found = std::find_if(found.begin(),
							 found.end(),
							 findPixelXY(px->column(), px->row(), px->roc()));
    // The pixel is in the "found" vector, which means it crossed threshold at some point:
    if(px_found != found.end()) continue;

    // The pixel is not in and never reached the threshold. We set the return value to
    // "dacMax" (rising edge) or "dacMin" (falling edge):
    if((flags&FLAG_RISING_EDGE) != 0) { px->setValue(dacMax); }
    else { px->setValue(dacMin); }
    LOG(logWARNING) << "No threshold found for " << (*px);
  }

  // Sort the output map by ROC->col->row - just because we are so nice:
  if((flags&FLAG_NOSORT) == 0) { std::sort(result.begin(),result.end()); }

  LOG(logDEBUGAPI) << "Correctly repacked&analyzed ThresholdMap data for delivery.";
  LOG(logDEBUGAPI) << "Repacking took " << t << "ms.";
  return result;
}

std::vector<std::pair<uint8_t,std::vector<pixel> > > pxarCore::repackThresholdDacScanData (std::vector<Event> &data, uint8_t dac1step, uint8_t dac1min, uint8_t dac1max, uint8_t dac2step, uint8_t dac2min, uint8_t dac2max, uint8_t thresholdlevel, uint16_t nTriggers, uint16_t flags) {

  std::vector<std::pair<uint8_t,std::vector<pixel> > > result;
  // Map of pixels with already assigned threshold (key is the dac2 value):
  std::map<uint8_t,std::vector<pixel> > found;

  // Threshold is the the given efficiency level "thresholdlevel":
  // Using ceiling function to take higher threshold when in doubt.
  uint16_t threshold = static_cast<uint16_t>(ceil(static_cast<float>(nTriggers)*thresholdlevel/100));
  LOG(logDEBUGAPI) << "Scanning for threshold level " << threshold << ", "
		   << ((flags&FLAG_RISING_EDGE) == 0 ? "falling":"rising") << " edge";

  // Measure time:
  timer t;

  // First, pack the data as it would be a regular DacDac Scan:
  std::vector<std::pair<uint8_t,std::pair<uint8_t,std::vector<pixel> > > > packed_dacdac = repackDacDacScanData(data,dac1step,dac1min,dac1max,dac2step,dac2min,dac2max,flags);

  // Efficiency map:
  std::map<uint8_t,std::map<pixel,uint8_t> > oldvalue;

  // Then loop over all pixels and DAC settings, start from the back if we are looking for falling edge.
  // This ensures that we end up having the correct edge, even if the efficiency suddenly changes from 0 to max.
  std::vector<std::pair<uint8_t,std::pair<uint8_t,std::vector<pixel> > > >::iterator it_start;
  std::vector<std::pair<uint8_t,std::pair<uint8_t,std::vector<pixel> > > >::iterator it_end;
  int increase_op;
  if((flags&FLAG_RISING_EDGE) != 0) { it_start = packed_dacdac.begin(); it_end = packed_dacdac.end(); increase_op = 1; }
  else { it_start = packed_dacdac.end()-1; it_end = packed_dacdac.begin()-1; increase_op = -1;  }

  for(std::vector<std::pair<uint8_t,std::pair<uint8_t,std::vector<pixel> > > >::iterator it = it_start; it != it_end; it += increase_op) {

    // For every DAC/DAC entry, loop over all pixels:
    for(std::vector<pixel>::iterator pixit = it->second.second.begin(); pixit != it->second.second.end(); ++pixit) {

      // Find the current DAC2 value in the result vector (simple replace for find_if):
      std::vector<std::pair<uint8_t, std::vector<pixel> > >::iterator dac;
      for(dac = result.begin(); dac != result.end(); ++dac) { if(it->second.first == dac->first) break; }

      // Didn't find the DAC2 value:
      if(dac == result.end()) {
	result.push_back(std::make_pair(it->second.first,std::vector<pixel>()));
	dac = result.end() - 1;
	// Also add an entry for bookkeeping:
	found.insert(std::make_pair(it->second.first,std::vector<pixel>()));
	oldvalue.insert(std::make_pair(it->second.first,std::map<pixel,uint8_t>()));
      }

      // Check if for this pixel a threshold has been found already and we can skip the rest:
      std::vector<pixel>::iterator px_found = std::find_if(found[dac->first].begin(),
							   found[dac->first].end(),
							   findPixelXY(pixit->column(), pixit->row(), pixit->roc()));
      if(px_found != found[dac->first].end()) continue;

      // Check if we have that particular pixel already in:
      std::vector<pixel>::iterator px = std::find_if(dac->second.begin(),
						     dac->second.end(),
						     findPixelXY(pixit->column(), pixit->row(), pixit->roc()));

      // Pixel is known:
      if(px != dac->second.end()) {
	// Calculate efficiency deltas and slope:
	uint8_t delta_old = abs(oldvalue[dac->first][*px] - threshold);
	uint8_t delta_new = abs(static_cast<uint8_t>(pixit->value()) - threshold);
	bool positive_slope = (static_cast<uint8_t>(pixit->value()) - oldvalue[dac->first][*px] > 0 ? true : false);

        // Check which value is closer to the threshold. Only if the slope is positive AND
	// the new delta between value and threshold is *larger* then the old delta, we
	// found the threshold. If slope is negative, we just have a ripple in the DAC's
	// distribution:
	if(positive_slope && !(delta_new < delta_old)) {
	  found[dac->first].push_back(*pixit);
	  continue;
	}

        // No threshold found yet, update the DAC threshold value for the pixel:
	px->setValue(it->first);
	// Update the oldvalue map:
	oldvalue[dac->first][*px] = static_cast<uint8_t>(pixit->value());
      }
      // Pixel is new, just adding it:
      else {
        // If the pixel is above threshold at first appearance, the respective
	// DAC value is set as its threshold:
	if(pixit->value() >= threshold) { found[dac->first].push_back(*pixit); }

	// Store the pixel with original efficiency
	oldvalue[dac->first].insert(std::make_pair(*pixit,pixit->value()));
	// Push pixel to result vector with current DAC as value field:
	pixit->setValue(it->first);
	dac->second.push_back(*pixit);
      }
    }
  }

  // Check for pixels that have not reached the threshold at all:
  for(std::vector<std::pair<uint8_t,std::vector<pixel> > >::iterator dac = result.begin(); dac != result.end(); ++dac) {

    for(std::vector<pixel>::iterator px = dac->second.begin(); px != dac->second.end(); px++) {
      std::vector<pixel>::iterator px_found = std::find_if(found[dac->first].begin(),
							   found[dac->first].end(),
							   findPixelXY(px->column(), px->row(), px->roc()));
      // The pixel is in the "found" vector, which means it crossed threshold at some point:
      if(px_found != found[dac->first].end()) continue;

      // The pixel is not in and never reached the threshold. We set the return value to
      // "dacMax" (rising edge) or "dacMin" (falling edge):
      if((flags&FLAG_RISING_EDGE) != 0) { px->setValue(dac2max); }
      else { px->setValue(dac2min); }
      LOG(logWARNING) << "No threshold found for " << (*px) << " at DAC value " << static_cast<int>(dac->first);
    }
  }

  // Sort the output map by DAC values and ROC->col->row - just because we are so nice:
  if((flags&FLAG_NOSORT) == 0) { std::sort(result.begin(),result.end()); }

  LOG(logDEBUGAPI) << "Correctly repacked&analyzed ThresholdDacScan data for delivery.";
  LOG(logDEBUGAPI) << "Repacking took " << t << "ms.";
  return result;
}

std::vector< std::pair<uint8_t, std::pair<uint8_t, std::vector<pixel> > > > pxarCore::repackDacDacScanData (std::vector<Event> &data, uint8_t dac1step, uint8_t dac1min, uint8_t dac1max, uint8_t dac2step, uint8_t dac2min, uint8_t dac2max, uint16_t /*flags*/) {
  std::vector< std::pair<uint8_t, std::pair<uint8_t, std::vector<pixel> > > > result;

  // Measure time:
  timer t;

  if(data.size() % static_cast<size_t>(((dac1max-dac1min)/dac1step+1)*((dac2max-dac2min)/dac2step+1)) != 0) {
    LOG(logCRITICAL) << "Data size not as expected! " << data.size() << " data blocks do not fit to " << static_cast<int>(((dac1max-dac1min)/dac1step+1)*((dac2max-dac2min)/dac2step+1)) << " DAC values!";
    return result;
  }

  LOG(logDEBUGAPI) << "Packing DAC range [" << static_cast<int>(dac1min) << " - " << static_cast<int>(dac1max)
		   << ", step size " << static_cast<int>(dac1step) << "]x["
		   << static_cast<int>(dac2min) << " - " << static_cast<int>(dac2max)
		   << ", step size " << static_cast<int>(dac2step)
		   << "], data has " << data.size() << " entries.";

  // Prepare the result vector
  for(size_t dac1 = dac1min; dac1 <= dac1max; dac1 += dac1step) {
    std::pair<uint8_t,std::vector<pixel> > dacpair;
    for(size_t dac2 = dac2min; dac2 <= dac2max; dac2 += dac2step) {
      dacpair = std::make_pair(dac2,std::vector<pixel>());
      result.push_back(std::make_pair(dac1,dacpair));
    }
  }

  size_t current1dac = dac1min;
  size_t current2dac = dac2min;

  // Loop over the packed data and separeate into DAC ranges, potentially several rounds:
  int i = 0;
  for(std::vector<Event>::iterator Eventit = data.begin(); Eventit!= data.end(); ++Eventit) {
    if(current2dac > dac2max) {
      current2dac = dac2min;
      current1dac += dac1step;
    }
    if(current1dac > dac1max) { current1dac = dac1min; }

    result.at((current1dac-dac1min)/dac1step*((dac2max-dac2min)/dac2step+1) + (current2dac-dac2min)/dac2step).second.second.insert(result.at((current1dac-dac1min)/dac1step*((dac2max-dac2min)/dac2step+1) + (current2dac-dac2min)/dac2step).second.second.end(),
												       Eventit->pixels.begin(),
												       Eventit->pixels.end());
    i++;
    current2dac += dac2step;
  }

  // Cleanup temporary data:
  data.clear();

  LOG(logDEBUGAPI) << "Correctly repacked DacDacScan data for delivery.";
  LOG(logDEBUGAPI) << "Repacking took " << t << "ms.";
  return result;
}

// Update mask and trim bits for the full DUT in NIOS structs:
void pxarCore::MaskAndTrimNIOS() {

  // First transmit all configured I2C addresses:
  _hal->SetupI2CValues(_dut->getRocI2Caddr());

  // Now run over all existing ROCs and transmit the pixel trim/mask data:
  for (std::vector<rocConfig>::iterator rocit = _dut->roc.begin(); rocit != _dut->roc.end(); ++rocit) {
    _hal->SetupTrimValues(rocit->i2c_address,rocit->pixels);
  }
}

// Mask/Unmask and trim all ROCs:
void pxarCore::MaskAndTrim(bool trim) {
  // Run over all existing ROCs:
  for (std::vector<rocConfig>::iterator rocit = _dut->roc.begin(); rocit != _dut->roc.end(); ++rocit) {
    // If it's enabled, do the requested action:
    if(rocit->enable()) { MaskAndTrim(trim,rocit); }
    // Else mask it anyway: it's diabled.
    else { MaskAndTrim(false,rocit); }
  }
}

// Mask/Unmask and trim one ROC:
void pxarCore::MaskAndTrim(bool trim, std::vector<rocConfig>::iterator rocit) {

  // This ROC is supposed to be trimmed as configured, so let's trim it:
  if(trim) {
    LOG(logDEBUGAPI) << "ROC@I2C " << static_cast<int>(rocit->i2c_address) << " features "
		     << static_cast<int>(std::count_if(rocit->pixels.begin(),rocit->pixels.end(),configMaskSet(true)))
		     << " masked pixels.";
    LOG(logDEBUGAPI) << "Unmasking and trimming ROC@I2C " << static_cast<int>(rocit->i2c_address) << " in one go.";
    _hal->RocSetMask(rocit->i2c_address,false,rocit->pixels);
    return;
  }
  else {
    LOG(logDEBUGAPI) << "Masking ROC@I2C " << static_cast<int>(rocit->i2c_address) << " in one go.";
    _hal->RocSetMask(rocit->i2c_address,true);
    return;
  }
}

// Program the calibrate bits in ROC PUCs:
void pxarCore::SetCalibrateBits(bool enable) {

  // Run over all existing ROCs:
  for (std::vector<rocConfig>::iterator rocit = _dut->roc.begin(); rocit != _dut->roc.end(); ++rocit) {

    // Check if the signal has to be turned on or off:
    if(enable) {
      std::vector<pixelConfig> cal_pixels = _dut->getEnabledPixels(rocit - _dut->roc.begin());
      LOG(logDEBUGAPI) << "Configuring calibrate bits in " << cal_pixels.size() << " enabled PUCs of ROC@I2C "
		       << static_cast<int>(rocit->i2c_address);
      _hal->RocSetCalibrate(rocit->i2c_address,cal_pixels,0);
    }
    // Clear the signal for the full ROC:
    else {
      LOG(logDEBUGAPI) << "Clearing Calibrate for ROC@I2C " << static_cast<int>(rocit->i2c_address);
      _hal->RocClearCalibrate(rocit->i2c_address);
    }
  }

}

void pxarCore::checkTestboardDelays(std::vector<std::pair<std::string,uint8_t> > sig_delays) {

  // Take care of the signal delay settings:
  std::map<uint8_t,uint8_t> delays;
  for(std::vector<std::pair<std::string,uint8_t> >::iterator sigIt = sig_delays.begin(); sigIt != sig_delays.end(); ++sigIt) {

    // Fill the signal timing pairs with the register from the dictionary:
    uint8_t sigRegister, sigValue = sigIt->second;
    if(!verifyRegister(sigIt->first,sigRegister,sigValue,DTB_REG)) continue;

    std::pair<std::map<uint8_t,uint8_t>::iterator,bool> ret;
    ret = delays.insert( std::make_pair(sigRegister,sigValue) );
    if(ret.second == false) {
      LOG(logWARNING) << "Overwriting existing DTB delay setting \"" << sigIt->first
		      << "\" value " << static_cast<int>(ret.first->second)
		      << " with " << static_cast<int>(sigValue);
      delays[sigRegister] = sigValue;
    }
  }
  // Store these validated parameters in the DUT
  _dut->sig_delays = delays;
}

void pxarCore::checkTestboardPower(std::vector<std::pair<std::string,double> > power_settings) {

  // Read the power settings and make sure we got all, these here are the allowed limits:
  double va = 2.5, vd = 3.0, ia = 3.0, id = 3.0;
  for(std::vector<std::pair<std::string,double> >::iterator it = power_settings.begin(); it != power_settings.end(); ++it) {
    std::transform((*it).first.begin(), (*it).first.end(), (*it).first.begin(), ::tolower);

    if((*it).second < 0) {
      LOG(logERROR) << "Negative value for power setting \"" << (*it).first << "\". Using default limit.";
      continue;
    }

    if((*it).first.compare("va") == 0) {
      if((*it).second > va) { LOG(logWARNING) << "Limiting \"" << (*it).first << "\" to " << va; }
      else { va = (*it).second; }
      _dut->va = va;
    }
    else if((*it).first.compare("vd") == 0) {
      if((*it).second > vd) { LOG(logWARNING) << "Limiting \"" << (*it).first << "\" to " << vd; }
      else {vd = (*it).second; }
      _dut->vd = vd;
    }
    else if((*it).first.compare("ia") == 0) {
      if((*it).second > ia) { LOG(logWARNING) << "Limiting \"" << (*it).first << "\" to " << ia; }
      else { ia = (*it).second; }
      _dut->ia = ia;
    }
    else if((*it).first.compare("id") == 0) {
      if((*it).second > id) { LOG(logWARNING) << "Limiting \"" << (*it).first << "\" to " << id; }
      else { id = (*it).second; }
      _dut->id = id;
    }
    else { LOG(logERROR) << "Unknown power setting " << (*it).first << "! Skipping.";}
  }

  if(va < 0.01 || vd < 0.01 || ia < 0.01 || id < 0.01) {
    LOG(logCRITICAL) << "Power settings are not sufficient. Please check and re-configure!";
    throw InvalidConfig("Power settings are not sufficient. Please check and re-configure.");
  }
}

void pxarCore::verifyPatternGenerator(std::vector<std::pair<std::string,uint8_t> > &pg_setup) {

  std::vector<std::pair<uint16_t,uint8_t> > patterns;

  // Get the Pattern Generator dictionary for lookup:
  PatternDictionary * _dict = PatternDictionary::getInstance();

  // Check total length of the pattern generator:
  if(pg_setup.size() > 256) {
    LOG(logCRITICAL) << "Pattern too long (" << pg_setup.size() << " entries) for pattern generator. "
		     << "Only 256 entries allowed!";
    throw InvalidConfig("Pattern too long for pattern generator. Please check and re-configure.");
  }
  else { LOG(logDEBUGAPI) << "Pattern generator setup with " << pg_setup.size() << " entries provided."; }

  // Some booleans to keep track of PG content:
  bool have_trigger = false;
  bool have_tbmreset = false;

  // Loop over all entries provided:
  for(std::vector<std::pair<std::string,uint8_t> >::iterator it = pg_setup.begin(); it != pg_setup.end(); ++it) {

    // Check for current element if delay is zero:
    if(it->second == 0 && it != pg_setup.end() -1 ) {
      LOG(logCRITICAL) << "Found delay = 0 on early entry! This stops the pattern generator at position "
		       << static_cast<int>(it - pg_setup.begin())  << ".";
      throw InvalidConfig("Found delay = 0 on early entry! This stops the pattern generator.");
    }

    // Check last entry for PG stop signal (delay = 0):
    if(it == pg_setup.end() - 1 && it->second != 0) {
      LOG(logWARNING) << "No delay = 0 found on last entry. Setting last delay to 0 to stop the pattern generator.";
      it->second = 0;
    }

    // Convert the name to lower case for comparison:
    std::transform(it->first.begin(), it->first.end(), it->first.begin(), ::tolower);

    std::istringstream signals(it->first);
    std::string s;
    uint16_t signal = 0;
    // Tokenize the signal string into single PG signals, separated by ";":
    while (std::getline(signals, s, ';')) {
      // Get the signal from the dictionary object:
      uint16_t sig = _dict->getSignal(s,PATTERN_PG);
      if(sig != PATTERN_ERR) signal += sig;
      else {
	LOG(logCRITICAL) << "Could not find pattern generator signal \"" << s << "\" in the dictionary!";
	throw InvalidConfig("Wrong pattern generator signal provided.");
      }

      // Check for some specific signals:
      if(sig == PG_TRG) have_trigger = true;
      if(sig == PG_REST) have_tbmreset = true;

      LOG(logDEBUGAPI) << "Found PG signal " << s << " (" << std::hex << sig << std::dec << ")";
    }
    patterns.push_back(std::make_pair(signal,it->second));
  }

  // If there is no trigger, no data is requested and read out from any detector:
  if(!have_trigger) {
    LOG(logWARNING) << "Pattern generator does not contain a trigger signal. "
		    << "No data is expected from the DUT!";
  }
  // If a TBM Reset is present the TBM event counter gets reset every cycle, so
  // we can't use the event id to check for missing events in the readout:
  if(have_tbmreset) {
    LOG(logWARNING) << "Pattern generator contains TBM Reset signal. "
		    << "No event number cross checks possible.";
  }

  // Store the Pattern Generator commands in the DUT:
  _dut->pg_setup = patterns;
  // Calculate the sum of all delays and store it:
  _dut->pg_sum = getPatternGeneratorDelaySum(_dut->pg_setup);
}

uint32_t pxarCore::getPatternGeneratorDelaySum(std::vector<std::pair<uint16_t,uint8_t> > &pg_setup) {

  uint32_t delay_sum = 0;
  // Total cycle time is sum of delays plus once clock cycle for the actual command:
  for(std::vector<std::pair<uint16_t,uint8_t> >::iterator it = pg_setup.begin(); it != pg_setup.end(); ++it) { delay_sum += (*it).second + 1; }
  // Add one more clock cycle:
  delay_sum++;
  LOG(logDEBUGAPI) << "Sum of Pattern generator delays: " << delay_sum << " clk";
  return delay_sum;
}

bool pxarCore::setExternalClock(bool enable) {

  LOG(logDEBUGAPI) << "Setting clock to " << (enable ? "external" : "internal") << " source.";
  if(enable) {
    // Try to set the clock to external source:
    if(_hal->IsClockPresent()) { _hal->SetClockSource(CLK_SRC_EXT); return true; }
    else LOG(logCRITICAL) << "DTB reports that no external clock is present!";
    return false;
  }
  else {
    // Set the clock to internal source:
    _hal->SetClockSource(CLK_SRC_INT);
    return true;
  }
}

void pxarCore::setSignalMode(std::string signal, uint8_t mode, uint8_t speed) {

  uint8_t sigRegister, value = 0;
  if(!verifyRegister(signal, sigRegister, value, DTB_REG)) return;

  LOG(logDEBUGAPI) << "Setting signal " << signal << " ("
		   << static_cast<int>(sigRegister) << ")  to mode "
		   << static_cast<int>(mode) << ".";

  if(mode == 3) { _hal->SigSetPRBS(sigRegister, speed); }
  else { _hal->SigSetMode(sigRegister, mode); }
}

void pxarCore::setSignalMode(std::string signal, std::string mode, uint8_t speed) {

  uint8_t modeValue = 0xff;

  // Convert the name to lower case for comparison:
  std::transform(mode.begin(), mode.end(), mode.begin(), ::tolower);

  if(mode == "normal")      modeValue = 0;
  else if(mode == "low")    modeValue = 1;
  else if(mode == "high")   modeValue = 2;
  else if(mode == "random") modeValue = 3;
  else {
    LOG(logERROR) << "Unknown signal mode \"" << mode << "\"";
    return;
  }

  // Set the signal mode:
  setSignalMode(signal, modeValue, speed);
}

void pxarCore::setClockStretch(uint8_t src, uint16_t delay, uint16_t width)
{
  LOG(logDEBUGAPI) << "Set Clock Stretch " << static_cast<int>(src) << " " << static_cast<int>(delay) << " " << static_cast<int>(width);
  _hal->SetClockStretch(src,width,delay);

}

uint16_t pxarCore::GetADC( uint8_t rpc_par1 ){

  if( ! status() ) { return 0; }

  return _hal->GetADC( rpc_par1 );

}

void pxarCore::setReportingLevel(std::string logLevel)
{
  LOG(logQUIET) << "Changing Reporting Level from " << Log::ToString(Log::ReportingLevel()) << " to " << logLevel;
  Log::ReportingLevel() = Log::FromString(logLevel);
}

std::string pxarCore::getReportingLevel()
{
  LOG(logQUIET) << "Reporting Level is " << Log::ReportingLevel();
  return Log::ToString(Log::ReportingLevel());
}
