#include "datasource_dtb.h"
#include "helper.h"
#include "constants.h"
#include "exceptions.h"
#include "rpc_calls.h"

namespace pxar {

  uint16_t dtbSource::FillBuffer() {
    pos = 0;
    do {
      dtbState = tb->Daq_Read(buffer, DTB_SOURCE_BLOCK_SIZE, dtbRemainingSize, channel);
    
      if (buffer.size() == 0) {
	if (stopAtEmptyData) throw dsBufferEmpty();
	if (dtbState) throw dsBufferOverflow();
      }
    } while (buffer.size() == 0);

    LOG4CPLUS_DEBUG(decodingLogger, "-------------------------");
    LOG4CPLUS_DEBUG(decodingLogger, "Channel " << static_cast<int>(channel)
		    << " (" << static_cast<int>(chainlength) << " ROCs)"
		    << (envelopetype == TBM_NONE ? " DESER160 " : (envelopetype == TBM_EMU ? " SOFTTBM " : " DESER400 ")));
    LOG4CPLUS_DEBUG(decodingLogger, "Remaining " << static_cast<int>(dtbRemainingSize));
    LOG4CPLUS_DEBUG(decodingLogger, "-------------------------");
    LOG4CPLUS_DEBUG(decodingLogger, "FULL RAW DATA BLOB:");
    LOG4CPLUS_DEBUG(decodingLogger, listVector(buffer,true));
    LOG4CPLUS_DEBUG(decodingLogger, "-------------------------");

    return lastSample = buffer[pos++];
  }

}
