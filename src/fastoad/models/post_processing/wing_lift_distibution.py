#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
import os.path as pth
import numpy as np
import openmdao.api as om
from matplotlib import pyplot as plt

from fastoad_cs25.models.aerodynamics.external.xfoil.xfoil_polar import (
    XfoilPolar,
)

# CONSTANTS FOR THE COMPUTATION :

N_THETA = 50
PROFILE_NAME = "BACJ.txt"
ALPHA_START = -5.0
ALPHA_END = 5.0
RESULT_FOLDER_PATH = "data_xfoil"
RESULT_POLAR_FILENAME = "xfoil_results.txt"
pi = np.pi


class Xfoil(om.Group):
    def setup(self):

        self.add_subsystem(
            "xfoil_run",
            XfoilPolar(
                alpha_start=-5.0,
                alpha_end=5.0,
                result_folder_path=RESULT_FOLDER_PATH,
                result_polar_filename=RESULT_POLAR_FILENAME,
                profile_name=PROFILE_NAME,
            ),
            promotes=["*"],
        )


class Alpha0(om.ExplicitComponent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def initialize(self):
        self.options.declare("result_folder_path", types=str)
        self.options.declare("result_polar_filename", types=str)

    def setup(self):
        self.add_output("data:aerodynamics:wing_lift_distribution:alpha0", shape=N_THETA)

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):

        xfoil_data_file = pth.join(RESULT_FOLDER_PATH, RESULT_POLAR_FILENAME)
        f = open(xfoil_data_file, "r")
        lines = f.readlines()
        for line in lines:
            print(line)
        f.close()
        outputs["data:aerodynamics:wing_lift_distribution:alpha0"] = -np.ones(N_THETA)






