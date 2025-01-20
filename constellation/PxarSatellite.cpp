#include "PxarSatellite.hpp"

#include <chrono>
#include <cstdint>
#include <fstream>
#include <map>
#include <memory>
#include <stop_token>
#include <string_view>
#include <thread>
#include <vector>

#include <constellation/core/config/Configuration.hpp>
#include <constellation/core/log/log.hpp>
#include "constellation/core/protocol/CSCP_definitions.hpp"
#include <constellation/core/utils/string.hpp>
#include <constellation/satellite/TransmitterSatellite.hpp>

#include "api.h"
#include "dictionaries.h"
#include "helper.h"

using namespace constellation::config;
using namespace constellation::protocol;
using namespace constellation::satellite;
using namespace constellation::utils;

static const std::string EVENT_TYPE_DUT = "CMSPixelDUT";
static const std::string EVENT_TYPE_REF = "CMSPixelREF";
static const std::string EVENT_TYPE_TRP = "CMSPixelTRP";
static const std::string EVENT_TYPE_QUAD = "CMSPixelQUAD";

PxarSatellite::PxarSatellite(std::string_view type, std::string_view name)
    : TransmitterSatellite(type, name) {}

void PxarSatellite::initializing(Configuration& config) {

  // Read detector type:
  m_detector = transform(config.get<std::string>("detector"), ::toupper);
  if (m_detector == "REF") {
    m_event_type = EVENT_TYPE_REF;
  } else if (m_detector == "TRP") {
    m_event_type = EVENT_TYPE_TRP;
  } else if (m_detector == "QUAD") {
    m_event_type = EVENT_TYPE_QUAD;
  } else {
    m_detector = "DUT";
    m_event_type = EVENT_TYPE_DUT;
  }

  bool confTrimming(false), confDacs(false);
  // declare config vectors
  std::vector<std::pair<std::string, uint8_t>> sig_delays;
  std::vector<std::pair<std::string, double>> power_settings;
  std::vector<std::pair<std::string, uint8_t>> pg_setup;
  std::vector<std::vector<std::pair<std::string, uint8_t>>> tbmDACs;
  std::vector<std::vector<std::pair<std::string, uint8_t>>> rocDACs;
  std::vector<std::vector<pxar::pixelConfig>> rocPixels;
  std::vector<uint8_t> rocI2C;

  uint8_t hubid = config.get<uint8_t>("hubid", 31);

  // DTB delays
  sig_delays.emplace_back("clk", config.get<uint8_t>("clk", 4));
  sig_delays.emplace_back("ctr", config.get<uint8_t>("ctr", 4));
  sig_delays.emplace_back("sda", config.get<uint8_t>("sda", 19));
  sig_delays.emplace_back("tin", config.get<uint8_t>("tin", 9));
  sig_delays.emplace_back("deser160phase", config.get<uint8_t>("deser160phase", 4));
  sig_delays.emplace_back("level", config.get<uint8_t>("level", 15));
  sig_delays.emplace_back("triggerlatency", config.get<uint8_t>("triggerlatency", 86));
  sig_delays.emplace_back("tindelay", config.get<uint8_t>("tindelay", 13));
  sig_delays.emplace_back("toutdelay", config.get<uint8_t>("toutdelay", 8));
  sig_delays.emplace_back("triggertimeout",config.get<uint8_t>("triggertimeout",3000));

  // Power settings:
  power_settings.emplace_back("va", config.get<double>("va", 1.8));
  power_settings.emplace_back("vd", config.get<double>("vd", 2.5));
  power_settings.emplace_back("ia", config.get<double>("ia", 1.10));
  power_settings.emplace_back("id", config.get<double>("id", 1.10));

  // Periodic ROC resets:
  m_roc_resetperiod = config.get<unsigned>("rocresetperiod", 0);
  LOG_IF(INFO, m_roc_resetperiod > 0) << "Sending periodic ROC resets every " << m_roc_resetperiod << "ms";

  // Pattern Generator:
  const auto testpulses = config.get<bool>("testpulses", false);
  if (testpulses) {
    pg_setup.emplace_back("resetroc", config.get<uint8_t>("resetroc", 25));
    pg_setup.emplace_back("calibrate", config.get<uint8_t>("calibrate", 106));
    pg_setup.emplace_back("trigger", config.get<uint8_t>("trigger", 16));
    pg_setup.emplace_back("token", config.get<uint8_t>("token", 0));
    m_pattern_delay = config.get<int>("patternDelay", 100) * 10;
    LOG(INFO) << "Using testpulses, pattern delay " << m_pattern_delay;
  } else {
    pg_setup.emplace_back("trigger", 46);
    pg_setup.emplace_back("token", 0);
    m_pattern_delay = config.get<int>("patternDelay", 100);
  }

  try {
    // Acquire lock for pxarCore instance:
    std::lock_guard<std::mutex> lck(mutex_);

    // Check for multiple ROCs using the I2C parameter:
    std::vector<int32_t> i2c_addresses = config.getArray<int32_t>("i2c", {-1});
    LOG(INFO) << "Found " << i2c_addresses.size() << " I2C addresses: " << range_to_string(i2c_addresses);

    // Set the type of the TBM and read registers if any:
    m_tbmtype = config.get<std::string>("tbmtype", "notbm");
    LOG(INFO) << "TBM type: " << m_tbmtype;
    try {
      tbmDACs.push_back(GetConfDACs(config, 0, true));
      tbmDACs.push_back(GetConfDACs(config, 1, true));
      m_channels = 2;
    } catch (const pxar::InvalidConfig& e) {
      LOG(CRITICAL) << "Could not read TBM configs: " << e.what();
    }

    // Set the type of the ROC correctly:
    m_roctype = config.get<std::string>("roctype", "psi46digv21respin");

    // Read the type of carrier PCB used ("desytb", "desytb-rot"):
    m_pcbtype = config.get<std::string>("pcbtype", "desytb");

    // Read the mask file if existent:
    std::vector<pxar::pixelConfig> maskbits = GetConfMaskBits(config);

    // Read DACs and Trim settings for all ROCs, one for each I2C address:
    for (int32_t i2c : i2c_addresses) {
      // Read trim bits from config:
      rocPixels.push_back(GetConfTrimming(config, maskbits, static_cast<int16_t>(i2c)));
      // Read the DAC file and update the vector with overwrite DAC settings
      // from config:
      rocDACs.push_back(GetConfDACs(config, static_cast<int16_t>(i2c)));
      // Add the I2C address to the vector:
      if (i2c > -1) {
        rocI2C.push_back(static_cast<uint8_t>(i2c));
      } else {
        rocI2C.push_back(static_cast<uint8_t>(0));
      }
    }

    if (api_ != nullptr) {
      api_.reset();
    }

    // Get a new pxar instance:
    const auto usbId = config.get<std::string>("usbId", "*");
    api_ = std::make_unique<pxar::pxarCore>(usbId, "WARNING");
    LOG(INFO) << "Trying to connect to USB id: " << usbId;

    // Initialize the testboard:
    if (!api_->initTestboard(sig_delays, power_settings, pg_setup)) {
      throw pxar::pxarException("Firmware mismatch");
    }

    LOG(INFO) << "TBMDACs: " << tbmDACs.size();
    LOG(INFO) << "ROCDACs: " << rocDACs.size();

    // Initialize the DUT as configured above:
    api_->initDUT(hubid, m_tbmtype, tbmDACs, m_roctype, rocDACs, rocPixels, rocI2C);
    // Store the number of configured ROCs to be stored in a BORE tag:
    m_nplanes = rocDACs.size();

    // Read current:
    LOG(INFO) << "Analog current: " << api_->getTBia() * 1000 << "mA";
    LOG(INFO) << "Digital current: " << api_->getTBid() * 1000 << "mA";

    if (api_->getTBid() * 1000 < 15) {
      LOG(WARNING) << "Digital current too low: " << (1000 * api_->getTBid()) << "mA";
    } else {
      LOG(WARNING) << "Digital current: " << (1000 * api_->getTBid()) << "mA";
    }

    if (api_->getTBia() * 1000 < 15) {
      LOG(WARNING) << "Analog current too low: " << (1000 * api_->getTBia()) << "mA";
    } else {
      LOG(WARNING) << "Analog current: " << (1000 * api_->getTBia()) << "mA";
    }

    // Switching to external clock if requested and check if DTB returns TRUE
    // status:
    if (!api_->setExternalClock(config.get<bool>("external_clock", true))) {
      throw InvalidValueError(config, "external_clock", "Couldn't switch to selected clock source");
    }

    LOG(INFO) << "Clock set to " << (config.get<bool>("external_clock", true) ? "external" : "internal");

    // Switching to the selected trigger source and check if DTB returns TRUE:
    std::string triggersrc = config.get<std::string>("trigger_source", "extern");
    if (!api_->daqTriggerSource(triggersrc)) {
      throw InvalidValueError(config, "tigger_source", "Couldn't select trigger source");
    }
    // Update the TBM setting according to the selected trigger source.
    // Switches to TBM_EMU if we selected a trigger source using the TBM EMU.
    pxar::TriggerDictionary *trgDict;
    if (m_tbmtype == "notbm" &&
        trgDict->getInstance()->getEmulationState(triggersrc)) {
        m_tbmtype = "tbmemulator";
    }

    if (triggersrc == "pg" || triggersrc == "pg_dir" ||
        triggersrc == "patterngenerator") {
        m_trigger_is_pg = true;
    }
    LOG(INFO) << "Trigger source selected: " << triggersrc;

    // Send a single RESET to the ROC to initialize its status:
    if (!api_->daqSingleSignal("resetroc")) {
      throw CommunicationError("Unable to send ROC reset signal!");
    }
    if (m_tbmtype != "notbm" && !api_->daqSingleSignal("resettbm")) {
      throw CommunicationError("Unable to send TBM reset signal!");
    }

    // Output the configured signal to the probes:
    const auto signal_d1 = config.get<std::string>("signalprobe_d1", "off");
    const auto signal_d2 = config.get<std::string>("signalprobe_d2", "off");
    const auto signal_a1 = config.get<std::string>("signalprobe_a1", "off");
    const auto signal_a2 = config.get<std::string>("signalprobe_a2", "off");

    if (api_->SignalProbe("d1", signal_d1) && signal_d1 != "off") {
      LOG(INFO) << "Setting scope output D1 to \"" << signal_d1 << "\"";
    }
    if (api_->SignalProbe("d2", signal_d2) && signal_d2 != "off") {
      LOG(INFO) << "Setting scope output D2 to \"" << signal_d2 << "\"";
    }
    if (api_->SignalProbe("a1", signal_a1) && signal_a1 != "off") {
      LOG(INFO) << "Setting scope output A1 to \"" << signal_a1 << "\"";
    }
    if (api_->SignalProbe("a2", signal_a2) && signal_a2 != "off") {
      LOG(INFO) << "Setting scope output A2 to \"" << signal_a2 << "\"";
    }

    LOG(INFO) << api_->getVersion() << " API set up successfully...";

    // test pixels
    if (testpulses) {
      LOG(INFO) << "Setting up pixels for calibrate pulses..." << std::endl
                << "col \t row" << std::endl;
      for (int i = 40; i < 45; i++) {
        api_->_dut->testPixel(25, i, true);
      }
    }
    // Read DUT info, should print above filled information:
    api_->_dut->info();

    LOG(INFO) << "Current DAC settings:";
    api_->_dut->printDACs(0);

    if (!m_trimmingFromConf) {
      LOG(CRITICAL) << "Couldn't read trim parameters from configuration.";
    }

  } catch (pxar::pxarException &e) {
    throw SatelliteError(std::string("pxarCore Error: ") + e.what());
  } catch (...) {
    throw SatelliteError("Unknown exception");
  }
}

