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

from typing import Union, Sequence, Optional, Tuple

import numpy as np
import pandas as pd
import pytest
from fastoad.constants import FlightPhase
from fastoad.models.performances.mission.segment import OptimalCruiseSegment
from fastoad.models.propulsion import EngineSet, IPropulsion
from numpy.testing import assert_allclose

from ..segment import (
    Polar,
    ClimbSegment,
    AccelerationSegment,
    FlightPoint,
)


def print_dataframe(df):
    """Utility for correctly printing results"""
    # Not used if all goes all well. Please keep it for future test setting/debugging.
    with pd.option_context(
        "display.max_rows", 20, "display.max_columns", None, "display.width", None
    ):
        print()
        print(df)


class DummyEngine(IPropulsion):
    def __init__(self, max_thrust, max_sfc):
        """
        Dummy engine model.

        Max thrust does not depend on flight conditions.
        SFC varies linearly with thrus_rate, from max_sfc/2. at thrust rate is 0.,
        to max_sfc when thrust_rate is 1.0

        :param max_thrust: thrust when thrust rate = 1.0
        :param max_sfc: SFC when thrust rate = 1.0
        """
        self.max_thrust = max_thrust
        self.max_sfc = max_sfc

    def compute_flight_points(
        self,
        mach: Union[float, Sequence],
        altitude: Union[float, Sequence],
        phase: Union[FlightPhase, Sequence],
        use_thrust_rate: Optional[Union[bool, Sequence]] = None,
        thrust_rate: Optional[Union[float, Sequence]] = None,
        thrust: Optional[Union[float, Sequence]] = None,
    ) -> Tuple[Union[float, Sequence], Union[float, Sequence], Union[float, Sequence]]:

        if use_thrust_rate or thrust is None:
            thrust = self.max_thrust * thrust_rate
        else:
            thrust_rate = thrust / self.max_thrust

        sfc = self.max_sfc * (1.0 + thrust_rate) / 2.0

        return sfc, thrust_rate, thrust


@pytest.fixture
def polar() -> Polar:
    """Returns a dummy polar where max L/D ratio is around 16."""
    cl = np.arange(0.0, 1.5, 0.01)
    cd = 0.5e-1 * cl ** 2 + 0.01
    return Polar(cl, cd)


def test_FlightPoint():

    # Init with kwargs, with one attribute initialized #########################
    fp1 = FlightPoint(mass=50000.0)
    assert fp1.mass == 50000.0
    assert fp1.mass == fp1["mass"]
    fp1.mass = 70000.0
    assert fp1["mass"] == 70000.0

    # Non initialized but known attributes are initialized to None
    for label in FlightPoint.labels:
        if label != "mass":
            assert getattr(fp1, label) is None

    # Init with dictionary, with all attributes initialized ####################
    test_values = {
        key: value for key, value in zip(FlightPoint.labels, range(len(FlightPoint.labels)))
    }
    fp2 = FlightPoint(test_values)
    for label in FlightPoint.labels:
        assert getattr(fp2, label) == test_values[label]
        assert getattr(fp2, label) == fp2[label]
        new_value = test_values[label] * 100
        setattr(fp2, label, new_value)
        assert fp2[label] == new_value

    # Init with unknown attribute ##############################################
    with pytest.raises(KeyError):
        _ = FlightPoint(unknown=0)

    with pytest.raises(KeyError):
        _ = FlightPoint({"unknown": 0})

    # FlightPoint to/from pandas DataFrame #####################################
    assert fp1 == FlightPoint(pd.DataFrame([fp1]).iloc[0])

    df = pd.DataFrame([fp1, fp2])
    for label in FlightPoint.labels:
        assert_allclose(df[label], [fp1.get(label, np.nan), fp2.get(label, np.nan)])

    fp2bis = FlightPoint(df.iloc[-1])
    assert fp2 == fp2bis

    fp1bis = FlightPoint(df.iloc[0])
    assert fp1 == fp1bis


