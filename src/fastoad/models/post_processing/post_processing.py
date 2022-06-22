"""Computation of the Altitude-Speed diagram."""
#  This file is part of FAST-OAD : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2021 ONERA & ISAE-SUPAERO
#  FAST is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

from .wing_lift_distibution import Alpha0, Xfoil

import openmdao.api as om
import fastoad.api as oad

import numpy as np

@oad.RegisterOpenMDAOSystem("fastoad.postprocessing.belgian_legacy")
class PostProcessing(om.Group):
    def initialize(self):
        self.options.declare("propulsion_id", default="", types=str)

    def setup(self):
        self.add_subsystem(
            "xfoil_run",
            Xfoil(),
            promotes=["*"],
        )

        self.add_subsystem(
            "alpha0",
            Alpha0(),
            promotes=["*"],
        )
