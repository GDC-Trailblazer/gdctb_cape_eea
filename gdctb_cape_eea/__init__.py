# see license/LICENSE.rst
import os
from pathlib import Path

try:
    from ._version import version as __version__
    from ._version import version_tuple
except ImportError:
    __version__ = "unknown version"
    version_tuple = (0, 0, "unknown version")

import swxsoc
from swxsoc import print_config

# Force the mission environment variable and reconfigure regardless of import order
os.environ["SWXSOC_MISSION"] = "GDCTB"
swxsoc._reconfigure()

# Load user configuration
config = swxsoc.config

log = swxsoc.log

# Then you can be explicit to control what ends up in the namespace,
__all__ = ["config", "print_config"]

_package_directory = Path(__file__).parent
_data_directory = _package_directory / "data"
_test_files_directory = _package_directory / "data" / "test"
_calibration_directory = _data_directory / "calibration"

log.debug(f"gdctb_cape_eea version: {__version__}")

MISSION_NAME = "GDCTB"
INSTRUMENT_NAME = "cape_eea"

# NOTE: kept as "eea" (not INSTRUMENT_NAME) because the EEA science/calibration file
# naming convention ported from hermes_eea (e.g. GDCTB_EEA_l0_*.bin) still encodes
# "eea" as the instrument field; see parse_science_filename().
INST_NAME = "eea"
INST_SHORTNAME = "eea"
INST_TARGETNAME = "EEA"
INST_FULLNAME = "Electron Electrostatic Analyzer"
INST_TO_SHORTNAME = {INST_NAME: INST_SHORTNAME}
INST_TO_TARGETNAME = {INST_NAME: INST_TARGETNAME}

# The installed swxsoc package does not (yet) ship a "GDCTB" entry in its default
# missions_data config, so config["mission"]["inst_*"] come back empty and
# swxsoc.util.util.parse_science_filename()/create_science_filename() would reject
# every GDCTB_EEA_* filename. Register this instrument directly so filename
# validation works regardless of which swxsoc config.yml happened to be loaded.
# The registry key must be INST_NAME ("eea"), not INSTRUMENT_NAME, since that is
# what the ported hermes_eea calibration code compares file_metadata["instrument"] against.
if not config["mission"]["inst_names"]:
    config["mission"].update(
        {
            "file_extension": ".cdf",
            "inst_names": [INST_NAME],
            "inst_shortnames": [INST_SHORTNAME],
            "inst_fullnames": [INST_FULLNAME],
            "inst_targetnames": [INST_TARGETNAME],
            "inst_to_shortname": dict(INST_TO_SHORTNAME),
            "inst_to_fullname": {INST_NAME: INST_FULLNAME},
            "inst_to_targetname": dict(INST_TO_TARGETNAME),
        }
    )

FirstStepperTable = "flight_stepper.txt"


def getCalibrationDirectory():
    return _calibration_directory
