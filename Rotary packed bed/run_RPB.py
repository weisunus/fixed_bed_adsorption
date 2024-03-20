import RPB_model
import pandas as pd
from idaes.core.util import to_json, from_json
import numpy as np

if __name__ == '__main__':
    
    RPB = RPB_model.full_model_creation()
    

    y_in = {'CO2': 0.002201,
            'N2': 0.940705,
            'H2O': 0.05}
    y_in = {'CO2': 0.002,
            'N2': 0.948,
            'H2O': 0.05}
    
    y_in = {'CO2': 0.0391,
            'N2': 0.8768,
            'H2O': 0.0841}
    
    # RPB.ads.w_rpm.fix(1)

    # RPB.ads.P_in.fix(1.03)
    
    # RPB.ads.D.fix(10)
    
    # RPB.ads.L.fix(1.8)

    # for comp in y_in.keys():
    #     RPB.ads.y_in[comp].fix(y_in[comp])
        
    # RPB.ads.F_in.fix(5000)
        
    # homotopy_points = np.linspace(0.2, 1, 5)
    # RPB_model.init_routine_1(RPB, homotopy_points)
    # try:
    #     # from_json(RPB, fname="base case solution 012424/base case solution 012424.json")
    #     from_json(RPB_model, fname="initialized_RPB_1.json")
    # except:
    #     RPB_model.init_routine_1(RPB)
    from_json(RPB_model, fname="base case solution 012424/base case solution 012424.json")
    RPB_model.solve_model(RPB)
    Results = RPB_model.report(RPB)
    Results_Inlet_Loading = RPB_model.report_loading(RPB)
    
    # Results = pd.DataFrame()
    # Results.at[0,'Pressure In'] = pyo.value(RPB.ads.P_in)
    
    
    # RPB.ads.P_in.fix(1.05)
    
    # RPB_model.solve_model(RPB)
    
    # p_in = [1.03, 1.04]
    # for P in p_in:
    #     RPB.ads.P_in.fix(P)
    #     RPB_model.solve_model(RPB)
        
    #     Pressure_res = pd.DataFrame()
    #     Pressure_res.at[P, 'Energy Requirement (MJ/kg CO2)'] = pyo.value(RPB.energy_requirement)
        
    