void PxarSatellite::launching() {
  try {
    // Acquire lock for pxarCore instance:
    std::lock_guard<std::mutex> lck(mutex_);

    LOG(INFO) << "Switching Sensor Bias HV ON.";
    api_->HVon();
    } catch(pxar::pxarException& e) {
        throw SatelliteError(std::string("pxar exception: ") + e.what());
    }
}

void PxarSatellite::landing() {
  try {
    // Acquire lock for pxarCore instance:
    std::lock_guard<std::mutex> lck(mutex_);

    LOG(INFO) << "Switching Sensor Bias HV OFF.";
    api_->HVoff();
    } catch(pxar::pxarException& e) {
        throw SatelliteError(std::string("pxar exception: ") + e.what());
    }
}

void PxarSatellite::starting(std::string_view /*run_identifier*/) {

  try {
    LOG(INFO) << "Starting Run";

    // Try to read left-over events from buffer:
    std::lock_guard<std::mutex> lck(mutex_);
    pxar::rawEvent daqEvent = api_->daqGetRawEvent();

    // Start the Data Acquisition:
    api_->daqStart();

    // Send additional ROC Reset signal at run start:
    if (!api_->daqSingleSignal("resetroc")) {
      throw CommunicationError("Unable to send ROC reset signal!");
    }

    LOG(INFO) << "ROC Reset signal issued.";

    // If we run on Pattern Generator, activate the PG loop:
    if (m_trigger_is_pg) {
      api_->daqTriggerLoop(m_pattern_delay);
    }

    // Start the timer for period ROC reset:
    m_reset_timer = std::chrono::steady_clock::now();

    // Set tags for the BOR message, make EUDAQ-compatible:
    setBORTag("eudaq_event", m_event_type);

    // Set the TBM & ROC type for decoding:
    setBORTag("ROCTYPE", m_roctype);
    setBORTag("TBMTYPE", m_tbmtype);

    // Set the number of planes (ROCs):
    setBORTag("PLANES", m_nplanes);

    // Store all DAC settings in one BORE tag:
    // FIXME
    // setBORTag("DACS", m_alldacs);

    // Set the PCB mount type for correct coordinate transformation:
    setBORTag("PCBTYPE", m_pcbtype);

    // Set the detector for correct plane assignment:
    setBORTag("DETECTOR", m_detector);

    // Store the pxarCore version this has been recorded with:
    setBORTag("PXARCORE", api_->getVersion());

    LOG(INFO) << "BOR message with detector " << m_detector << " (event type " << m_event_type << ") and ROC type " << m_roctype;
  } catch(pxar::pxarException& e) {
    throw SatelliteError(std::string("pxar exception: ") + e.what());
  }
}

