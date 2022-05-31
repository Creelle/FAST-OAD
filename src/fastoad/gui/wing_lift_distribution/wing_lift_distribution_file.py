"""
Defines the analysis and plotting functions for postprocessing
"""
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

from typing import Dict

import numpy as np
import pandas as pd
import plotly
import plotly.graph_objects as go
from openmdao.utils.units import convert_units
from plotly.subplots import make_subplots
from scipy.optimize import fsolve

from fastoad.constants import EngineSetting
from fastoad.io import VariableIO
from fastoad.model_base import FlightPoint
from stdatm import Atmosphere
from fastoad.openmdao.variables import VariableList


import fastoad.api as oad
import os.path as pth
import time

COLS = plotly.colors.DEFAULT_PLOTLY_COLORS


def wing_lift_distribution_plot(
        aircraft_file_path: str,
        name=None,
        fig=None,
        file_formatter=None,
        x_axis=None,
        y_axis=None,
        color="black",
) -> go.FigureWidget:
    """
    Returns a figure of the lift distribution on the wing along the y coordinate
    Different designs can be superposed by providing an existing fig.
    Each design can be provided a name.

    :param aircraft_file_path: path of data file
    :param name: name to give to the trace added to the figure
    :param fig: existing figure to which add the plot
    :param file_formatter: the formatter that defines the format of data file. If not provided,
                           default format will be assumed.
    :param x_axis: defines the x axis if the user wants to
    :param y_axis: defines the y axis if the user wants to
    :param color : defines the color of the graph
    :return: plot of the payload-range diagram with the points calculated using breguet-leduc formula
    """

    # Figure :
    if fig is None:
        fig = go.Figure()

    fig = go.FigureWidget(fig)
    fig.update_layout(
        title_text=name, xaxis_title="x", yaxis_title="y"
    )

    if x_axis is not None:
        fig.update_xaxes(range=[x_axis[0], x_axis[1]])
    if y_axis is not None:
        fig.update_yaxes(range=[y_axis[0], y_axis[1]])

    return fig
