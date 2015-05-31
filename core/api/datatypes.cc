#include "datatypes.h"
#include "helper.h"
#include "exceptions.h"
#include "constants.h"

namespace pxar {


  void pixel::decodeRaw(uint32_t raw, bool invert) {
    // Get the pulse height:
    setValue(static_cast<double>((raw & 0x0f) + ((raw >> 1) & 0xf0)));
    if((raw & 0x10) > 0) {
      LOG4CPLUS_DEBUG(pxarCoreLogger, "invalid pulse-height fill bit from raw value of "<< std::hex << raw << std::dec << ": " << *this);
      throw DataInvalidPulseheightError("Error decoding pixel raw value");
    }

    // Decode the pixel address
    int r2 =    (raw >> 15) & 7;
    if(invert) { r2 ^= 0x7; }
    int r1 = (raw >> 12) & 7;
    if(invert) { r1 ^= 0x7; }
    int r0 = (raw >>  9) & 7;
    if(invert) { r0 ^= 0x7; }
    int r = r2*36 + r1*6 + r0;
    _row = 80 - r/2;
    _column = 2*(((raw >> 21) & 7)*6 + ((raw >> 18) & 7)) + (r&1);

    // Perform range checks:
    if(_row >= ROC_NUMROWS || _column >= ROC_NUMCOLS) {
      LOG4CPLUS_DEBUG(pxarCoreLogger, "Invalid pixel from raw value of "<< std::hex << raw << std::dec << ": " << *this);
      if(_row == ROC_NUMROWS) throw DataCorruptBufferError("Error decoding pixel raw value");
      else throw DataInvalidAddressError("Error decoding pixel raw value");
    }
  }

  uint8_t pixel::translateLevel(uint16_t x, int16_t level0, int16_t level1, int16_t levelS) {
    int16_t y = expandSign(x) - level0;
    if (y >= 0) y += levelS; else y -= levelS;
    return level1 ? y/level1 + 1: 0;
  }

  void pixel::decodeAnalog(std::vector<uint16_t> analog, int16_t ultrablack, int16_t black) {
    // Check pixel data length:
    if(analog.size() != 6) {
      LOG4CPLUS_DEBUG(pxarCoreLogger, "Received wrong number of data words for a pixel: " << analog.size());
      throw DataInvalidAddressError("Received wrong number of data words for a pixel");
    }

    // Calculate the levels:
    int16_t level0 = black;
    int16_t level1 = (black - ultrablack)/4;
    int16_t levelS = level1/2;

    // Get the pulse height:
    setValue(static_cast<double>(expandSign(analog.back() & 0x0fff) - level0));

    // Decode the pixel address
    int c1 = translateLevel(analog.at(0),level0,level1,levelS);
    int c0 = translateLevel(analog.at(1),level0,level1,levelS);
    int c  = c1*6 + c0;

    int r2 = translateLevel(analog.at(2),level0,level1,levelS);
    int r1 = translateLevel(analog.at(3),level0,level1,levelS);
    int r0 = translateLevel(analog.at(4),level0,level1,levelS);
    int r  = (r2*6 + r1)*6 + r0;

    _row = 80 - r/2;
    _column = 2*c + (r&1);

    // Perform range checks:
    if(_row >= ROC_NUMROWS || _column >= ROC_NUMCOLS) {
      LOG4CPLUS_DEBUG(pxarCoreLogger, "Invalid pixel from levels "<< listVector(analog) << ": " << *this);
      throw DataInvalidAddressError("Error decoding pixel address");
    }
  }

  uint32_t pixel::encode() {
    uint32_t raw = 0;
    // Set the pulse height:
    raw = ((static_cast<int>(value()) & 0xf0) << 1) + (static_cast<int>(value()) & 0xf);

    // Encode the pixel address
    int r = 2*(80 - _row);
    raw |= ((r/36) << 15);
    raw |= (((r%36)/6) << 12);
    raw |= (((r%36)%6 + _column%2) << 9);

    int dcol = _column/2;
    raw |= ((dcol)/6 << 21);
    raw |= (((dcol%6)) << 18);

    LOG4CPLUS_DEBUG(decodingLogger, "Pix  " << static_cast<int>(_column) << "|" 
		    << static_cast<int>(_row) << " = "
		    << dcol << "/" << r << " = "
		    << dcol/6 << " " << dcol%6 << " "
		    << r/36 << " " << (r%36)/6 << " " << (r%36)%6);

    // Return the 24 bits belonging to the pixel:
    return (raw & 0x00ffffff);
  }

