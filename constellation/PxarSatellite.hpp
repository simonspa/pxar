#pragma once

#include <memory>
#include <mutex>
#include <stop_token>
#include <string_view>

#include <constellation/core/config/Configuration.hpp>
#include <constellation/core/log/Level.hpp>
#include <constellation/core/log/Logger.hpp>
#include <constellation/core/protocol/CSCP_definitions.hpp>
#include <constellation/satellite/TransmitterSatellite.hpp>

#include "api.h"

class PxarLogger final : public std::stringbuf {
public:
    PxarLogger();
    ~PxarLogger();
    int sync() final;
    static std::pair<constellation::log::Level, std::size_t> getLogLevel(std::string_view log_lvl);

private:
    constellation::log::Logger logger_;
};

class PxarSatellite final : public constellation::satellite::TransmitterSatellite {
public:
    PxarSatellite(std::string_view type, std::string_view name);

    void initializing(constellation::config::Configuration& config) final;
    void launching() final;
    void landing() final;
    void starting(std::string_view run_identifier) final;
    void running(const std::stop_token& stop_token) final;
    void stopping() final;

private:
    // Parameters
    unsigned m_roc_resetperiod;
    unsigned m_nplanes;
    unsigned m_channels;
    int m_pattern_delay;
    bool m_trimmingFromConf, m_trigger_is_pg;
    std::string m_roctype, m_tbmtype, m_pcbtype, m_detector, m_event_type, m_alldacs;

    // Methods
    std::vector<std::pair<std::string, uint8_t>> GetConfDACs(constellation::config::Configuration& config,
                                                             int16_t i2c = -1,
                                                             bool tbm = false);
    std::vector<pxar::pixelConfig> GetConfMaskBits(constellation::config::Configuration& config);
    std::vector<pxar::pixelConfig> GetConfTrimming(constellation::config::Configuration& config,
                                                   std::vector<pxar::pixelConfig> maskbits,
                                                   int16_t i2c = -1);
    std::string prepareFilename(std::string filename, std::string n);
    std::vector<std::size_t> split(const std::string& s, char delim);

    PxarLogger pxar_logger_;

    // Add one mutex to protect calls to pxarCore:
    std::mutex mutex_;
    std::unique_ptr<pxar::pxarCore> api_;
    std::chrono::steady_clock::time_point m_reset_timer;
};
