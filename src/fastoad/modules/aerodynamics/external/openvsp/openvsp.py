"""
    FAST - Copyright (c) 2016 ONERA ISAE
"""
#  This file is part of FAST : A framework for rapid Overall Aircraft Design
#  Copyright (C) 2019  ONERA/ISAE
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

import multiprocessing
import os
import os.path as pth

import win32event
import win32process
from openmdao.core.explicitcomponent import ExplicitComponent

from fastoad.utils.physics import Atmosphere

_WING_GEOMETRY_PARAMETERS = ['l0', 'span', 'area', 'l2', 'y2', 'l3', 'x3', 'y3', 'l4', 'x4', 'y4']
_VSPSCRIPT_NAME = 'wing_openvsp.script'  # name of the resource file
_RESOURCE_FOLDER_PATH = pth.join(pth.dirname(__file__), 'resources')


# class OpenVSPGeom(ExternalCodeComp):
#     def initialize(self):
#         self.options.declare('openvsp_exe_path', types=str)
#         self.options.declare('result_folder_path', default='', types=str)
#
#     def setup(self):
#         self.add_input('geometry:wing_l2', val=np.nan, units='m')
#         self.add_input('geometry:wing_y2', val=np.nan, units='m')
#         self.add_input('geometry:wing_l3', val=np.nan, units='m')
#         self.add_input('geometry:wing_x3', val=np.nan, units='m')
#         self.add_input('geometry:wing_y3', val=np.nan, units='m')
#         self.add_input('geometry:wing_l4', val=np.nan, units='m')
#         self.add_input('geometry:wing_x4', val=np.nan, units='m')
#         self.add_input('geometry:wing_y4', val=np.nan, units='m')
#         self.add_input('geometry:wing_area', val=np.nan, units='m**2')
#         self.add_input('geometry:wing_span', val=np.nan, units='m')
#         self.add_input('geometry:wing_l0', val=np.nan, units='m')
#
#     def compute(self, inputs, outputs):
#         tmp_directory = tempfile.TemporaryDirectory(prefix='openvsp')
#
#         wing_geometry = {param_name: inputs['geometry:%s' % param_name]
#                          for param_name in _WING_GEOMETRY_PARAMETERS}
#
#         template_vspscript_path = pth.join(_RESOURCE_FOLDER_PATH, _VSPSCRIPT_NAME)
#         tmp_vspscript_path = pth.join(tmp_directory, _VSPSCRIPT_NAME)
#
#         self._generate_vspscript(template_vspscript_path, tmp_vspscript_path, wing_geometry)
#
#     def _generate_vspscript(self, template_path, script_path, wing_geometry):
#
#         parser = InputFileGenerator()
#         parser.set_template_file(template_path)
#         parser.set_generated_file(script_path)
#         parser.mark_anchor('LOAD')
#         parser.transfer_var(tmp_profile_file_path, 1, 1)
#         parser.generate()
#
# class WingGeometry
#

