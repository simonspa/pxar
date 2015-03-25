/**
 * pxar hardware constants
 * this file contains DAC definitions and other global constants such
 * as testboard register ids
 */

#ifndef PXAR_CONSTANTS_H
#define PXAR_CONSTANTS_H

namespace pxar {

// --- Data Transmission settings & flags --------------------------------------
#define DTB_SOURCE_BLOCK_SIZE  8192
#define DTB_SOURCE_BUFFER_SIZE 50000000
#define DTB_DAQ_FIFO_OVFL 4 // bit 2 = DAQ fast HW FIFO overflow
#define DTB_DAQ_MEM_OVFL  2 // bit 1 = DAQ RAM FIFO overflow
#define DTB_DAQ_STOPPED   1 // bit 0 = DAQ stopped (because of overflow)


// --- TBM Types ---------------------------------------------------------------
#define TBM_NONE           0x20
#define TBM_EMU            0x21
#define TBM_08             0x22
#define TBM_08A            0x23
#define TBM_08B            0x24
#define TBM_09             0x25


// --- TBM Register -----------------------------------------------------------
// These register addresses give the position relative to the base of the cores
// To actually program the TBM the base has to be added, e.g.
// Register 0x04 + Base -> 0xE4 or 0xF4
#define TBM_REG_COUNTER_SWITCHES    0x00
#define TBM_REG_SET_MODE            0x02
#define TBM_REG_CLEAR_INJECT        0x04
#define TBM_REG_SET_PKAM_COUNTER    0x08
#define TBM_REG_SET_DELAYS          0x0A
#define TBM_REG_TEMPERATURE_CONTROL 0x0C
#define TBM_REG_CORES_A_B           0x0E


// --- ROC Size ---------------------------------------------------------------
#define ROC_NUMROWS 80
#define ROC_NUMCOLS 52
#define MOD_NUMROCS 16

// --- ROC Types ---------------------------------------------------------------
#define ROC_PSI46V2           0x01
#define ROC_PSI46XDB          0x02
#define ROC_PSI46DIG          0x03
#define ROC_PSI46DIG_TRIG     0x04
#define ROC_PSI46DIGV2_B      0x05
#define ROC_PSI46DIGV2        0x06
#define ROC_PSI46DIGV21       0x07
#define ROC_PSI46DIGV21RESPIN 0x08


// --- ROC DACs ---------------------------------------------------------------
#define ROC_DAC_Vdig       0x01
#define ROC_DAC_Vana       0x02
#define ROC_DAC_Vsh        0x03
#define ROC_DAC_Vcomp      0x04
#define ROC_DAC_Vleak_comp 0x05
#define ROC_DAC_VrgPr      0x06
#define ROC_DAC_VwllPr     0x07
#define ROC_DAC_VrgSh      0x08
#define ROC_DAC_VwllSh     0x09
#define ROC_DAC_VhldDel    0x0A
#define ROC_DAC_Vtrim      0x0B
#define ROC_DAC_VthrComp   0x0C
#define ROC_DAC_VIBias_Bus 0x0D
#define ROC_DAC_Vbias_sf   0x0E
#define ROC_DAC_VoffsetOp  0x0F
#define ROC_DAC_VIbiasOp   0x10
#define ROC_DAC_VoffsetRO  0x11
#define ROC_DAC_VIon       0x12
#define ROC_DAC_VIbias_PH  0x13
#define ROC_DAC_VIbias_DAC 0x14
#define ROC_DAC_VIbias_roc 0x15
#define ROC_DAC_VIColOr    0x16
#define ROC_DAC_Vnpix      0x17
#define ROC_DAC_VsumCol    0x18
#define ROC_DAC_Vcal       0x19
#define ROC_DAC_CalDel     0x1A
#define ROC_DAC_CtrlReg    0xFD
#define ROC_DAC_WBC        0xFE
#define ROC_DAC_Readback   0xFF


// --- Testboard Signal Delay -------------------------------------------------
#define SIG_CLK 0
#define SIG_CTR 1
#define SIG_SDA 2
#define SIG_TIN 3
#define SIG_RDA_TOUT 4

#define SIG_ADC_TINDELAY 0xF7
#define SIG_ADC_TOUTDELAY 0xF8
#define SIG_ADC_TIMEOUT 0xF9
#define SIG_TRIGGER_TIMEOUT 0xFA
#define SIG_TRIGGER_LATENCY 0xFB
#define SIG_LEVEL 0xFC
#define SIG_LOOP_TRIGGER_DELAY 0xFD
#define SIG_DESER160PHASE 0xFE

#define SIG_MODE_NORMAL  0
#define SIG_MODE_LO      1
#define SIG_MODE_HI      2
#define SIG_MODE_RNDM    3


// --- Testboard Clock / Timing -----------------------------------------------
#define CLK_SRC_INT 0
#define CLK_SRC_EXT 1

// --- Clock Stretch and Clock Divider settings -------------------------------
#define STRETCH_AFTER_TRG  0
#define STRETCH_AFTER_CAL  1
#define STRETCH_AFTER_RES  2
#define STRETCH_AFTER_SYNC 3

#define MHZ_1_25   5
#define MHZ_2_5    4
#define MHZ_5      3
#define MHZ_10     2
#define MHZ_20     1
#define MHZ_40     0

// --- Trigger settings -------------------------------------------------------
#define TRG_SEL_ASYNC      0x100
#define TRG_SEL_SYNC       0x080
#define TRG_SEL_SINGLE     0x040
#define TRG_SEL_GEN        0x020
#define TRG_SEL_PG         0x010
#define TRG_SEL_SINGLE_DIR 0x008
#define TRG_SEL_PG_DIR     0x004
#define TRG_SEL_CHAIN      0x002
#define TRG_SEL_SYNC_OUT   0x001

#define TRG_SEND_SYN   1
#define TRG_SEND_TRG   2
#define TRG_SEND_RSR   4
#define TRG_SEND_RST   8
#define TRG_SEND_CAL  16


// --- Testboard digital signal probe -----------------------------------------
#define PROBE_OFF 0
#define PROBE_CLK 1
#define PROBE_SDA 2
#define PROBE_SDA_SEND 3
#define PROBE_PG_TOK 4
#define PROBE_PG_TRG 5
#define PROBE_PG_CAL 6
#define PROBE_PG_RES_ROC 7
#define PROBE_PG_RES_TBM 8
#define PROBE_PG_SYNC 9
#define PROBE_CTR 10
#define PROBE_TIN 11
#define PROBE_TOUT 12
#define PROBE_CLK_PRESEN 13
#define PROBE_CLK_GOOD 14
#define PROBE_DAQ0_WR 15
#define PROBE_CRC 16
#define PROBE_ADC_RUNNING 19
#define PROBE_ADC_RUN 20
#define PROBE_ADC_PGATE 21
#define PROBE_ADC_START 22
#define PROBE_ADC_SGATE 23
#define PROBE_ADC_S 24

#define PROBE_TBM0_GATE 100
#define PROBE_TBM0_DATA 101
#define PROBE_TBM0_TBMHDR 102
#define PROBE_TBM0_ROCHDR 103
#define PROBE_TBM0_TBMTRL 104

#define PROBE_TBM1_GATE 105
#define PROBE_TBM1_DATA 106
#define PROBE_TBM1_TBMHDR 107
#define PROBE_TBM1_ROCHDR 108
#define PROBE_TBM1_TBMTRL 109

#define PROBE_TBM2_GATE 110
#define PROBE_TBM2_DATA 111
#define PROBE_TBM2_TBMHDR 112
#define PROBE_TBM2_ROCHDR 113
#define PROBE_TBM2_TBMTRL 114

#define PROBE_TBM3_GATE 115
#define PROBE_TBM3_DATA 116
#define PROBE_TBM3_TBMHDR 117
#define PROBE_TBM3_ROCHDR 118
#define PROBE_TBM3_TBMTRL 119

#define PROBE_TBM4_GATE 120
#define PROBE_TBM4_DATA 121
#define PROBE_TBM4_TBMHDR 122
#define PROBE_TBM4_ROCHDR 123
#define PROBE_TBM4_TBMTRL 124

#define PROBE_TBM5_GATE 125
#define PROBE_TBM5_DATA 126
#define PROBE_TBM5_TBMHDR 127
#define PROBE_TBM5_ROCHDR 128
#define PROBE_TBM5_TBMTRL 129


// --- Testboard analog signal probe ------------------------------------------
#define PROBEA_TIN     0
#define PROBEA_SDATA1  1
#define PROBEA_SDATA2  2
#define PROBEA_CTR     3
#define PROBEA_CLK     4
#define PROBEA_SDA     5
#define PROBEA_TOUT    6
#define PROBEA_OFF     7

#define GAIN_1   0
#define GAIN_2   1
#define GAIN_3   2
#define GAIN_4   3


// --- Testboard pulse pattern generator --------------------------------------
#define PG_TOK   0x0100
#define PG_TRG   0x0200
#define PG_CAL   0x0400
#define PG_RESR  0x0800
#define PG_REST  0x1000
#define PG_SYNC  0x2000

} //namespace pxar

#endif /* PXAR_CONSTANTS_H */
