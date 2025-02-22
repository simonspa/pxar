#include <iostream>
#include "PixSetup.hh"
#include "log.h"
#include <cstdlib>

#include "rsstools.hh"
#include "shist256.hh"

using namespace std;
using namespace pxar;

// ----------------------------------------------------------------------
PixSetup::PixSetup(pxarCore *a, PixTestParameters *tp, ConfigParameters *cp) {
  fApi               = a;
  fPixTestParameters = tp;
  fConfigParameters  = cp;
  fPixMonitor        = new PixMonitor(this);
  fDoAnalysisOnly    = false;
  fDoUpdateRootFile  = false;
  fGuiActive         = false;
  init();
}


// ----------------------------------------------------------------------
PixSetup::PixSetup(string verbosity, PixTestParameters *tp, ConfigParameters *cp) {
  fPixTestParameters = tp;
  fConfigParameters  = cp;
  fDoAnalysisOnly    = false;
  fDoUpdateRootFile  = false;
  fGuiActive         = false;
  init();

  vector<vector<pair<string,uint8_t> > >       rocDACs = fConfigParameters->getRocDacs();
  vector<vector<pair<string,uint8_t> > >       tbmDACs = fConfigParameters->getTbmDacs();
  vector<vector<pixelConfig> >                 rocPixels = fConfigParameters->getRocPixelConfig();
  vector<pair<string,uint8_t> >                sig_delays = fConfigParameters->getTbSigDelays();
  vector<pair<string, double> >                power_settings = fConfigParameters->getTbPowerSettings();
  vector<pair<std::string, uint8_t> >             pg_setup = fConfigParameters->getTbPgSettings();

  fApi = new pxar::pxarCore("*", verbosity);
  fApi->initTestboard(sig_delays, power_settings, pg_setup);
  fApi->initDUT(fConfigParameters->getHubId(),
		fConfigParameters->getTbmType(), tbmDACs,
		fConfigParameters->getRocType(), rocDACs,
		rocPixels);
  LOG(logINFO) << "DUT info: ";
  fApi->_dut->info();

  fPixMonitor = new PixMonitor(this);


}

// ----------------------------------------------------------------------
PixSetup::PixSetup() {
  fApi               = 0;
  fPixTestParameters = 0;
  fConfigParameters  = 0;
  fPixMonitor        = 0;
  fDoAnalysisOnly    = false;
  init();
  LOG(logDEBUG) << "PixSetup ctor()";
}

// ----------------------------------------------------------------------
PixSetup::~PixSetup() {
  LOG(logDEBUG) << "PixSetup free fPxarMemory";
  free(fPxarMemory);
}


// ----------------------------------------------------------------------
void PixSetup::killApi() {
  if (fApi) delete fApi;
}

// ----------------------------------------------------------------------
void PixSetup::init() {
  rsstools rss;
  LOG(logDEBUG) << "PixSetup init start; getCurrentRSS() = " << rss.getCurrentRSS();
  int N(100000);
  //  fPxarMemory = std::malloc(300000000);
  fPxarMemory = std::calloc(N, sizeof(shist256));
  fPxarMemHi  = ((shist256*)fPxarMemory) + N;

  LOG(logDEBUG) << "fPixTestParameters = " << fPixTestParameters;
  LOG(logDEBUG) << " fConfigParameters = " << fConfigParameters;
  LOG(logDEBUG) << "       fPxarMemory = " << fPxarMemory;
  LOG(logDEBUG)	<< "        fPxarMemHi = " << fPxarMemHi;

  if (0 == fPxarMemory) {
    LOG(logERROR) << "not enough memory; go invest money into a larger computer";
    exit(1);
  } else {
    //     shist256 *p = (shist256*)fPxarMemory;
    //     int cnt(0);
    //     while (p < fPxarMemHi) {
    //       if (cnt%100 == 0) cout << p << ": " << p->get(0) << ", " << (p - (shist256*)fPxarMemory) << endl;
    //       p += 1;
    //       ++cnt;
    //     }
    //     p -= 1;
    //     cout << p << ": " << p->get(0) << ", " << (p - (shist256*)fPxarMemory) << endl;
  }
  LOG(logDEBUG) << "PixSetup init done;  getCurrentRSS() = " << rss.getCurrentRSS() << " fPxarMemory = " << fPxarMemory;
}


// ----------------------------------------------------------------------
void PixSetup::writeAllFiles() {
  // -- DUT files
  writeDacParameterFiles();
  writeTrimFiles();
  writeTbmParameterFiles();

  // -- TB and configParameters.dat
  fConfigParameters->writeAllFiles();
}

// ----------------------------------------------------------------------
void PixSetup::writeDacParameterFiles() {
  vector<uint8_t> rocs = fApi->_dut->getEnabledRocIDs();
  for (unsigned int iroc = 0; iroc < rocs.size(); ++iroc) {
    fConfigParameters->writeDacParameterFile(rocs[iroc], fApi->_dut->getDACs(iroc));
  }
}

// ----------------------------------------------------------------------
void PixSetup::writeTrimFiles() {
  int active = fApi->_dut->getEnabledPixels().size();
  if (0 == active) {
    LOG(logINFO) << "enbling all pixels for trim file writing";
    fApi->_dut->testAllPixels(true);
  }
  vector<uint8_t> rocs = fApi->_dut->getEnabledRocIDs();
  for (unsigned int iroc = 0; iroc < rocs.size(); ++iroc) {
    fConfigParameters->writeTrimFile(rocs[iroc], fApi->_dut->getEnabledPixels(rocs[iroc]));
  }
  if (0 == active) {
    LOG(logINFO) << "disabling (again) all pixels for trim file writing";
    fApi->_dut->testAllPixels(false);
  }
}

// ----------------------------------------------------------------------
void PixSetup::writeTbmParameterFiles() {
  for (unsigned int itbm = 0; itbm < fApi->_dut->getNTbms(); itbm += 2) {
    fConfigParameters->writeTbmParameterFile(itbm/2,
					     fApi->_dut->getTbmDACs(itbm),
					     fApi->_dut->getTbmChainLengths(itbm),
					     fApi->_dut->getTbmDACs(itbm+1),
					     fApi->_dut->getTbmChainLengths(itbm+1)
					     );
  }
}

// ----------------------------------------------------------------------
void PixSetup::pinGui(int x, int y ) {
  fConfigParameters->setGuiX(x);
  fConfigParameters->setGuiY(y);
}
