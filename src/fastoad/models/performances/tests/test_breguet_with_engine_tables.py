#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2020  ONERA & ISAE-SUPAERO
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

import openmdao.api as om
from numpy.testing import assert_allclose

from tests.testing_utilities import run_system
from ..breguet import BreguetFromMTOW, BreguetFromOWE
from ...propulsion.fuel_engine.rubber_engine.openmdao import RubberEngineTable


def test_breguet_from_mtow_with_rubber_engine():
    ivc = om.IndepVarComp()
    ivc.add_output("data:mission:sizing:cruise:altitude", 35000, units="ft")
    ivc.add_output("data:TLAR:cruise_mach", 0.78)
    ivc.add_output("data:TLAR:range", 500, units="NM")
    ivc.add_output("data:TLAR:NPAX", 150)
    ivc.add_output("data:aerodynamics:aircraft:cruise:L_D_max", 16.0)
    ivc.add_output("data:weight:aircraft:MTOW", 74000, units="kg")

    ivc.add_output("data:propulsion:rubber_engine:bypass_ratio", 5)
    ivc.add_output("data:propulsion:rubber_engine:maximum_mach", 0.95)
    ivc.add_output("data:propulsion:rubber_engine:design_altitude", 35000, units="ft")
    ivc.add_output("data:propulsion:MTO_thrust", 100000, units="N")
    ivc.add_output("data:propulsion:rubber_engine:overall_pressure_ratio", 30)
    ivc.add_output("data:propulsion:rubber_engine:turbine_inlet_temperature", 1500, units="K")

    group = om.Group()
    group.add_subsystem("engine", RubberEngineTable(), promotes=["*"])
    group.add_subsystem("breguet", BreguetFromMTOW(use_tables=True), promotes=["*"])
    group.nonlinear_solver = om.NonlinearBlockGS()
    problem = run_system(group, ivc)

    assert_allclose(problem["data:mission:sizing:ZFW"], 65076.0, atol=1)
    assert_allclose(problem["data:mission:sizing:fuel"], 8924.0, atol=1)
    assert_allclose(problem["data:mission:sizing:fuel:unitary"], 0.0642, rtol=1e-3)


def test_breguet_from_owe_with_rubber_engine():
    ivc = om.IndepVarComp()
    ivc.add_output("data:mission:sizing:cruise:altitude", 35000, units="ft")
    ivc.add_output("data:TLAR:cruise_mach", 0.78)
    ivc.add_output("data:TLAR:range", 500, units="NM")
    ivc.add_output("data:TLAR:NPAX", 150)
    ivc.add_output("data:aerodynamics:aircraft:cruise:L_D_max", 16.0)
    ivc.add_output("data:weight:aircraft:payload", 15076, units="kg")
    ivc.add_output("data:weight:aircraft:OWE", 50000, units="kg")

    ivc.add_output("data:propulsion:rubber_engine:bypass_ratio", 5)
    ivc.add_output("data:propulsion:rubber_engine:maximum_mach", 0.95)
    ivc.add_output("data:propulsion:rubber_engine:design_altitude", 35000, units="ft")
    ivc.add_output("data:propulsion:MTO_thrust", 100000, units="N")
    ivc.add_output("data:propulsion:rubber_engine:overall_pressure_ratio", 30)
    ivc.add_output("data:propulsion:rubber_engine:turbine_inlet_temperature", 1500, units="K")

    group = om.Group()

    group.add_subsystem("engine", RubberEngineTable(), promotes=["*"])
    group.add_subsystem("breguet", BreguetFromOWE(use_tables=True), promotes=["*"])
    problem = run_system(group, ivc)

    assert_allclose(problem["data:weight:aircraft:MTOW"], 74000.0, atol=10)
    assert_allclose(problem["data:mission:sizing:ZFW"], 65076.0, atol=1)
    assert_allclose(problem["data:mission:sizing:fuel"], 8924.0, atol=1)
    assert_allclose(problem["data:mission:sizing:fuel:unitary"], 0.0642, rtol=1e-3)
