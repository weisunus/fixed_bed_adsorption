import RPB_model
import pandas as pd
from idaes.core.util import to_json, from_json
import numpy as np
import pyomo.environ as pyo
import idaes.core.util.scaling as iscale
import scaling_methods as sm



def Remove_Pressure_Drop(b):
    # b.ads.R_dP.fix(0.001)
    # b.des.R_dP.fix(0.001)
    
    b.ads.F_in.fix()
    b.ads.P_in.fix()
    b.ads.P_out.unfix()
    
    b.des.F_in.fix()
    b.des.P_in.fix()
    b.des.P_out.unfix()
    
def set_polishing_bounds(sections):
    for section in sections:
        section.P_in.setub(10)
        section.L.setub(40)
        if str(section) == 'ads':
            section.Tx.setlb(298)
            section.Tx.setub(368)
        elif str(section) == 'des':
            section.Tx.setlb(373)
            section.Tx.setub(433)
        for z in section.z:
            for o in section.o:
                section.dPdz[z,o].setub(5)
                section.dPdz[z,o].setlb(-5)
                section.C_tot.setub(250)
                section.P[z,o].setub(10)
                section.vel[z,o].setub(15)
                
def toggle_design_variables(blk, fix=False):
    variable_list = [
                     blk.ads.L,
                     blk.ads.w_rpm,
                     blk.ads.theta,
                     blk.ads.Tx,
                     blk.ads.P_in,
                     blk.des.P_in,
                     blk.des.P_out,
                     blk.des.Tx,
                     ]
    if fix:
        for v in variable_list:
            v.fix()
    else:
        for v in variable_list:
            v.unfix()

if __name__ == '__main__':
    
    has_pressure_drop = True
    RPB = RPB_model.full_model_creation(lean_temp_connection=True,
                                        configuration='counter-current')
    ads = RPB.ads
    des = RPB.des
    # RPB_model.add_ads_inlet_comp_constraint(RPB.ads)
    

    y_in = {'CO2': 0.002201,
            'N2': 0.940705,
            'H2O': 0.05}
    y_in = {'CO2': 0.002,
            'N2': 0.948,
            'H2O': 0.05}
    
    y_in = {'CO2': 0.0391,
            'N2': 0.8768,
            'H2O': 0.0841}
    
    
    # @RPB.Expression()
    # def obj(RPB):
    #     return RPB.energy_requirement
    # RPB.objective = pyo.Objective(expr=RPB.obj)
    
    # RPB.ads.P_in.bounds = (0.99, 1.5)
    RPB.ads.P_in.setub(1.75)
    RPB.ads.P_in.setlb(0.99)
    # RPB.ads.P.bounds = (0.99, 1.5)
    RPB.ads.P.setub(1.75)
    # RPB.ads.P.setlb(0.99)
    
    if not has_pressure_drop:
        Remove_Pressure_Drop(RPB)
        
    homotopy_points = np.linspace(0.2, 1, 5)
    # RPB_model.init_routine_1(RPB)#, homotopy_points)

    # from_json(RPB, fname="opt solution 012424.json.gz", gz=True)
    from_json(RPB, fname="json_files/high_co2/cap_85.json.gz", gz=True)
    
    # RPB.ads = RPB_model.scale_model(RPB.ads, gas_flow_direction=1, mode='adsorption')
    # for z in RPB.des.z:
    #     for o in RPB.des.o:
    #         iscale.constraint_scaling_transform(RPB.des.Q_delH_eq[z,o], 1e-3)
    #         iscale.constraint_scaling_transform(RPB.ads.Q_delH_eq[z,o], 1e-2)
    #         iscale.constraint_scaling_transform(RPB.ads.heat_flux_eq[z,o], 1e-3)
    #         iscale.constraint_scaling_transform(RPB.des.Rs_CO2_eq[z,o], 1e-2)
    #         iscale.constraint_scaling_transform(RPB.ads.Rs_CO2_eq[z,o], 1e-2)
    #         iscale.constraint_scaling_transform(RPB.des.constr_MTcont[z, o], 1e-2)
    #         if z < 1:
    #             iscale.set_scaling_factor(RPB.des.dPdz[z, o], 1e3)
    #             iscale.constraint_scaling_transform(RPB.des.dPdz_disc_eq[z, o], 1e-5)
    #             iscale.constraint_scaling_transform(RPB.des.pde_gasEB[z,o], 1e-3)
    #         if z > 0:
    #             iscale.constraint_scaling_transform(RPB.ads.pde_gasEB[z,o], 1e-1)
    
    # RPB_model.solve_model(RPB,)# optarg={'max_iter': 0})
    Results = RPB_model.report(RPB)
    # Results_Inlet_Loading = RPB_model.report_loading(RPB)
    
    # co2_comp_list = np.linspace(0.04, 0.004, 10)
    # n2_comp_list = np.linspace(0.87, 0.94, 10)
    # for i in range(len(co2_comp_list)):
    #     print(i)
    #     RPB.ads.y_in["CO2"].fix(co2_comp_list[i])
    #     RPB.ads.y_in["N2"].fix(n2_comp_list[i])
    #     RPB_model.solve_model(RPB)
        
    
    

        
    