void PxarSatellite::running(const std::stop_token &stop_token) {
  unsigned ev_runningavg_filled = 0;
  unsigned ev_filled = 0;

    while (!stop_token.stop_requested()) {

    // Send periodic ROC Reset
    if (m_roc_resetperiod > 0 &&
      (std::chrono::steady_clock::now() - m_reset_timer) > std::chrono::seconds{m_roc_resetperiod}) {
        std::lock_guard<std::mutex> lck(mutex_);
        if (!api_->daqSingleSignal("resetroc")) {
          LOG(CRITICAL) << "Unable to send ROC reset signal!";
        }
        m_reset_timer = std::chrono::steady_clock::now();
      }

      // Trying to get the next event, daqGetRawEvent throws exception if none is available:
      try {
          // Acquire lock for pxarCore object access:
          std::lock_guard<std::mutex> lck(mutex_);
          pxar::rawEvent daqEvent = api_->daqGetRawEvent();

          auto data_msg = newDataMessage(1);
          const auto seq = data_msg.getHeader().getSequenceNumber();
          auto data = daqEvent.data;
          data_msg.addFrame(std::move(data));
          data_msg.addTag("trigger_number", seq);
          data_msg.addTag("flag_trigger", true);
          sendDataMessage(data_msg);

          // Analog: Events with pixel data have more than 4 words for TBM header/trailer and 3 for each ROC header:
          if (m_roctype == "psi46v2") {
            if (daqEvent.data.size() > (4 * m_channels + 3 * m_nplanes)) {
              ev_filled++;
              ev_runningavg_filled++;
            }
          }
          // Events with pixel data have more than 4 words for TBM header/trailer and 1 for each ROC header:
          else if (daqEvent.data.size() > (4 * m_channels + m_nplanes)) {
            ev_filled++;
            ev_runningavg_filled++;
          }

      // Print every 1k evt:
      if (seq % 1000 == 0) {
        uint8_t filllevel = 0;
        api_->daqStatus(filllevel);
        LOG(INFO) << "CMSPixel " << m_detector << " EVT " << seq << " / " << ev_filled << " w/ px";
        LOG(INFO) << "\t Total average:  \t" << (seq > 0 ? std::to_string(100 * ev_filled / seq) : "(inf)") << "%";
        LOG(INFO) << "\t 1k Trg average: \t" << (100 * ev_runningavg_filled / 1000) << "%";
        LOG(INFO) << "\t RAM fill level: \t" << static_cast<int>(filllevel) << "%";
        ev_runningavg_filled = 0;
      }
    } catch (pxar::DataNoEvent &) {
      // No event available in derandomize buffers (DTB RAM), return to scheduler:
      sched_yield();
    } catch(const pxar::DataException &e) {
      LOG(CRITICAL) << "Data issue detected: " << e.what();
    }
  }
}

