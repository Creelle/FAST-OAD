#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import numpy as np
import openmdao.api as om
from fastoad.module_management.constants import ModelDomain
from fastoad.module_management.service_registry import RegisterOpenMDAOSystem, RegisterSubmodel

from fastoad_cs25.models.aerodynamics.external.xfoil.xfoil_polar import (
    XfoilPolar,
    OPTION_RESULT_FOLDER_PATH,
    OPTION_RESULT_POLAR_FILENAME,
    OPTION_ALPHA_START,
    OPTION_ALPHA_END,
)
from fastoad_cs25.models.aerodynamics.constants import SERVICE_XFOIL

# CONSTANTS FOR THE COMPUTATION :

N_THETA = 50
PROFILE_NAME = "BACJ.txt"
ALPHA_START = -5.0
ALPHA_END = 5.0
RESULT_FOLDER_PATH = (
    "C:/Users/robbe/PycharmProjects/FAST-OAD/src/fastoad/models/post_processing/data"
)
RESULT_POLAR_FILENAME = "xfoil_results.txt"


class TestXfoil(om.Group):
    def setup(self):
        self.add_subsystem(
            "xfoil_run",
            XfoilPolar(
                alpha_start=-5.0,
                alpha_end=5.0,
                result_folder_path=RESULT_FOLDER_PATH,
                result_polar_filename=RESULT_POLAR_FILENAME,
            ),
            promotes=["*"],
        )
        self.add_subsystem(
            "wing",
            WingLiftDistribution(
                result_folder_path=RESULT_FOLDER_PATH, result_polar_filename=RESULT_POLAR_FILENAME
            ),
        )


class WingLiftDistribution(om.ExplicitComponent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def initialize(self):

        self.options.declare("result_folder_path", types=str)
        self.options.declare("result_polar_filename", types=str)

    def setup(self):
        self.add_output("data:aerodynamics:wing_lift_distribution:alpha0", shape=N_THETA)

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):
        # result_folder = self.options("result_folder_path")
        outputs["data:aerodynamics:wing_lift_distribution:alpha0"] = -np.ones(N_THETA)

    def add_subsystem(self, param, param1, promotes):
        pass
