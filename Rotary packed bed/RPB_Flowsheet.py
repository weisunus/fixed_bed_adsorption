"""
RPB Flowsheet (WIP)
"""
# Python imports
import math
import logging

# Pyomo imports
import pyomo.environ as pyo
from pyomo.network import Arc, Port
from pyomo.common.config import ConfigValue, ListOf
from pyomo.util.calc_var_value import calculate_variable_from_constraint


# IDAES imports
from idaes.core.util.model_statistics import degrees_of_freedom
from idaes.core import FlowsheetBlockData, declare_process_block_class
from idaes.core.util.constants import Constants
import idaes.core.util.scaling as iscale

from RPB_model import RPB_model

logging.getLogger('pyomo.repn.plugins.nl_writer').setLevel(logging.ERROR)

@declare_process_block_class("RPBFlowsheet")
class RPBFlowsheetData(FlowsheetBlockData):
    CONFIG = FlowsheetBlockData.CONFIG()
    CONFIG.declare(
        "lean_temp_connection",
        ConfigValue(
            default=True,
            description="Placeholder",
        ),
    )
    CONFIG.declare(
        "configuration",
        ConfigValue(
            default='counter-current',
            description="Configuration of FG and steam flow through RPB")
    )
    CONFIG.declare(
        "has_pressure_drop",
        ConfigValue(
            default=True,
            description="Placeholder",
        ),
    )
    def build(self):
        super().build()
        # self._add_properties()
        self._add_units()
        # self._add_arcs()
        self._add_boundary_constraints()
        self._add_performance_math()
        self._scaling()
    
    def _add_units(self):
        if self.config.configuration == "co-current":
            self.ads = RPB_model(mode="adsorption", gas_flow_direction=1)
            self.des = RPB_model(mode="desorption", gas_flow_direction=1)
        elif self.config.configuration == "counter-current":
            self.ads = RPB_model(mode="adsorption", gas_flow_direction=1)
            self.des = RPB_model(mode="desorption", gas_flow_direction=-1)
        
        # these variables are inactive, just fixing them to same value for plotting purposes
        self.ads.qCO2[0, 0].fix(1)
        self.ads.qCO2[1, 0].fix(1)
        self.des.qCO2[0, 0].fix(1)
        self.des.qCO2[1, 0].fix(1)

        self.ads.Ts[0, 0].fix(100 + 273)
        self.ads.Ts[1, 0].fix(100 + 273)
        self.des.Ts[0, 0].fix(100 + 273)
        self.des.Ts[1, 0].fix(100 + 273)
    
    def _add_boundary_constraints(self):
        lean_temp_connection = self.config.lean_temp_connection
        
        # connect rich stream
        # unfix inlet loading and temperature to the desorption section. (No mass transfer at boundaries so z=0 and z=1 need to remain fixed.)
        for z in self.des.z:
            if 0 < z < 1:
                self.des.qCO2[z, 0].unfix()
                self.des.Ts[z, 0].unfix()

        # add equality constraint equating inlet desorption loading to outlet adsorption loading. Same for temperature.
        self.interface_scale = pyo.Param(initialize=1e-4,
                                            # mutable=True,
                                            )
        @self.Constraint(self.des.z)
        def rich_loading_constraint(b, z):
            if 0 < z < 1:
                return b.interface_scale * (b.des.qCO2[z, 0] - b.ads.qCO2[z, 1]) == 0
            else:
                return pyo.Constraint.Skip

        @self.Constraint(self.des.z)
        def rich_temp_constraint(b, z):
            if 0 < z < 1:
                return b.interface_scale * (b.des.Ts[z, 0] - b.ads.Ts[z, 1]) == 0
            else:
                return pyo.Constraint.Skip

        # connect lean stream
        # unfix inlet loading to the adsorption section
        for z in self.ads.z:
            if 0 < z < 1:
                self.ads.qCO2[z, 0].unfix()
                if lean_temp_connection:
                    self.ads.Ts[z, 0].unfix()

        # add equality constraint equating inlet adsorption loading to outlet desorption loading
        @self.Constraint(self.ads.z)
        def lean_loading_constraint(b, z):
            if 0 < z < 1:
                return b.interface_scale * (b.ads.qCO2[z, 0] - b.des.qCO2[z, 1]) == 0
            else:
                return pyo.Constraint.Skip

        if lean_temp_connection:

            @self.Constraint(self.ads.z)
            def lean_temp_constraint(b, z):
                if 0 < z < 1:
                    return b.interface_scale * (b.ads.Ts[z, 0] - b.des.Ts[z, 1]) == 0
                else:
                    return pyo.Constraint.Skip
        
        
        # add constraints so that the length, diameter, and rotational speed are the same for both sides
        self.des.L.unfix()  # unfix des side vars
        self.des.D.unfix()
        self.des.w_rpm.unfix()

        @self.Constraint(doc="Length equality constraint")
        def length_constraint(b):
            return b.ads.L == b.des.L

        @self.Constraint(doc="Diameter equality constraint")
        def diameter_constraint(b):
            return b.ads.D == b.des.D

        @self.Constraint(doc="Rotational speed equality constraint")
        def speed_constraint(b):
            return b.ads.w_rpm == b.des.w_rpm

        # add constraint so that the fraction of each section adds to 1
        self.des.theta.unfix()  # unfix des side var

        @self.Constraint(doc="Theta summation constraint")
        def theta_constraint(b):
            return b.ads.theta + b.des.theta == 1
    
    def _add_performance_math(self):
        self.steam_enthalpy = pyo.Param(
            initialize=2257.92,
            mutable=True,
            units=pyo.units.kJ / pyo.units.kg,
            doc="saturated steam enthalpy at 1 bar[kJ/kg]",
        )

        @self.Expression(doc="Steam energy [kW]")
        def steam_energy(b):
            return (
                b.des.F_in * b.des.y_in["H2O"] * b.des.MW["H2O"] * b.steam_enthalpy
            )

        @self.Expression(doc="total thermal energy (steam + HX) [kW]")
        def total_thermal_energy(b):
            return b.steam_energy - b.des.Q_ghx_tot_kW

        @self.Expression(doc="Energy requirement [MJ/kg CO2]")
        def energy_requirement(b):
            return pyo.units.convert(
                b.total_thermal_energy / b.ads.delta_CO2 / b.ads.MW["CO2"],
                to_units=pyo.units.MJ / pyo.units.kg,
            )

        @self.Expression(doc="Productivity [kg CO2/h/m^3]")
        def productivity(b):
            return pyo.units.convert(
                b.ads.delta_CO2 * b.ads.MW["CO2"] / b.ads.vol_tot,
                to_units=pyo.units.kg / pyo.units.h / pyo.units.m**3,
            )
    
    def _scaling(self):
        # add scaling factors
        iscale.set_scaling_factor(self.theta_constraint, 1e2)
        for z in self.ads.z:
            if 0 < z < 1:
                iscale.set_scaling_factor(self.lean_loading_constraint[z], 10)
                iscale.set_scaling_factor(self.rich_loading_constraint[z], 10)