void PxarSatellite::stopping() {

    std::lock_guard<std::mutex> lck(mutex_);

    // If running with PG, halt the loop:
    if (m_trigger_is_pg) {
      api_->daqTriggerLoopHalt();
    }

    // Stop the Data Acquisition:
    api_->daqStop();

    try {
      // Read the rest of events from DTB buffer:
      std::vector<pxar::rawEvent> daqEvents = api_->daqGetRawEventBuffer();
      LOG(INFO) << "CMSPixel " << m_detector << " Post run read-out, sending " << daqEvents.size() << " evt.";

      for(const auto& evt : daqEvents) {

        auto data_msg = newDataMessage(1);
        const auto seq = data_msg.getHeader().getSequenceNumber();
        auto data = evt.data;
        data_msg.addFrame(std::move(data));
        data_msg.addTag("trigger_number", seq);
        sendDataMessage(data_msg);
      }
    } catch (pxar::DataNoEvent &) {
      // No event available in derandomize buffers (DTB RAM),
    }
}

std::string PxarSatellite::prepareFilename(std::string filename, std::string n) {

  size_t datpos = filename.find(".dat");
  if (datpos != std::string::npos) {
    filename.insert(datpos, "_C" + n);
  } else {
    filename += "_C" + n + ".dat";
  }
  return filename;
}