class OpenVSP(ExplicitComponent):
    """Wrapper for OpenVSP tool: see http://www.openvsp.org/

    Class Attributes:
        vspscript_exe: OpenVSP script executable name
        vspaero_exe: OpenVSP vspareo executable name
        vspscript_filename: input file for OpenVSP script
        vspaero_filename: setup file for OpenVSP vspareo tool
        result_filename: openvsp result file
        takeoff_result_filename: openvsp result file when takeoff run option is enabled

    Attributes:
        aircraft: Aircraft object
        resultdir: absolute path to store results
        tmpdir: absolute path to store temporary files
        ovspdir (optional): installation directory of OpenVSP software
    """

    vspscript_exe = 'vspscript.exe'
    vspaero_exe = 'vspaero.exe'

    vspscript_filename = "wing_openvsp.vspscript"
    vspaero_filename = "wing_openvsp_DegenGeom.vspaero"
    result_filename = 'polar.txt'
    takeoff_result_filename = 'Result_of_vsp_takeoff.txt'

    def initialize(self):
        self.options.declare('ovsp_dir',
                             default=os.path.join(os.path.dirname(__file__), os.pardir,
                                                  'OpenVSP-3.5.1-win32'),
                             types=str)
        self.options.declare('result_dir',
                             default=os.path.join(os.path.dirname(__file__), os.pardir, 'result'),
                             types=str)
        self.options.declare('tmp_dir',
                             default=os.path.join(os.path.dirname(__file__), os.pardir, 'tmp'),
                             types=str)
        self.options.declare('openvsp_aero', default=False, types=bool)
        self.options.declare('takeoff_flag', default=False, types=bool)

    def setup(self):
        self.ovspdir = self.options['ovsp_dir']
        self.resultdir = self.options['result_dir']
        self.tmpdir = self.options['tmp_dir']
        self.openvsp_aero = self.options['openvsp_aero']
        self.takeoff_flag = self.options['takeoff_flag']

        if self.openvsp_aero:
            self.add_input('AoA_min_hs', val=0.)
            self.add_input('AoA_max_hs', val=0.)
            self.add_input('AoA_step_hs', val=0.)
            self.add_input('tlar:cruise_Mach', val=0.)
            self.add_input('sizing_mission:cruise_altitude', val=0.)
        else:
            self.add_input('AoA_min', val=0.)
            self.add_input('AoA_max', val=0.)
            self.add_input('AoA_step', val=0.)
            self.add_input('openvsp:mach', val=0.)
            self.add_input('openvsp:altitude', val=0.)

        self.add_input('geometry:wing_l2', val=0.)
        self.add_input('geometry:wing_y2', val=0.)
        self.add_input('geometry:wing_l3', val=0.)
        self.add_input('geometry:wing_x3', val=0.)
        self.add_input('geometry:wing_y3', val=0.)
        self.add_input('geometry:wing_l4', val=0.)
        self.add_input('geometry:wing_x4', val=0.)
        self.add_input('geometry:wing_y4', val=0.)
        self.add_input('geometry:wing_area', val=0.)
        self.add_input('geometry:wing_span', val=0.)
        self.add_input('geometry:wing_l0', val=0.)

    def compute(self, inputs, outputs):
        if self.openvsp_aero:
            AoA_min = inputs['AoA_min_hs']
            AoA_max = inputs['AoA_max_hs']
            step = inputs['AoA_step_hs']
            mach = inputs['tlar:cruise_Mach']
            altitude = inputs['sizing_mission:cruise_altitude']
        else:
            AoA_min = inputs['AoA_min']
            AoA_max = inputs['AoA_max']
            step = inputs['AoA_step']
            mach = inputs['openvsp:mach']
            altitude = inputs['openvsp:altitude']

        l2_wing = inputs['geometry:wing_l2']
        y2_wing = inputs['geometry:wing_y2']
        y3_wing = inputs['geometry:wing_y3']
        y4_wing = inputs['geometry:wing_y4']
        l4_wing = inputs['geometry:wing_l4']
        l3_wing = inputs['geometry:wing_l3']
        x3_wing = inputs['geometry:wing_x3']
        x4_wing = inputs['geometry:wing_x4']
        sref = inputs['geometry:wing_area']
        cref = inputs['geometry:wing_l0']
        bref = inputs['geometry:wing_span']

        AoA_vector = [AoA_min, AoA_max, step]
        condition_vector = [mach, altitude]

        wing_geometry_vector = [l2_wing, y2_wing, l3_wing, x3_wing,
                                y3_wing, l4_wing, x4_wing, y4_wing]

        wing_parameter_vector = [sref, cref, bref]

        self.run(AoA_vector, condition_vector, wing_geometry_vector, wing_parameter_vector,
                 self.takeoff_flag)

    def run(self, AoA_vector, condition_vector, wing_geometry_vector,
            wing_parameter_vector, takeoff):

        self._write_vsp_file(wing_geometry_vector)
        self._write_vspaero_file(condition_vector, wing_parameter_vector)

        AoA_min = float(AoA_vector[0])
        AoA_max = float(AoA_vector[1])
        step = float(AoA_vector[2])

        alpha_vector = []
        result_cl = []
        result_cxi = []
        cx_wing = []

        vspaero_basename = os.path.splitext(OpenVSP.vspaero_filename)[0]

        self._make_inplace_change(
            os.path.join(self.tmpdir, OpenVSP.vspaero_filename),
            "\nAoA = " + str(0.0), "\nAoA = " + str(AoA_min))
        alpha = AoA_min
        while alpha < AoA_max:
            old_alpha = alpha
            alpha += step
            alpha_vector.append(alpha)
            self._make_inplace_change(
                os.path.join(self.tmpdir, OpenVSP.vspaero_filename),
                "\nAoA = " + str(old_alpha), "\nAoA = " + str(alpha))
            # Run the vspscript using vsp
            handle = win32process.CreateProcess(
                None,
                os.path.join(self.ovspdir, OpenVSP.vspscript_exe) + ' -script ' +
                os.path.join(self.tmpdir, OpenVSP.vspscript_filename),
                None,
                None,
                0,
                win32process.CREATE_NO_WINDOW,
                None,
                None,
                win32process.STARTUPINFO())
            # to wait for the exit of the process
            win32event.WaitForSingleObject(handle[0], -1)
            # Run DegenGeom using vspaero
            handle2 = win32process.CreateProcess(
                None,
                os.path.join(self.ovspdir, OpenVSP.vspaero_exe) + " " +
                os.path.join(self.tmpdir, vspaero_basename),
                None,
                None,
                0,
                win32process.CREATE_NO_WINDOW,
                None,
                None,
                win32process.STARTUPINFO())
            # to wait for the exit of the process
            win32event.WaitForSingleObject(handle2[0], -1)
            histfile = os.path.join(
                self.tmpdir,
                vspaero_basename + '.history')
            with open(histfile, 'r') as hf:
                l1 = hf.readlines()
                result = l1[5][40:50]
                result = result.replace(' ', '')
                result_cl.append(float(result))
                result2 = l1[5][60:70]
                result2 = result2.replace(' ', '')
                result_cxi.append(float(result2))
                result3 = l1[5][50:60]
                result3 = result3.replace(' ', '')
                cx_wing.append(float(result3))
        if takeoff:
            f_vsp = os.path.join(self.tmpdir, OpenVSP.takeoff_result_filename)
        else:
            f_vsp = os.path.join(self.tmpdir, OpenVSP.result_filename)
        fichier = open(f_vsp, "w")
        for iteration4 in range(len(result_cl)):
            fichier.write(str(result_cl[iteration4]) +
                          ',' +
                          str(result_cxi[iteration4]) +
                          ',' +
                          str(cx_wing[iteration4]) +
                          ',' +
                          str(alpha_vector[iteration4]) +
                          '\n')
        fichier.close()
        f_vsp_temp = os.path.join(self.tmpdir, vspaero_basename + '.lod')
        # if os.path.isfile(f_vsp_temp):
        # os.remove(os.path.join(self.tmpdir, vspaero_basename + '.lod'))
        # os.remove(os.path.join(self.tmpdir, vspaero_basename + '.adb'))
        # os.remove(
        #     os.path.join(
        #         self.tmpdir,
        #         vspaero_basename + '.history'))
        # os.remove(os.path.join(self.tmpdir, vspaero_basename + '.csv'))
        # os.remove(
        #     os.path.join(self.tmpdir, vspaero_basename + '.vspaero'))

    # use equations to calculate the oswald coefficient, in order not to use
    # vspaero

    def _write_vsp_file(
            self, wing_geom_v, filename=vspscript_filename,
            resourcesdir=os.path.join(os.path.dirname(__file__), 'resources')):

        for i, value in enumerate(wing_geom_v):
            wing_geom_v[i] = float(value)
        l2_wing = wing_geom_v[0]
        y2_wing = wing_geom_v[1]
        l3_wing = wing_geom_v[2]
        x3_wing = wing_geom_v[3]
        y3_wing = wing_geom_v[4]
        l4_wing = wing_geom_v[5]
        x4_wing = wing_geom_v[6]
        y4_wing = wing_geom_v[7]

        area_1 = l2_wing * y2_wing
        span_2 = y3_wing - y2_wing
        span_3 = y4_wing - y3_wing
        const1 = x4_wing + l4_wing - l3_wing - x3_wing
        const2 = l3_wing + const1 - l4_wing
        area_3 = (const1 + l3_wing) * (y4_wing - y3_wing) - 0.5 * \
                 const1 * (y4_wing - y3_wing) - 0.5 * const2 * (y4_wing - y3_wing)

        # ----------------------------------------------------------------
        #                     WRITE VSPSCRIPT FOR THE WING FOR OPENVSP
        # ----------------------------------------------------------------

        vspaero_basename = os.path.splitext(OpenVSP.vspaero_filename)[0]
        resdir = os.path.abspath(resourcesdir)
        fichier = open(
            os.path.join(self.tmpdir, filename),
            "w")
        fichier.write(
            '\n//==== Create A Multi Section Wing and Change Some Parameters ====//\nvoid main()\n{\n    //==== Add Wing ====//\n    string wid = AddGeom( "WING", "");\n\n    //===== Insert A Couple More Sections =====//\n')
        insert_xsec = "    InsertXSec( wid, 1, XS_FOUR_SERIES );\n    InsertXSec( wid, 1, XS_FOUR_SERIES );\n    InsertXSec( wid, 1, XS_FOUR_SERIES );"
        fichier.write(insert_xsec)
        fichier.write(
            '\n\n    //===== Cut The Original Section =====//\n    CutXSec( wid, 1 );\n\n    //===== Change Driver =====//\n    SetDriverGroup( wid, 1, AREA_WSECT_DRIVER, ROOTC_WSECT_DRIVER, TIPC_WSECT_DRIVER );\n\n    SetParmVal( wid, "RotateAirfoilMatchDideralFlag", "WingGeom", 1.0 );\n\n    //===== Change Some Parameters 1st Section ====//\n')

        fichier.write('    SetParmVal( wid, "Root_Chord", "XSec_1", ')
        fichier.write(str(l2_wing))
        fichier.write(' );\n    SetParmVal( wid, "Tip_Chord", "XSec_1", ')
        fichier.write(str(l2_wing))
        fichier.write(' );\n    SetParmVal( wid, "Area", "XSec_1", ')
        fichier.write(str(area_1))
        fichier.write(' );\n    SetParmVal( wid, "Sweep", "XSec_1", 0.0 );')

        fichier.write(
            "\n\n    //==== Because Sections Are Connected Change One Section At A Time Then Update ====//\n    Update();\n\n    //===== Change Some Parameters 2nd Section ====//")

        fichier.write('\n    SetParmVal( wid, "Tip_Chord", "XSec_2", ')
        fichier.write(str(l3_wing))
        fichier.write(' );\n    SetParmVal( wid, "Span", "XSec_2", ')
        fichier.write(str(span_2))
        fichier.write(
            ' );\n    SetParmVal( wid, "Sweep", "XSec_2", 20.74 );\n    SetParmVal( wid, "Sweep_Location", "XSec_2", 0.17419 );\n    SetParmVal( wid, "Sec_Sweep_Location", "XSec_2", 0.9871 );\n    SetParmVal( wid, "Twist", "XSec_2", 0.5 );\n    SetParmVal( wid, "Twist_Location", "XSec_2", 0.25 );\n    SetParmVal( wid, "Dihedral", "XSec_2", 5.0 );\n    Update();')

        fichier.write(
            "\n\n    //===== Change Some Parameters 3rd Section ====//\n")

        fichier.write('    SetParmVal( wid, "Tip_Chord", "XSec_3", ')
        fichier.write(str(l4_wing))
        fichier.write(' );\n    SetParmVal( wid, "Span", "XSec_3", ')
        fichier.write(str(span_3))
        fichier.write(' );\n    SetParmVal( wid, "Area", "XSec_3", ')
        fichier.write(str(area_3))
        fichier.write(
            ' );\n    SetParmVal( wid, "Sweep", "XSec_3", 24.54 );\n    SetParmVal( wid, "Twist", "XSec_3", 0.3 );\n    SetParmVal( wid, "Twist_Location", "XSec_3", 0.25 );\n    SetParmVal( wid, "Dihedral", "XSec_3", 5.0 );\n    Update();')

        airfoil_0 = '\n\n    //==== Change Airfoil 0 ====//\n    string xsec_surf0 = GetXSecSurf( wid, 0 );\n    ChangeXSecShape( xsec_surf0, 0, XS_FILE_AIRFOIL );\n    string xsec0 = GetXSec( xsec_surf0, 0 );\n    ReadFileAirfoil( xsec0, "' + \
                    os.path.join(
                        resdir,
                        "airfoil_f_15_15.dat") + '");\n\n    Update();\n\n'
        airfoil_0 = airfoil_0.replace('\\', '/')
        fichier.write(airfoil_0)
        airfoil_1 = '    //==== Change Airfoil 1====//\n    string xsec_surf = GetXSecSurf( wid, 1 );\n    ChangeXSecShape( xsec_surf, 1, XS_FILE_AIRFOIL );\n    string xsec1 = GetXSec( xsec_surf, 1 );\n    ReadFileAirfoil( xsec1, "' + \
                    os.path.join(
                        resdir,
                        "airfoil_f_15_15.dat") + '");\n\n    Update();\n\n'
        airfoil_1 = airfoil_1.replace('\\', '/')
        fichier.write(airfoil_1)
        airfoil_2 = '    //==== Change Airfoil 2====//\n    string xsec_surf2 = GetXSecSurf( wid, 2 );\n    ChangeXSecShape( xsec_surf2, 2, XS_FILE_AIRFOIL );\n    string xsec2 = GetXSec( xsec_surf2, 2 );\n    ReadFileAirfoil( xsec2, "' + \
                    os.path.join(
                        resdir,
                        "airfoil_f_15_12.dat") + '");\n\n    Update();\n\n'
        airfoil_2 = airfoil_2.replace('\\', '/')
        fichier.write(airfoil_2)
        airfoil_3 = '    //==== Change Airfoil 3====//\n    string xsec_surf3 = GetXSecSurf( wid, 3 );\n    ChangeXSecShape( xsec_surf3, 3, XS_FILE_AIRFOIL );\n    string xsec3 = GetXSec( xsec_surf3, 3 );\n    ReadFileAirfoil( xsec3, "' + \
                    os.path.join(
                        resdir,
                        "airfoil_f_15_11.dat") + '");\n\n    Update();\n\n'
        airfoil_3 = airfoil_3.replace('\\', '/')
        fichier.write(airfoil_3)

        fichier.write(
            "    //==== Check For API Errors ====//\n    while ( GetNumTotalErrors() > 0 )\n    {\n        ErrorObj err = PopLastError();\n        Print( err.GetErrorString() );\n    }\n\n")

        csvfile = '    //==== Set File Name ====//\n    SetComputationFileName( DEGEN_GEOM_CSV_TYPE, "' + \
                  os.path.join(
                      self.tmpdir,
                      vspaero_basename + '.csv') + '" );\n\n'
        csvfile = csvfile.replace('\\', '/')
        fichier.write(csvfile)
        fichier.write(
            '    //==== Run Degen Geom ====//\n    ComputeDegenGeom( SET_ALL, DEGEN_GEOM_CSV_TYPE );\n}')

        fichier.close()

    # ----------------------------------------------------------------
    #              MODIFY DEGENGEOM FUNCTION FOR THE WING FOR OPENVSP
    # ----------------------------------------------------------------

    @staticmethod
    def _make_inplace_change(filename, old_string, new_string):
        s = open(filename).read()
        if old_string in s:
            s = s.replace(old_string, new_string)
            f = open(filename, 'w')
            f.write(s)
            f.flush()
            f.close()
        else:
            print('No occurances of "{old_string}" found.'.format(**locals()))

    # ----------------------------------------------------------------
    #                     WRITE DEGENGEOM FOR THE WING FOR OPENVSP
    # ----------------------------------------------------------------
    def _write_vspaero_file(self, cond_v, wing_param_v,
                            filename=vspaero_filename):

        for i, value in enumerate(cond_v):
            cond_v[i] = float(value)
        for i, value in enumerate(wing_param_v):
            wing_param_v[i] = float(value)

        mach = cond_v[0]
        altitude = cond_v[1]
        Sref = wing_param_v[0]
        Cref = wing_param_v[1]
        Bref = wing_param_v[2]

        atmosphere = Atmosphere(altitude)
        # temperature, rho, pression, viscosity, sos = Atmosphere(altitude)
        V_inf = atmosphere.speed_of_sound * mach
        Re = V_inf * Cref / atmosphere.kinematic_viscosity
        fichier = open(os.path.join(self.tmpdir, filename), "w")
        fichier.write("Sref = ")
        fichier.write(str(Sref))
        fichier.write("\nCref = ")
        fichier.write(str(Cref))
        fichier.write("\nBref = ")
        fichier.write(str(Bref))
        fichier.write(
            "\nX_cg = 0.000000\nY_cg = 0.000000\nZ_cg = 0.000000\nMach = ")
        fichier.write(str(mach))
        fichier.write("\nAoA = ")
        fichier.write(str(0.0))
        fichier.write("\nBeta = 0.000000")
        fichier.write("\nVinf = ")
        fichier.write(str(V_inf))
        fichier.write("\nRho = ")
        fichier.write(str(atmosphere.density))
        fichier.write("\nReCref = ")
        fichier.write(str(Re))
        fichier.write("\nClMax = -1.000000\nMaxTurningAngle = -1.000000 \n\
        Symmetry = No \nFarDist = -1.000000\nNumWakeNodes = " + str(multiprocessing.cpu_count()) + " \nWakeIters = 5 \n\
        NumberOfRotors = 0")
        fichier.close()
