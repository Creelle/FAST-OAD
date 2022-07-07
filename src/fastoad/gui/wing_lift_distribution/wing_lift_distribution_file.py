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
import plotly
import plotly.graph_objects as go
from openmdao.utils.units import convert_units
from plotly.subplots import make_subplots


from fastoad.constants import EngineSetting
from fastoad.io import VariableIO
from fastoad.model_base import FlightPoint
from stdatm import Atmosphere
from fastoad.openmdao.variables import VariableList

COLS = plotly.colors.DEFAULT_PLOTLY_COLORS
pi = np.pi

def wing_lift_distribution_plot(
    aircraft_file_path: str,
    name=None,
    fig=None,
    file_formatter=None,
    alpha: float = 5.0,
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
                           default format will be assumed
    :param alpha: AoA considered for the lift distribution. Default is 5°
    :param x_axis: defines the x axis if the user wants to
    :param y_axis: defines the y axis if the user wants to
    :param color : defines the color of the graph
    :return: plot of the payload-range diagram with the points calculated using breguet-leduc formula
    """
    variables = VariableIO(aircraft_file_path, file_formatter).read()

    wing_tip_leading_edge_x_local = variables["data:geometry:wing:tip:leading_edge:x:local"].value[0]
    wing_root_y = variables["data:geometry:wing:root:y"].value[0]
    wing_kink_y = variables["data:geometry:wing:kink:y"].value[0]
    wing_tip_y = variables["data:geometry:wing:tip:y"].value[0]
    wing_root_chord = variables["data:geometry:wing:root:chord"].value[0]
    wing_tip_chord = variables["data:geometry:wing:tip:chord"].value[0]

    alpha0 = variables["data:aerodynamics:wing_lift_distribution:alpha0"].value
    span = variables["data:geometry:wing:span"].value[0]
    aspect_ratio = variables["data:geometry:wing:aspect_ratio"].value[0]

    #sweep
    sweep_25 = variables["data:geometry:wing:sweep_25"].value[0]


    def leading_edge_x(y: float):
        slope = wing_tip_leading_edge_x_local / (wing_tip_y - wing_root_y)
        return slope * (y - wing_root_y)

    def trailing_edge_x(y: float):
        if y < wing_kink_y:
            return wing_root_chord
        else:
            slope = (wing_tip_leading_edge_x_local + wing_tip_chord - wing_root_chord) / (
                wing_tip_y - wing_kink_y
            )
            return slope * (y - wing_kink_y) + wing_root_chord

    n = len(alpha0)
    theta = np.linspace(pi / 2, pi * n / (n + 1), n)
    z = -span / 2 * np.cos(theta)
    chord = np.zeros(len(theta))
    for i in range(n):
        chord[i] = trailing_edge_x(z[i]) - leading_edge_x(z[i])
    # chord = np.interp(z, [wing_root_y, wing_tip_y], [wing_root_chord, wing_tip_chord ])

    # Set up the system K A  = L : A unknown
    alpha = alpha * pi / 180 * np.ones(n)
    alpha0 = np.asarray(alpha0) * pi / 180
    delta_vrillage = -4.0 * pi / 180 / n

    alpha_vrillage = np.zeros(n)
    for i in range(n):
        alpha_vrillage[i] = delta_vrillage * i

    K = np.zeros([n, n])
    for i in range(n):  # seuls les A impairs sont nuls
        K[:, i] = np.sin((2 * i + 1) * theta) * (
            1 + pi * chord / (4 * span) * (2 * i + 1) / np.sin(theta)
        )

    L = pi / (4 * span) * chord * (alpha + alpha_vrillage - alpha0)
    A = np.linalg.solve(K, L)

    cl_global = pi * aspect_ratio * A[0]
    gamma = np.zeros(n)
    for i in range(n):
        for j in range(n):
            gamma[i] += A[j] * np.sin((2 * j + 1) * theta[i])
    cl_local = 4 * span / chord * gamma * np.cos(sweep_25*pi/180)

    # Figure
    if fig is None:
        fig = go.Figure()

    scatter = go.Scatter(x=z, y=cl_local / cl_global, mode="lines",marker_color=color,name = name)

    fig.add_trace(scatter)

    fig = go.FigureWidget(fig)
    fig.update_layout(
        title_text= name, xaxis_title="span [m]", yaxis_title="$Cl_{2D}/CL_{3D}$"
    )

    if x_axis is not None:
        fig.update_xaxes(range=[x_axis[0], x_axis[1]])
    if y_axis is not None:
        fig.update_yaxes(range=[y_axis[0], y_axis[1]])

    fig2 = go.Figure()
    f=open("data/boeing_airfoil.dat","r")
    lines = f.readlines()[1:]
    f.close()

    x_airfoil = np.zeros(len(lines))
    y_airfoil = np.zeros(len(lines))
    counter = 0
    for line in lines:
        string_table = line.split(" ")

        if counter < len(lines)/2 :
            x_airfoil[counter] = float(string_table[2])
            y_airfoil[counter] = float(string_table[4])
        else :
            x_airfoil[counter] = float(string_table[2])
            y_airfoil[counter] = float(string_table[3])

        counter += 1
        #print(string_table)
    scatter = go.Scatter(x=x_airfoil,y=y_airfoil,mode="lines",name = "BACJ airfoil",fill='tonexty')
    fig2.add_trace(scatter)

    fig2.update_layout(
        xaxis_title="x", yaxis_title="y"
    )
    fig2.update_yaxes(scaleanchor="x", scaleratio=1)





    return fig,fig2