std::vector<std::pair<std::string, uint8_t>>
PxarSatellite::GetConfDACs(Configuration& config, int16_t i2c, bool tbm) {

  std::string regname = (tbm ? "TBM" : "DAC");

  std::string filename;
  // Read TBM register file, Core A:
  if (tbm && i2c < 1) {
    filename = prepareFilename(config.get<std::string>("tbmFile", ""), "0a");
  }
  // Read TBM register file, Core B:
  else if (tbm && i2c >= 1) {
    filename = prepareFilename(config.get<std::string>("tbmFile", ""), "0b");
  }
  // Read ROC DAC file, no I2C address indicator is given, assuming filename is
  // correct "as is":
  else if (i2c < 0) {
    filename = config.get<std::string>("dacFile", "");
  }
  // Read ROC DAC file, I2C address is given, appending a "_Cx" with x = I2C:
  else {
    filename =
        prepareFilename(config.get<std::string>("dacFile", ""), std::to_string(i2c));
  }

  std::vector<std::pair<std::string, uint8_t>> dacs;
  std::ifstream file(filename);
  size_t overwritten_dacs = 0;

  if (!file.fail()) {
    LOG(INFO) << "Reading " << regname << " settings from file \"" << filename << "\".";

    std::string line;
    while (std::getline(file, line)) {
      std::stringstream linestream(line);
      std::string name;
      int dummy, value;
      linestream >> dummy >> name >> value;

      // Check if the first part read was really the register:
      if (name == "") {
        // Rereading with only DAC name and value, no register:
        std::stringstream newstream(line);
        newstream >> name >> value;
      }

      // Convert to lower case for cross-checking with config:
      std::transform(name.begin(), name.end(), name.begin(), ::tolower);

      // Check if reading was correct:
      if (name.empty()) {
        LOG(CRITICAL) << "Problem reading DACs from file \"" << filename << "\": DAC name appears to be empty";
        throw pxar::InvalidConfig("WARNING: Problem reading DACs from file \"" + filename + "\": DAC name appears to be empty.");
      }

      // Skip the current limits that are wrongly placed in the DAC file
      // sometimes (belong to the DTB!)
      if (name == "vd" || name == "va") {
        continue;
      }

      // Check if this DAC is overwritten by directly specifying it in the
      // config file:
      if (config.has(name)) {
        std::cout << "Overwriting DAC " << name << " from file: " << value;
        value = config.get<int>(name);
        std::cout << " -> " << value << std::endl;
        overwritten_dacs++;
      }

      dacs.emplace_back(name, value);
      m_alldacs.append(name + " " + std::to_string(value) + "; ");
    }

    LOG(INFO) << "Successfully read " << dacs.size() << " DACs from file, " << overwritten_dacs << " overwritten by config.";
  } else {
    if (tbm) {
      throw pxar::InvalidConfig("Could not open " + regname + " file.");
    }

    LOG(CRITICAL) << "Could not open " << regname << " file \"" << filename << "\".";
    LOG(INFO) << "If DACs from configuration should be used, remove dacFile path.";
    throw pxar::InvalidConfig("Could not open " + regname + " file.");
  }

  return dacs;
}