def test_ClimbSegment(polar):

    propulsion = EngineSet(DummyEngine(1.0e5, 1.0e-5), 2)

    # initialisation then change instance attributes
    segment = ClimbSegment(propulsion, polar, 120.0)
    segment.thrust_rate = 1.0
    segment.time_step = 2.0

    # Climb computation with fixed altitude target #############################
    flight_points = segment.compute(
        FlightPoint(altitude=5000.0, speed=150.0, mass=70000.0), 10000.0
    )

    last_point = flight_points.iloc[-1]
    # Note: reference values are obtained by running the process with 0.01s as time step
    assert_allclose(last_point.time, 143.5, rtol=1e-2)
    assert_allclose(last_point.altitude, 10000.0)
    assert_allclose(last_point.speed, 150.0)
    assert_allclose(last_point.mass, 69713.0, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 20943.0, rtol=1e-3)

    # Climb computation to optimal altitude ####################################
    segment.time_step = 2.0
    flight_points = segment.compute(
        FlightPoint(altitude=5000.0, speed=250.0, mass=70000.0), ClimbSegment.OPTIMAL_ALTITUDE
    )

    last_point = flight_points.iloc[-1]
    # Note: reference values are obtained by running the process with 0.01s as time step
    assert_allclose(last_point.altitude, 10085.0, atol=0.1)
    assert_allclose(last_point.time, 84.1, rtol=1e-2)
    assert_allclose(last_point.speed, 250.0)
    assert_allclose(last_point.mass, 69832.0, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 20401.0, rtol=1e-3)

    # Climb computation with too low thrust rate should fail ###################
    segment = ClimbSegment(propulsion, polar, 100.0, thrust_rate=0.1)
    with pytest.raises(ValueError):
        segment.time_step = 5.0  # Let's fail quickly
        flight_points = segment.compute(
            FlightPoint(altitude=5000.0, speed=150.0, mass=70000.0), 10000.0
        )

    # Descent computation ######################################################
    segment.time_step = 2.0

    flight_points = segment.compute(
        FlightPoint(altitude=10000.0, speed=200.0, mass=70000.0, time=2000.0), 5000.0
    )  # And we define a start time

    last_point = flight_points.iloc[-1]
    # Note: reference values are obtained by running the process with 0.01s as time step
    assert_allclose(last_point.time, 3370.4, rtol=1e-2)
    assert_allclose(last_point.altitude, 5000.0)
    assert_allclose(last_point.speed, 200.0)
    assert_allclose(last_point.mass, 69849.0, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 274043.0, rtol=1e-3)


def test_AccelerationSegment(polar):
    propulsion = EngineSet(DummyEngine(0.5e5, 1.0e-5), 2)

    # initialisation using kwarg
    segment = AccelerationSegment(propulsion, polar, 120.0, thrust_rate=1.0, time_step=0.2)

    # Acceleration computation #################################################
    flight_points = segment.compute({"altitude": 5000.0, "speed": 150.0, "mass": 70000.0}, 250.0)

    last_point = flight_points.iloc[-1]
    # Note: reference values are obtained by running the process with 0.01s as time step
    assert_allclose(last_point.time, 103.3, rtol=1e-2)
    assert_allclose(last_point.altitude, 5000.0)
    assert_allclose(last_point.speed, 250.0)
    assert_allclose(last_point.mass, 69896.0, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 20697.0, rtol=1e-3)

    # Acceleration computation with too low thrust rate should fail ############
    segment.thrust_rate = 0.1
    with pytest.raises(ValueError):
        segment.time_step = 5.0  # Let's fail quickly
        flight_points = segment.compute(
            {"altitude": 5000.0, "speed": 150.0, "mass": 70000.0}, 250.0
        )

    # Deceleration computation #################################################
    segment.time_step = 1.0
    flight_points = segment.compute({"altitude": 5000.0, "speed": 250.0, "mass": 70000.0}, 150.0)
    print_dataframe(flight_points)

    last_point = flight_points.iloc[-1]
    # Note: reference values are obtained by running the process with 0.01s as time step
    assert_allclose(last_point.time, 315.8, rtol=1e-2)
    assert_allclose(last_point.altitude, 5000.0)
    assert_allclose(last_point.speed, 150.0)
    assert_allclose(last_point.mass, 69982.0, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 62804.0, rtol=1e-3)


def test_Cruise(polar):
    propulsion = EngineSet(DummyEngine(0.5e5, 1.0e-5), 2)

    segment = OptimalCruiseSegment(propulsion, polar, 120.0, cruise_mach=0.78, time_step=60.0)
    flight_points = segment.compute(
        FlightPoint(mass=70000.0, time=1000.0, ground_distance=1e5), 5.0e5
    )

    first_point = flight_points.iloc[1]
    last_point = FlightPoint(flight_points.iloc[-1])
    # Note: reference values are obtained by running the process with 0.05s as time step
    assert_allclose(first_point.altitude, 9156.0, atol=1.0)
    assert_allclose(first_point.speed, 236.4, atol=0.1)

    assert_allclose(last_point.altitude, 9196.0, atol=1.0)
    assert_allclose(last_point.time, 3115.0, rtol=1e-2)
    assert_allclose(last_point.speed, 236.3, atol=0.1)
    assert_allclose(last_point.mass, 69577.0, rtol=1e-4)
    assert_allclose(last_point.ground_distance, 600000.0)
