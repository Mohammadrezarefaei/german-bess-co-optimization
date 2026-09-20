# tests/test_optimization.py

import pytest
import pandas as pd
import numpy as np
from src.optimization_model import solve_bess_co_optimization

@pytest.fixture
def sample_market_data():
    hours = list(range(24))
    spot_prices = [50.0] * 24
    afrr_pos = [25.0] * 6
    afrr_neg = [25.0] * 6
    
    df = pd.DataFrame({
        'Hour': hours,
        'Spot_DA_EUR_MWh': spot_prices,
        'aFRR_Pos_Cap_EUR_MW': [afrr_pos[h // 4] for h in hours],
        'aFRR_Neg_Cap_EUR_MW': [afrr_neg[h // 4] for h in hours]
    })
    return df

@pytest.fixture
def standard_bess_config():
    return {
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

def test_optimization_success(sample_market_data, standard_bess_config):
    df_results, status, obj_val = solve_bess_co_optimization(sample_market_data, standard_bess_config)
    
    # بررسی موفقیت‌آمیز بودن حل مدل
    assert status == "Optimal"
    # بررسی مثبت بودن سود حاصله
    assert obj_val > 0

def test_soc_boundaries(sample_market_data, standard_bess_config):
    df_results, status, _ = solve_bess_co_optimization(sample_market_data, standard_bess_config)
    
    soc_min_allowed = standard_bess_config['SOC_min_pct'] * standard_bess_config['E_max']
    soc_max_allowed = standard_bess_config['SOC_max_pct'] * standard_bess_config['E_max']
    
    # بررسی اینکه SOC همیشه بین حد مجاز (مثلاً ۱۰٪ تا ۹۰٪) باقی بماند
    assert df_results['SOC_MWh'].min() >= soc_min_allowed - 1e-5
    assert df_results['SOC_MWh'].max() <= soc_max_allowed + 1e-5

def test_inverter_capacity_limit(sample_market_data, standard_bess_config):
    df_results, status, _ = solve_bess_co_optimization(sample_market_data, standard_bess_config)
    p_max = standard_bess_config['P_max']
    
    for idx, row in df_results.iterrows():
        # مجموع توان شارژ/دشارژ و رزرو نباید از P_max تجاوز کند
        assert row['P_discharge_MW'] + row['R_aFRR_Pos_MW'] <= p_max + 1e-5
        assert row['P_charge_MW'] + row['R_aFRR_Neg_MW'] <= p_max + 1e-5
