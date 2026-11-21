from pathlib import Path

import pytest

from gdctb_cape_eea.stepper.StepperTable import CURRENT_STEPPER_TABLE_FILE

TEST_PROCESSING = [
    "20261014040843395730000_boot.bin",
    "gdctb_cape-eea_265_20261015-234049_v0.bin",
    "20261014040843395730000_boot_btabsel_2.bin",
    # "gdctb_cape-eea_260_2026161-142203_v0.bin",
    "20261014040843395730000_boot_btabsel_1.bin",
    "gdctb_cape-eea_260_2026161-132236_v0.bin",
    "gdctb_cape-eea_265_2026161-132237_v0.bin",
    "gdctb_cape-eea_265_2026023-000000_v0.bin",
]


def pytest_addoption(parser):
    parser.addoption(
        "--debug-cdf",
        metavar="DIR",
        help="Copy generated test CDF files to this existing directory.",
    )


@pytest.fixture
def debug_cdf_dir(request):
    directory = request.config.getoption("--debug-cdf")
    if directory is None:
        return None
    directory = Path(directory)
    if not directory.is_dir():
        raise pytest.UsageError(f"--debug-cdf requires an existing directory: {directory}")
    return directory


@pytest.fixture(autouse=True, scope="session")
def seed_boot_packet():
    """Seed CURRENT_STEPPER_TABLE_FILE ("boot_packet.txt") with a known-good default stepper
    table name before any test runs.

    Production code only ever creates this file as a side effect of processing a boot-packet
    TEST_PROCESSING entry (see calib.store_boot_packet), via a bare relative path resolved
    against whatever directory the process happens to run from. That means tests that need a
    stepper table (e.g. verify_l1a's get_stepper_table_for_file call) would fail with a
    FileNotFoundError unless an earlier test in the same run order happened to populate it
    first. Writing a default here makes the file available regardless of test order,
    filtering, or isolation. Tests that do process a real boot-packet entry still overwrite it
    with the real value, same as production.
    """
    CURRENT_STEPPER_TABLE_FILE.write_text("flight_stepper.csv")
