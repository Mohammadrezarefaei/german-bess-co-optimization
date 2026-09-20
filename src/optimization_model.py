# src/optimization_model.py

import pulp
import pandas as pd
import numpy as np

def solve_bess_co_optimization(df_market, config):
    """
    Solves the utility-scale BESS day-ahead and aFRR co-optimization problem.
    """
    model = pulp.LpProblem("BESS_German_DayAhead_aFRR_CoOptimization", pulp.LpMaximize)
    
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
    p_ch = pulp.LpVariable.dicts("P_ch", T, lowBound=0, upBound=P_max, cat=pulp.LpContinuous)
    p_dis = pulp.LpVariable.dicts("P_dis", T, lowBound=0, upBound=P_max, cat=pulp.LpContinuous)
    u_ch = pulp.LpVariable.dicts("u_ch", T, cat=pulp.LpBinary)
    u_dis = pulp.LpVariable.dicts("u_dis", T, cat=pulp.LpBinary)

    r_pos_block = pulp.LpVariable.dicts("R_pos_block", blocks, lowBound=0, upBound=P_max, cat=pulp.LpContinuous)
    r_neg_block = pulp.LpVariable.dicts("R_neg_block", blocks, lowBound=0, upBound=P_max, cat=pulp.LpContinuous)

    soc = pulp.LpVariable.dicts("SOC", T, lowBound=SOC_min, upBound=SOC_max, cat=pulp.LpContinuous)

    # Objective Function
    spot_rev = pulp.lpSum([
        (df_market.loc[t, 'Spot_DA_EUR_MWh'] * p_dis[t] - df_market.loc[t, 'Spot_DA_EUR_MWh'] * p_ch[t])
        for t in T
    ])
    
    afrr_rev = pulp.lpSum([
        4 * (df_market.loc[b*4, 'aFRR_Pos_Cap_EUR_MW'] * r_pos_block[b] + 
             df_market.loc[b*4, 'aFRR_Neg_Cap_EUR_MW'] * r_neg_block[b])
        for b in blocks
    ])
    
    total_deg_cost = pulp.lpSum([
        deg_cost * (p_ch[t] + p_dis[t])
        for t in T
    ])

    model += spot_rev + afrr_rev - total_deg_cost, "Net_Profit"

    # Constraints
    for t in T:
        b = t // 4
        
        # Exclusive charging/discharging in Spot
        model += p_ch[t] <= P_max * u_ch[t]
        model += p_dis[t] <= P_max * u_dis[t]
        model += u_ch[t] + u_dis[t] <= 1

        # Inverter capacity sharing
        model += p_dis[t] + r_pos_block[b] <= P_max
        model += p_ch[t] + r_neg_block[b] <= P_max

        # SOC dynamics
        prev_soc = SOC_init if t == 0 else soc[t - 1]
        model += soc[t] == prev_soc + (p_ch[t] * eta_ch - (p_dis[t] / eta_dis))

        # aFRR Energy Backing Buffers
        model += soc[t] - (r_pos_block[b] * afrr_dur_buffer) >= SOC_min
        model += soc[t] + (r_neg_block[b] * afrr_dur_buffer) <= SOC_max

    model += soc[23] >= SOC_INIT, "Final_SOC_Neutrality"

    # Solve
    solver = pulp.PULP_CBC_CMD(msg=False)
    status = model.solve(solver)
    
    results = []
    for t in T:
        b = t // 4
        results.append({
            'Hour': t,
            'Block_4h': b,
            'Spot_DA_EUR_MWh': df_market.loc[t, 'Spot_DA_EUR_MWh'],
            'aFRR_Pos_EUR_MW': df_market.loc[t, 'aFRR_Pos_Cap_EUR_MW'],
            'aFRR_Neg_EUR_MW': df_market.loc[t, 'aFRR_Neg_Cap_EUR_MW'],
            'P_charge_MW': p_ch[t].varValue,
            'P_discharge_MW': p_dis[t].varValue,
            'R_aFRR_Pos_MW': r_pos_block[b].varValue,
            'R_aFRR_Neg_MW': r_neg_block[b].varValue,
            'SOC_MWh': soc[t].varValue,
            'SOC_Pct': (soc[t].varValue / E_max) * 100
        })
        
    return pd.DataFrame(results), pulp.LpStatus[status], pulp.value(model.objective)
