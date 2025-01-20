---
# SPDX-License-Identifier: CC-BY-4.0
title: "pxar"
description: "CMSPixel Phase 1 Detector"
category: "External"
language: "C++"
parent_class: "TransmitterSatellite"
---

## Description

The *PxarSatellite* integrates the pxarCore library with Constellation.
It provides the interface functions for the satellite finite state machine to allow integrated data acquisition with other
satellites. When running a DAQ with a TBM and multiple ROCs configured, the *PxarSatellite* will automatically assemble all
ROCs found in the readout stream to a module-like pixel plane for both online monitoring and correlation as well as for the
conversion to other formats.

All functions provided by pxarCore are supported, including operation of all sorts of PSI46 devices such as analog PSI46V2
ROCs as well as custom-built telescopes using PSI46 devices as telescope planes. Even beam telescopes with several planes
consisting of full CMS Pixel modules featuring 16 ROCs each have been [successfully operated](https://indico.cern.ch/event/368934/session/12/contribution/35/attachments/733916/1006970/2015-06-10-pixel-workshop-beamtests.pdf).
The *PxarSatellite* checks all supplied configuration parameters for consistency and catches exceptions thrown by pxarCore.
Error messages are sent via the Constellation logging facilities. This allows to identify improper detector configuration
already at initialization stage before the actual data acquisition starts. Important parameters for offline interpretation
of the data recorded such as the type and the number of ROCs operated, all DAC parameters as well as the TBM type are written
into the begin-of-run (BOR) message in form of tags consisting of a name-value pair. These tags can be read from the stored
data files and used for correct interpretation of the data.

Following the paradigm of the Constellation framework, the detector data read during data taking is stored as-is, meaning
that no data decoding is performed online prior to storing the data to disk. This has the advantage that possible flaws in
the decoding methods do not affect the data taken, but the conversion to other event formats can just be re-run on the raw
and unaltered detector data.

## Building

Building requires:

- CMake
- `pkg-config`
- Constellation v0.3 or newer

If Constellation is not installed in a default system directory such as `/usr/local`, the directory needs to be exported in
order to be found by `pkg-config`:

```sh
export CNSTLN_PREFIX="/opt/constellation"
export PKG_CONFIG_PATH="$CNSTLN_PREFIX/share/pkgconfig:$CNSTLN_PREFIX/lib64/pkgconfig:$CNSTLN_PREFIX/lib/x86_64-linux-gnu/pkgconfig"
```

Then, the *PxarSatellite* can be built with CMake:

```sh
mkdir build && cd build
cmake .. -DBUILD_CNSTLN_SATELLITE=ON
make -j$(nproc)
make install
```

```{hint}
To disable building the pXar UI, add `-DBUILD_pxarui=OFF` to the CMake call.
```

## Parameters


The following parameters are read and interpreted by this satellite. Parameters without a default value are required.

| Parameter  | Description | Type | Default Value |
|------------|-------------|------|---------------|
| `pxar_verbosity` | Verbosity setting of the pxarCore library. All verbosity levels and their outputs are described in Section 5.8 of [the pxar manual](https://cds.cern.ch/record/2137512). The following mapping to Constellation log levels is used: `INTERFACE`, `DEBUGPIPES`, `DEBUGRPC` become `TRACE`; `DEBUGHAL`, `DEBUGAPI` and `DEBUG` become `DEBUG`; `INFO` corresponds to `INFO`, `WARNING` to `WARNING`, both `ERROR` and `CRITICAL` become `CRITICAL` and `QUET` is mapped to `STATUS`. | String | `INFO` |
| `roctype` | The device type of the ROC to be operated. This will be fed to the function `pxarCore::initDUT(...)`. The list of available devices can be found in Table 2 of [the pxar manual](https://cds.cern.ch/record/2137512) | String | `psi46digv21respin` |
| `pcbtype` | Type of the carrier printed circuit board (PCB) the ROC is mounted on. Content of this is free and it can be used to keep track of different PCB types, e.g. distinguishing different material budgets. If the PCB type parameter contains the pattern -rot indicating a PCB with the ROC mounted in a π/2 rotated position, columns and rows will automatically be swapped | String | `desytb` |
| `i2c` | This is an optional parameter for specifying non-standard (non-0) I2 C addresses the devices are listening on. This parameter takes a vector of integers which allows to run more than one ROC attached to a single DTB such as token-chained ROCs in beam telescopes, or full CMS Pixel modules. For this, the I2C address of every ROC has to be specified, e.g. `i2c = 0 1 2 4 5 6` would set up the DUT in a way that six ROCs are programmed (using six DAC and trim bit files) and read out. If no I2C parameter is specified, the I2C address defaults to 0 and the `dacFile` and `trimFile` parameters are assumed to represent the full path and name of the files to be read. If the I2C parameter is specified (even for a single ROC) the file names will be appended with the pattern `_Cx` where `x` is the I2C address from this parameter. This is possible for both single chips and multiple ROCs. | Array of integers | - |
| `dacFile` | standard formatted pxar configuration file containing all DAC parameters for the ROC. These values will be provided to the `pxarCore::initDUT(...)` function. All possible DAC names can be found in Table 5 of [the pxar manual](https://cds.cern.ch/record/2137512). If the `i2c` parameter is specified, the name will be appended with the trailing `_Cx` pattern automatically. | String | - |
| `tbmFile` | standard formatted pxar configuration file containing all register parameters for one TBM core. These values will be provided to the `pxarCore::initDUT(...)` function. All possible register names can be found in Table 4 of [the pxar manual](https://cds.cern.ch/record/2137512). The file name will
be appended with the trailing `_C0a/b` pattern for the two cores | String | - |
| `trimFile` | standard formatted pxar configuration file containing the trim bits for all 4160 pixels of the ROC. These values will be provided to the `pxarCore::initDUT(...)` function. If the `i2c` parameter is specified, the name will be appended with the trailing `_Cx` pattern automatically. | String | - |
| `maskFile` | global, standard formatted pxar configuration file containing a list of masked pixels for all ROCs attached. Pixels which appear in this list will be masked during data acquisition. Pixels have to be specified with the pattern `pix ROC COL ROW`, multiple consecutive pixels in the same column can be masked using `pix ROC COL ROW1:ROW2` | String | - |
| `external_clock` | Boolean switch to select running on externally supplied clock (via the DTB LEMO connector, see Section 3.1 of [the pxar manual](https://cds.cern.ch/record/2137512)) or the DTB-internally generated clock. This calls the function `pxarCore::setExternalClock(bool enable)`. If no external clock is present but requested, the producer will return with an error requiring reconfiguration. | Boolean | `true` |
| `trigger source` | String literal to select the trigger source to be set up in the DTB. It is also possible to activate more than one trigger source by concatenating them using the semicolon `;` as separator. The trigger sources are configured via the API function `pxarCore::daqTriggerSource(std::string src)``. A full list of available trigger sources and their description can be found in Table 6 of [the pxar manual](https://cds.cern.ch/record/2137512). | String | `extern` |
| `usbId` | USB identification string of the DTB to be connected. It is recommended to always specify this parameter instead of supplying the wildcard `*`. This is needed in the pxarCore constructor. | String | `*` |
| `hubid` | Hub address the DUT is attached to. See Section 5.1.2 of [the pxar manual](https://cds.cern.ch/record/2137512) for more information. This value is required by `pxarCore::initDUT(...)` | Integer | 31 |
| `signalprobe_d1/d2/a1/a2` | Expects a string literal as value. Allows setting the DTB LEMO outputs to the selected signal. For more information see Section 3.1 of [the pxar manual](https://cds.cern.ch/record/2137512). The default setting (no parameter given) is off. A full list of available signal outputs it given in Table 7 of the manual. | String | - |
| `vd/va/id/ia` | Mandatory parameters representing the DTB current limits (ia,id) and the supply voltage for the attached DUT (va,vd). These parameters are passed to the function `pxarCore::initTestboard(...)`` at the initial configuration stage. More detailed information can be found in Section 5.1.1 of [the pxar manual](https://cds.cern.ch/record/2137512). | Floating point number | - | 1.8, 2.5, 1.1 and 1.1, respectively
| `clk/ctr/sda/tin` | Phase settings for DTB output signals. A more detailed description is given in Section 5.1.1 of [the pxar manual](https://cds.cern.ch/record/2137512). | Integer | 4, 4, 19 and 9, respectively |
| `level` | Signal gain of the above signals, with 0 being off and 15 being maximum gain. Section 5.1.1 of [the pxar manual](https://cds.cern.ch/record/2137512) provides more information on these configuration parameters. | Integer | 15 |
| `deser160phase` | Relative phase of the 160 MHz deserializer module clock to the 40 MHz clock. More information can be found in Section 3.2 of [the pxar manual](https://cds.cern.ch/record/2137512) | Integer | 4 |
| `triggerlatency` | Additional delay for the trigger to match the overall trigger latency including WBC. This setting can be used to match the actual trigger latency from the trigger logic unit (TLU) and cabling to the ROC’s WBC setting and thus allows to run with different WBC settings. | Integer | 86 |
| `tindelay` | ADC DAQ only (analog PSI46v2 chips): delay for the ADC to start sampling the incoming data after the token in has been sent out. For more information see Section 5.11 of [the pxar manual](https://cds.cern.ch/record/2137512). | Integer | 13 |
| `toutdelay` | ADC DAQ only (analog PSI46v2 chips): delay for the ADC to stop sampling the incoming data after the token out from the DUT has been received back. For more information see Section 5.11 of [the pxar manual](https://cds.cern.ch/record/2137512). | Integer | 8 |
| `testpulses` | Boolean parameter which allows to run the DUT with testpulses and the pattern generator instead of external triggers. The trigger source parameter
has to be set accordingly. In addition, the delays in 40 MHz clock cycles after the different signals contained in the pattern generator setup can be changed using
the parameters `resetroc`/`calibrate`/`trigger`/`token`. The overall delays between two calls of the pattern generator (so the rough overall trigger frequency) can
be adjusted using the patternDelay parameter. The testpulses functionality is mainly intended for software development with no actual particle beam present.
More information on the pattern generator can be found in Section 3.4 of [the pxar manual](https://cds.cern.ch/record/2137512) | Boolean | `false` |
| `rocresetperiod` | Parameter allowing to send a periodic reset signal to the ROC. The value is given in Milliseconds, a value of 0 turns the periodic reset off. Internally this uses the direct signal trigger mode, switching on this source in addition to the one selected by the trigger source parameter. However, there is no guarantee that the two signals will not coincide, and some triggers might get lost while sending the reset. This leads to a loss of synchronization between the DUT and other detectors in the DAQ. This feature should be used with caution and only when really necessary! | Integer | 0 |

In addition to the above parameters, it is also possible to overwrite DAC parameters. This is useful in cases when several DAC files (e.g. with different threshold settings) have been prepared in the laboratory beforehand, but the WBC is only known at time of the test beam. Instead of changing this parameter in all DAC files which is error prone and cumbersome, the DAC in question can be set as parameter in the EUDAQ configuration file. A list of all possible DAC parameters can be found in Table 5 of [the pxar manual](https://cds.cern.ch/record/2137512). To overwrite a DAC parameter, its name and the desired value have to be specified
in lower case in the configuration file, e.g.

```toml
wbc = 186
```

First, all parameters from the DAC file are read in, and then their values are updated and potentially overwritten by settings from the global configuration file. It has to be noted that only DACs present in the DAC file will be updated, while DACs missing from the file will not be taken into account even if specified in the configuration file. In case a DAC parameter has been overwritten by a configuration file setting, this will be noted in the logs.