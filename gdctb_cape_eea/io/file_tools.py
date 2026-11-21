from pathlib import Path
import struct
from ccsdspy import FixedLength

"""
This module provides a generic file reader.
"""

__all__ = ["read_ccsds", "is_boot_packet", "get_apid_for_file", "is_ascii_file"]


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