std::vector<int32_t> PxarSatellite::split(const std::string &s, char delim) {
  std::vector<int32_t> result;
  std::stringstream ss(s);
  std::string item;
  while (std::getline(ss, item, delim)) {
    result.push_back(std::stoi(item));
  }
  return result;
}

std::vector<pxar::pixelConfig> PxarSatellite::GetConfMaskBits(Configuration& config) {

  // Read in the mask bits:
  std::vector<pxar::pixelConfig> maskbits;

  std::string filename = config.get<std::string>("maskFile", "");
  if (filename == "") {
    LOG(INFO) << "No mask file specified. Not masking anything.";
    return maskbits;
  }

  std::ifstream file(filename);

  if (!file.fail()) {
    std::string line;
    while (std::getline(file, line)) {
      std::stringstream linestream(line);
      std::string dummy, rowpattern;
      int roc, col;
      linestream >> dummy >> roc >> col >> rowpattern;
      if (rowpattern.find(":") != std::string::npos) {
        std::vector<int32_t> row = split(rowpattern, ':');
        for (size_t i = row.front(); i <= row.back(); i++) {
          maskbits.push_back(pxar::pixelConfig(roc, col, i, 15, true, false));
        }
      } else {
        maskbits.push_back(pxar::pixelConfig(roc, col, std::stoi(rowpattern),
                                             15, true, false));
      }
    }
  } else {
    LOG(INFO) << "Couldn't read mask bits from \"" << filename << "\". Not masking anything.";
  }

  LOG(INFO) << "Found " << maskbits.size() << " masked pixels in configuration: \"" << filename << "\"";
  return maskbits;
}

std::vector<pxar::pixelConfig> PxarSatellite::GetConfTrimming(Configuration& config, std::vector<pxar::pixelConfig> maskbits,
                                  int16_t i2c) {

  std::string filename;
  // No I2C address indicator is given, assuming filename is correct "as is":
  if (i2c < 0) {
    filename = config.get<std::string>("trimFile", "");
  }
  // I2C address is given, appending a "_Cx" with x = I2C:
  else {
    filename = prepareFilename(config.get<std::string>("trimFile", ""), std::to_string(i2c));
  }

  std::vector<pxar::pixelConfig> pixels;
  std::ifstream file(filename);

  if (!file.fail()) {
    std::string line;
    while (std::getline(file, line)) {
      std::stringstream linestream(line);
      std::string dummy;
      int trim, col, row;
      linestream >> trim >> dummy >> col >> row;
      pixels.emplace_back(col, row, trim, false, false);
    }
    m_trimmingFromConf = true;
  } else {
    LOG(WARNING) << "Couldn't read trim parameters from \"" << filename << "\". Setting all to 15.";
    for (int col = 0; col < 52; col++) {
      for (int row = 0; row < 80; row++) {
        pixels.emplace_back(col, row, 15, false, false);
      }
    }
    m_trimmingFromConf = false;
  }

  // Process the mask bit list:
  for (auto& px : pixels) {

    // Check if this pixel is part of the maskbit vector:
    std::vector<pxar::pixelConfig>::iterator maskpx =
        std::find_if(maskbits.begin(), maskbits.end(), pxar::findPixelXY(px.column(), px.row(), i2c < 0 ? 0 : i2c));
    // Pixel is part of mask vector, set the mask bit:
    if (maskpx != maskbits.end()) {
      px.setMask(true);
    }
  }

  if (m_trimmingFromConf) {
    LOG(INFO) << "Trimming successfully read from configuration: \"" << filename << "\"";
  }
  return pixels;
}

