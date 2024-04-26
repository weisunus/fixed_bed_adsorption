import pyomo.environ as pyo

from idaes.core.util.model_diagnostics import DiagnosticsToolbox
import idaes.core.util.scaling as iscale

def dt_jac_scaling(model):
    
    # dt = DiagnosticsToolbox(model)
    
    # extreme_jac_entries = dt.display_extreme_jacobian_entries()
    # print(extreme_jac_entries)
    # for entry in extreme_jac_entries:
    #     print(entry)
    
    count = 0
    for entry in iscale.extreme_jacobian_entries(model, scaled=True):
        count += 1
        print(entry[0], entry[1], entry[2])
        iscale.set_scaling_factor(entry[2], entry[0])
        
    print(f'\n{count} extreme entries scaled')
        
def scale_from_init(model):
    
    for v in model.component_objects(pyo.Var, descend_into = True):
        if v.dim() == 0:
            sf = 1 / v()
            iscale.set_scaling_factor(v, sf)
        else:
            for index in v:
                if v[index]() is not None:
                    # print(v[index], v[index]())
                    if v[index]() != 0:
                        sf = 1 / v[index]()
                    else:
                        sf = 1
                    if sf > 1e10:
                        sf = 1e10
                    iscale.set_scaling_factor(v[index], sf)
                    
def check_scaling(model, large = 1e4, small = 1e-4):
    not_scaled_count = 0
    for v in model.component_objects(pyo.Var, descend_into = True):
        for index in v:
            if v[index]() is not None:
                sf = iscale.get_scaling_factor(v[index])
                if sf is not None:
                    if v[index]() * sf > large or v[index]() * sf < small:
                        print(v[index], v[index]())
                else:
                    print(v[index])
                    not_scaled_count += 1
                    
    print(f'{not_scaled_count} unscaled variables')
        # if v.dim() == 0:
        #     sf = 1 / v()
        #     iscale.set_scaling_factor(v, sf)
        # else:
        #     for index in v:
        #         if v[index]() is not None and v[index]() != 0:
        #             # print(v[index], v[index]())
        #             sf = 1 / v[index]()
        #             iscale.set_scaling_factor(v[index], sf)
        
def unset_constraint_scaling(model):
    for c in model.component_objects(pyo.Constraint, descend_into=True):
        for index in c:
            iscale.unset_scaling_factor(c[index])
            
def display_constraint_scaling(model, descend_into=True):
    for c in model.component_objects(pyo.Constraint, descend_into=descend_into):
        for index in c:
            sf = iscale.get_scaling_factor(c[index])
            if sf is not None:
                print(c[index], sf)