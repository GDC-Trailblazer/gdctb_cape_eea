import os
import gdctb_cape_eea
from pathlib import Path
from gdctb_cape_eea.io.file_tools import read_file
from gdctb_cape_eea.Stepper.StepperTable import StepperTable
from pathlib import Path
import pytest


def test_read_file():
    assert read_file("./gdctb_cape_eea/data/calibration/flight_stepper.txt") is not None


@pytest.fixture(scope="session")  # this is a pytest fixture
def first_stepper_file(tmp_path_factory):
    fn = Path(os.path.join(gdctb_cape_eea.FirstStepperTable))
    return fn


def test_characterize_stepper(first_stepper_file):
    stepper = StepperTable(first_stepper_file)
    assert len(stepper.energies) == 164