  void Event::printHeader() {
    LOG4CPLUS_INFO(pxarCoreLogger, "Header content: 0x" << std::hex << header << std::dec);
    LOG4CPLUS_INFO(pxarCoreLogger, "\t Event ID \t" << static_cast<int>(this->triggerCount()));
    LOG4CPLUS_INFO(pxarCoreLogger, "\t Data ID " << static_cast<int>(this->dataID()) 
		   << " Value " << static_cast<int>(this->dataValue()));
  }

  void Event::printTrailer() {
    LOG4CPLUS_INFO(pxarCoreLogger, "Trailer content: 0x" << std::hex << trailer << std::dec);
    LOG4CPLUS_INFO(pxarCoreLogger, "\t Token Pass \t" << textBool(this->hasTokenPass()));
    LOG4CPLUS_INFO(pxarCoreLogger, "\t Reset TBM \t" << textBool(this->hasResetTBM()));
    LOG4CPLUS_INFO(pxarCoreLogger, "\t Reset ROC \t" << textBool(this->hasResetROC()));
    LOG4CPLUS_INFO(pxarCoreLogger, "\t Sync Err \t" << textBool(this->hasSyncError()));
    LOG4CPLUS_INFO(pxarCoreLogger, "\t Sync Trigger \t" << textBool(this->hasSyncTrigger()));
    LOG4CPLUS_INFO(pxarCoreLogger, "\t ClearTrig Cnt \t" << textBool(this->hasClearTriggerCount()));
    LOG4CPLUS_INFO(pxarCoreLogger, "\t Cal Trigger \t" << textBool(this->hasCalTrigger()));
    LOG4CPLUS_INFO(pxarCoreLogger, "\t Stack Full \t" << textBool(this->stackFull()));

    LOG4CPLUS_INFO(pxarCoreLogger, "\t Auto Reset \t" << textBool(this->hasAutoReset()));
    LOG4CPLUS_INFO(pxarCoreLogger, "\t PKAM Reset \t" << textBool(this->hasPkamReset()));
    LOG4CPLUS_INFO(pxarCoreLogger, "\t Stack Count \t" << static_cast<int>(this->stackCount()));
  }

  void statistics::dump() {
    // Print out the full statistics:
    LOG4CPLUS_INFO(pxarCoreLogger, "Decoding statistics:");
    LOG4CPLUS_INFO(pxarCoreLogger, "  General information:");
    LOG4CPLUS_INFO(pxarCoreLogger, "\t 16bit words read:         " << this->info_words_read());
    LOG4CPLUS_INFO(pxarCoreLogger, "\t valid events total:       " << this->info_events_total());
    LOG4CPLUS_INFO(pxarCoreLogger, "\t empty events:             " << this->info_events_empty());
    LOG4CPLUS_INFO(pxarCoreLogger, "\t valid events with pixels: " << this->info_events_valid());
    LOG4CPLUS_INFO(pxarCoreLogger, "\t valid pixel hits:         " << this->info_pixels_valid());
    LOG4CPLUS_INFO(pxarCoreLogger, "  Event errors: \t           " << this->errors_event());
    LOG4CPLUS_INFO(pxarCoreLogger, "\t start marker:             " << this->errors_event_start());
    LOG4CPLUS_INFO(pxarCoreLogger, "\t stop marker:              " << this->errors_event_stop());
    LOG4CPLUS_INFO(pxarCoreLogger, "\t overflow:                 " << this->errors_event_overflow());
    LOG4CPLUS_INFO(pxarCoreLogger, "\t invalid 5bit words:       " << this->errors_event_invalid_words());
    LOG4CPLUS_INFO(pxarCoreLogger, "\t invalid XOR eye diagram:  " << this->errors_event_invalid_xor());
    LOG4CPLUS_INFO(pxarCoreLogger, "  TBM errors: \t\t           " << this->errors_tbm());
    LOG4CPLUS_INFO(pxarCoreLogger, "\t flawed TBM headers:       " << this->errors_tbm_header());
    LOG4CPLUS_INFO(pxarCoreLogger, "\t flawed TBM trailers:      " << this->errors_tbm_trailer());
    LOG4CPLUS_INFO(pxarCoreLogger, "\t event ID mismatches:      " << this->errors_tbm_eventid_mismatch());
    LOG4CPLUS_INFO(pxarCoreLogger, "  ROC errors: \t\t           " << this->errors_roc());
    LOG4CPLUS_INFO(pxarCoreLogger, "\t missing ROC header(s):    " << this->errors_roc_missing());
    LOG4CPLUS_INFO(pxarCoreLogger, "\t misplaced readback start: " << this->errors_roc_readback());
    LOG4CPLUS_INFO(pxarCoreLogger, "  Pixel decoding errors:\t   " << this->errors_pixel());
    LOG4CPLUS_INFO(pxarCoreLogger, "\t pixel data incomplete:    " << this->errors_pixel_incomplete());
    LOG4CPLUS_INFO(pxarCoreLogger, "\t pixel address:            " << this->errors_pixel_address());
    LOG4CPLUS_INFO(pxarCoreLogger, "\t pulse height fill bit:    " << this->errors_pixel_pulseheight());
    LOG4CPLUS_INFO(pxarCoreLogger, "\t buffer corruption:        " << this->errors_pixel_buffer_corrupt());
  }

