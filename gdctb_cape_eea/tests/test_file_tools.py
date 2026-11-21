import csv
from pathlib import Path

import numpy as np
import pytest
from astropy.table import Table
from astropy.timeseries import TimeSeries
from ccsdspy.utils import iter_packet_bytes

import gdctb_cape_eea
from gdctb_cape_eea.io import read_raw_hk
from gdctb_cape_eea.stepper.stepper_table import StepperTable, validate_stepper_table


def test_read_raw_hk():
    filename = (
        gdctb_cape_eea._test_files_directory
        / "gdctb_cape-eea_265_2026161-132237_v0.bin"
    )
    result = read_raw_hk(filename)

    assert isinstance(result, TimeSeries)
    assert len(result) == 2405
    assert result.time[0].isot == "2000-01-01T12:01:20.000"
    assert result.time[0].datetime.microsecond == 124
    assert result["CCSDS_APID"][0] == 265
    assert result["SHCOARSE"][0] == 80
    assert result["SHFINE"][0] == 124
    assert result["T_FEE"][0] == 3515
    assert result["V_5_7V"][0] == 6641
    assert result["ANODE_V"][0] == 32771
    assert "SHFILL" not in result.colnames
    assert "FILL" not in result.colnames


@pytest.mark.parametrize("include_hk", [False, True])
def test_read_raw_hk_rejects_non_hk_packets(tmp_path, include_hk):
    test_dir = gdctb_cape_eea._test_files_directory
    boot = next(iter_packet_bytes(str(test_dir / "20261014040843395730000_boot.bin")))
    content = boot
    if include_hk:
        hk = next(
            iter_packet_bytes(str(test_dir / "gdctb_cape-eea_265_2026161-132237_v0.bin"))
        )
        content = hk + boot
    filename = tmp_path / "packets.bin"
    filename.write_bytes(content)

    with pytest.raises(ValueError, match="Expected only housekeeping APID 265"):
        read_raw_hk(filename)


def test_read_raw_hk_rejects_empty_file(tmp_path):
    filename = tmp_path / "empty.bin"
    filename.touch()

    with pytest.raises(ValueError, match="file is empty"):
        read_raw_hk(filename)


def test_read_cpt_stepper_file():
    lines = (gdctb_cape_eea._calibration_directory / "cpt_stepper.csv").read_text().splitlines()

    assert len(lines) == 165
    assert lines[0].strip() == "energy,deflection"
    assert lines[1].strip() == "0.049230224,16.875"
    assert lines[33].strip() == "34.95603837,16.875"
    assert lines[-1].strip() == "0.049230224,-16.875"


@pytest.fixture(scope="session")  # this is a pytest fixture
def first_stepper_file(tmp_path_factory):
    fn = Path("flight_stepper.csv")
    return fn


def test_characterize_stepper(first_stepper_file):
    stepper = StepperTable(first_stepper_file)
    assert len(stepper.energies) == 164


@pytest.mark.parametrize(
    ("filename", "row_count"),
    [
        ("cpt_stepper.csv", 164),
        ("flight_stepper.csv", 164),
        ("ptb_esastepped_deflected_stepper.csv", 64),
        ("ptb_esastepped_undeflected_stepper.csv", 64),
    ],
)
def test_parse_stepper_table(filename, row_count):
    with (gdctb_cape_eea._calibration_directory / filename).open(newline="") as file:
        rows = list(csv.DictReader(file))
    expected_energies = [float(row["energy"]) for row in rows]
    expected_deflections = [float(row["deflection"]) for row in rows]

    stepper = StepperTable(Path(filename))

    assert len(rows) == row_count
    assert isinstance(stepper.table, Table)
    assert stepper.table.colnames == ["energy", "deflection"]
    np.testing.assert_array_equal(stepper.table["energy"], expected_energies)
    np.testing.assert_array_equal(stepper.table["deflection"], expected_deflections)
    np.testing.assert_array_equal(stepper.energies, expected_energies)
    np.testing.assert_array_equal(stepper.deflections, expected_deflections)


@pytest.mark.parametrize(
    "stepper_table_file",
    ["flight_stepper.csv", "ptb_esastepped_undeflected_stepper.csv"],
)
def test_validate_stepper_table_passes(stepper_table_file):
    stepper = StepperTable(stepper_table_file)
    assert validate_stepper_table(stepper) == []


def test_validate_stepper_table_catches_swapped_columns():
    stepper = StepperTable("flight_stepper.csv")
    # Deliberately swap the parsed columns to simulate a mis-parsed/malformed file.
    stepper.energies, stepper.deflections = stepper.deflections, stepper.energies
    issues = validate_stepper_table(stepper)
    assert issues != []
    assert any("may be swapped" in issue for issue in issues)


def test_validate_stepper_table_catches_empty_table():
    stepper = StepperTable("flight_stepper.csv")
    stepper.energies = []
    stepper.deflections = []
    issues = validate_stepper_table(stepper)
    assert issues == ["Stepper table has no parsed energy/deflection rows."]


def test_stepper_table_raises_on_swapped_columns_file(tmp_path, monkeypatch):
    # Write a stepper table file with the energy/deflection columns swapped:
    # a small, repeated set of deflection-sized values in the energy column,
    # and large, mostly-unique, energy-sized values in the deflection column.
    # Confirm StepperTable() rejects it automatically at construction time,
    # rather than silently loading it.
    defl_like_values = [-16.875, -5.625, 5.625, 16.875]
    bad_table = tmp_path / "swapped_stepper.csv"
    bad_table.write_text(
        "energy,deflection\n"
        + "\n".join(
            f"{defl_like_values[i % len(defl_like_values)]}, {100.0 + i}"
            for i in range(50)
        )
    )
    monkeypatch.setattr(gdctb_cape_eea, "_calibration_directory", tmp_path)

    with pytest.raises(ValueError, match="failed validation"):
        StepperTable("swapped_stepper.csv")
