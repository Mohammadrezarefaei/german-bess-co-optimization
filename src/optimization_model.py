# src/optimization_model.py

import pandas as pd
import numpy as np
from ortools.linear_solver import pywraplp

def solve_bess_co_optimization(df_market, config):
    """
    Solves the utility-scale BESS day-ahead and aFRR co-optimization problem 
    using Google OR-Tools (MILP Solver).
    """
    solver = pywraplp.Solver.CreateSolver('CBC')
    if not solver:
        raise Exception("Could not create OR-Tools solver.")

    T = df_market['Hour'].tolist()
    num_blocks = 6
    blocks = list(range(num_blocks))

    P_max = config['P_max']
    E_max = config['E_max']
    eta_ch = config['eta_ch']
    eta_dis = config['eta_dis']
    deg_cost = config['deg_cost']
    afrr_dur_buffer = config['afrr_dur_buffer']
    
    SOC_min = config['SOC_min_pct'] * E_max
    SOC_max = config['SOC_max_pct'] * E_max
    SOC_init = config['SOC_init_pct'] * E_max

    # Decision Variables
    p_ch = {}
    p_dis = {}
    u_ch = {}
    u_dis = {}
    soc = {}

    for t in T:
        p_ch[t] = solver.NumVar(0.0, P_max, f"P_ch_{t}")
        p_dis[t] = solver.NumVar(0.0, P_max, f"P_dis_{t}")
        u_ch[t] = solver.BoolVar(f"u_ch_{t}")
        u_dis[t] = solver.BoolVar(f"u_dis_{t}")
        soc[t] = solver.NumVar(SOC_min, SOC_max, f"SOC_{t}")

    r_pos_block = {}
    r_neg_block = {}
    for b in blocks:
        r_pos_block[b] = solver.NumVar(0.0, P_max, f"R_pos_block_{b}")
        r_neg_block[b] = solver.NumVar(0.0, P_max, f"R_neg_block_{b}")

    # Constraints
    for t in T:
        b = t // 4
        
        # Exclusive charging/discharging in Spot
        solver.Add(p_ch[t] <= P_max * u_ch[t])
        solver.Add(p_dis[t] <= P_max * u_dis[t])
        solver.Add(u_ch[t] + u_dis[t] <= 1)

        # Inverter capacity sharing
        solver.Add(p_dis[t] + r_pos_block[b] <= P_max)
        solver.Add(p_ch[t] + r_neg_block[b] <= P_max)

        # SOC dynamics
        prev_soc = SOC_init if t == 0 else soc[t - 1]
        solver.Add(soc[t] == prev_soc + (p_ch[t] * eta_ch - (p_dis[t] / eta_dis)))

        # aFRR Energy Backing Buffers
        solver.Add(soc[t] - (r_pos_block[b] * afrr_dur_buffer) >= SOC_min)
        solver.Add(soc[t] + (r_neg_block[b] * afrr_dur_buffer) <= SOC_max)

    # Final SOC Neutrality Constraint
    solver.Add(soc[23] >= SOC_init)

    # Objective Function
    spot_rev = solver.Sum([
        (df_market.loc[t, 'Spot_DA_EUR_MWh'] * p_dis[t] - df_market.loc[t, 'Spot_DA_EUR_MWh'] * p_ch[t])
        for t in T
    ])
    
    afrr_rev = solver.Sum([
        4 * (df_market.loc[b*4, 'aFRR_Pos_Cap_EUR_MW'] * r_pos_block[b] + 
             df_market.loc[b*4, 'aFRR_Neg_Cap_EUR_MW'] * r_neg_block[b])
        for b in blocks
    ])
    
    total_deg_cost = solver.Sum([
        deg_cost * (p_ch[t] + p_dis[t])
        for t in T
    ])

    solver.Maximize(spot_rev + afrr_rev - total_deg_cost)

    # Solve
    status_code = solver.Solve()
    
    if status_code == pywraplp.Solver.OPTIMAL:
        status = "Optimal"
    elif status_code == pywraplp.Solver.FEASIBLE:
        status = "Feasible"
    else:
        status = "Infeasible"

    results = []
    for t in T:
        b = t // 4
        results.append({
            'Hour': t,
            'Block_4h': b,
            'Spot_DA_EUR_MWh': df_market.loc[t, 'Spot_DA_EUR_MWh'],
            'aFRR_Pos_EUR_MW': df_market.loc[t, 'aFRR_Pos_Cap_EUR_MW'],
            'aFRR_Neg_EUR_MW': df_market.loc[t, 'aFRR_Neg_Cap_EUR_MW'],
            'P_charge_MW': p_ch[t].solution_value(),
            'P_discharge_MW': p_dis[t].solution_value(),
            'R_aFRR_Pos_MW': r_pos_block[b].solution_value(),
            'R_aFRR_Neg_MW': r_neg_block[b].solution_value(),
            'SOC_MWh': soc[t].solution_value(),
            'SOC_Pct': (soc[t].solution_value() / E_max) * 100
        })
        
    return pd.DataFrame(results), status, solver.Objective().Value()
