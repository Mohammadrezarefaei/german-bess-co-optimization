# app.py

import pandas as pd
import numpy as np
from src.optimization_model import solve_bess_co_optimization
from src.visualization import create_market_dashboard

def main():
    print("--- Starting German BESS Co-Optimization Pipeline ---")
    
    # 1. Configuration
    BESS_CONFIG = {
        'P_max': 10.0,
        'E_max': 20.0,
        'SOC_min_pct': 0.10,
        'SOC_max_pct': 0.90,
        'SOC_init_pct': 0.50,
        'eta_ch': 0.95,
        'eta_dis': 0.95,
        'deg_cost': 5.0,
        'afrr_dur_buffer': 0.5
    }

    # 2. Market Data
    hours = list(range(24))
    spot_prices = [
        58.2, 52.1, 48.5, 45.0, 51.4, 72.8, 125.6, 168.4, 142.0, 95.5, 62.0, 31.2,
        18.5, 12.0, 24.8, 55.3, 110.0, 185.5, 215.0, 192.4, 145.0, 112.5, 88.0, 68.2
    ]
    afrr_pos_block = [18.5, 38.0, 26.5, 22.0, 48.0, 32.5]
    afrr_neg_block = [32.0, 16.5, 24.0, 42.5, 15.0, 22.0]

    df_market = pd.DataFrame({
        'Hour': hours,
        'Spot_DA_EUR_MWh': spot_prices,
        'aFRR_Pos_Cap_EUR_MW': [afrr_pos_block[h // 4] for h in hours],
        'aFRR_Neg_Cap_EUR_MW': [afrr_neg_block[h // 4] for h in hours]
    })

    # 3. Optimization
    df_results, status, obj_val = solve_bess_co_optimization(df_market, BESS_CONFIG)
    print(f"Optimization Status: {status}")
    print(f"Total Objective Value: {obj_val:,.2f} EUR")

    # 4. Visualization
    fig = create_market_dashboard(df_results, BESS_CONFIG)
    fig.write_html("outputs/bess_market_dashboard.html")
    df_results.to_csv("outputs/bess_co_optimization_results.csv", index=False)
    print("Pipeline executed successfully. Outputs saved to /outputs/")

if __name__ == "__main__":
    main()