  void statistics::clear() {
    m_info_words_read = 0;
    m_info_events_empty = 0;
    m_info_events_valid = 0;
    m_info_pixels_valid = 0;

    m_errors_event_start = 0;
    m_errors_event_stop = 0;
    m_errors_event_overflow = 0;
    m_errors_event_invalid_words = 0;
    m_errors_event_invalid_xor = 0;

    m_errors_tbm_header = 0;
    m_errors_tbm_trailer = 0;
    m_errors_tbm_eventid_mismatch = 0;

    m_errors_roc_missing = 0;
    m_errors_roc_readback = 0;

    m_errors_pixel_incomplete = 0;
    m_errors_pixel_address = 0;
    m_errors_pixel_pulseheight = 0;
    m_errors_pixel_buffer_corrupt = 0;
  }

  statistics& operator+=(statistics &lhs, const statistics &rhs) {
    // Informational bits:
    lhs.m_info_words_read += rhs.m_info_words_read;
    lhs.m_info_events_empty += rhs.m_info_events_empty;
    lhs.m_info_events_valid += rhs.m_info_events_valid;
    lhs.m_info_pixels_valid += rhs.m_info_pixels_valid;

    // Event errors:
    lhs.m_errors_event_start += rhs.m_errors_event_start;
    lhs.m_errors_event_stop += rhs.m_errors_event_stop;
    lhs.m_errors_event_overflow += rhs.m_errors_event_overflow;
    lhs.m_errors_event_invalid_words += rhs.m_errors_event_invalid_words;
    lhs.m_errors_event_invalid_xor += rhs.m_errors_event_invalid_xor;

    // TBM errors:
    lhs.m_errors_tbm_header += rhs.m_errors_tbm_header;
    lhs.m_errors_tbm_trailer += rhs.m_errors_tbm_trailer;
    lhs.m_errors_tbm_eventid_mismatch += rhs.m_errors_tbm_eventid_mismatch;

    // ROC errors:
    lhs.m_errors_roc_missing += rhs.m_errors_roc_missing;
    lhs.m_errors_roc_readback += rhs.m_errors_roc_readback;

    // Pixel decoding errors:
    lhs.m_errors_pixel_incomplete += rhs.m_errors_pixel_incomplete;
    lhs.m_errors_pixel_address += rhs.m_errors_pixel_address;
    lhs.m_errors_pixel_pulseheight += rhs.m_errors_pixel_pulseheight;
    lhs.m_errors_pixel_buffer_corrupt += rhs.m_errors_pixel_buffer_corrupt;

    return lhs;
  }

} // namespace pxar
