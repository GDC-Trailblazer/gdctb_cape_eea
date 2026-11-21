import csv
import struct
from pathlib import Path

from astropy.time import Time
from astropy.timeseries import TimeSeries
from ccsdspy import FixedLength
from ccsdspy.utils import read_primary_headers

import gdctb_cape_eea
from gdctb_cape_eea.util.time import ccsds_to_cdf_time

"""
This module provides a generic file reader.
"""

__all__ = [
    "get_apid_for_file",
    "is_ascii_file",
    "is_boot_packet",
    "read_ccsds",
    "read_raw_hk",
]


def _peek_apid(data_filename: Path) -> int:
    """Read the CCSDS APID out of the first packet's primary header (its first 2
    bytes), without needing to know which packet definition (sci vs hk) applies yet.
    """
    with open(data_filename, "rb") as fh:
        header = fh.read(2)
    if len(header) < 2:
        raise ValueError(
            f"{data_filename} is too short to contain a CCSDS primary header."
        )
    first_word = struct.unpack(">H", header)[0]
    return first_word & 0x07FF


def get_apid_for_file(data_filename) -> int:
    """Look up the CCSDS APID that applies to a given registered L0 input file."""
    try:
        return _peek_apid(data_filename)
    except OSError as err:
        raise OSError(f"Could not read input file {data_filename!r}: {err}") from err
    except ValueError as err:
        raise ValueError(
            f"Could not determine APID for input file {data_filename!r}: {err}"
        ) from err


def is_ascii_file(file_path, block_size=1024):
    """Returns True if the file contains only valid 7-bit ASCII characters."""
    try:
        with open(file_path, "rb") as f:
            block = f.read(block_size)

            # A null byte means it is a binary file, not ASCII text
            if b"\x00" in block:
                return False

            # ASCII characters only use byte values from 0 to 127
            return not any(byte > 127 for byte in block)
    except OSError:
        print(f"Error: Could not read file {file_path}")
        return False


def is_boot_packet(file_path):
    """Returns True if the file is a boot packet (ASCII text), False otherwise."""
    if is_ascii_file(file_path):
        return True  # we have both ascii and binary boot packets
    apid = get_apid_for_file(file_path)
    return apid == 266


def read_ccsds(filename: Path, pkt_def: FixedLength):
    """
    Read a ccsds packet file.

    Parameters
    ----------
    filename: `pathlib.Path`
        A file to read.

    pkt_def: `ccsdspy.FixedLength`
        CCSDS packet definition

    Returns
    -------
    `OrderedDict` mapping field names to NumPy arrays.
    """
    result = pkt_def.load(filename)
    return result


def _read_hk_fill_field_names() -> set[str]:
    """Find fill fields, whose decoded sub-byte values may include neighboring bits."""
    csv_path = gdctb_cape_eea._data_directory / "gdctb_cape-eea_hk_packet_def.csv"
    with csv_path.open(newline="") as fp:
        reader = csv.DictReader(fp, skipinitialspace=True)
        return {
            row["name"].strip()
            for row in reader
            if row["data_type"].strip().lower() == "fill"
        }


def read_raw_hk(filename: str | Path) -> TimeSeries:
    """Read an APID 265 housekeeping file into an Astropy time series.

    The time column uses the same CCSDS-to-UTC conversion as the L1 CDF
    pipeline. Other columns contain raw, uncalibrated packet fields, including
    CCSDS primary headers; fill fields are omitted.

    Raises
    ------
    ValueError
        If the file contains no packets or packets with other APIDs.
    """
    from spacepy.pycdf import lib

    filename = Path(filename)
    if filename.stat().st_size == 0:
        raise ValueError(f"Expected housekeeping packets in {filename}; file is empty")
    headers = read_primary_headers(str(filename))
    apids = set(headers["CCSDS_APID"].tolist())
    if apids != {265}:
        raise ValueError(
            f"Expected only housekeeping APID 265 in {filename}; found {sorted(apids)}"
        )

    definition = gdctb_cape_eea._data_directory / "gdctb_cape-eea_hk_packet_def.csv"
    packets = FixedLength.from_file(definition).load(
        filename, include_primary_header=True
    )
    epochs = ccsds_to_cdf_time.convert_ccsds_times_to_cdf(packets)
    times = Time([lib.tt2000_to_datetime(epoch) for epoch in epochs])
    fill_fields = _read_hk_fill_field_names()
    columns = {name: values for name, values in packets.items() if name not in fill_fields}
    return TimeSeries(time=times, data=columns)
