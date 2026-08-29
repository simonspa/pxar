/**
 * pxar API logging class
 */

#ifndef PXAR_LOGGING_H
#define PXAR_LOGGING_H

#include <sstream>
#include <iomanip>
#include <cstdio>
#include <string.h>

#include "logging.h"

#ifndef __FILE_NAME__
#define __FILE_NAME__ (strrchr(__FILE__, '/') ? strrchr(__FILE__, '/') + 1 : __FILE__)
#endif

#define IFLOG(level) \
  if (level > pxar::Log::ReportingLevel() || !pxar::SetLogOutput::Stream()) ; \
  else 

#define LOG(level)				\
  if (level > pxar::Log::ReportingLevel() || !pxar::SetLogOutput::Stream()) ; \
  else pxar::Log().Get(level,__FILE_NAME__,__func__,__LINE__)

#endif /* PXAR_LOGGING_H */
