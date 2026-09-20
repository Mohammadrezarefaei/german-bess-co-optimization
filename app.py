# app.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

from src.optimization_model import solve_bess_co_optimization

st.set_page_config(page_title="German BESS Optimizer", page_icon="🔋", layout="wide")

def create_market_data():
    hours = list(range(24))
    np.random.seed(42)
    return pd.DataFrame({
        'Hour': hours,
        'Spot_DA_EUR_MWh': np.random.uniform(30, 150, 24),
        'aFRR_Pos_Cap_EUR_MW': np.repeat(np.random.uniform(10, 50, 6), 4),
        'aFRR_Neg_Cap_EUR_MW': np.repeat(np.random.uniform(10, 50, 6), 4)
    })

def calculate_kpis(df_results, obj_val, config):
    spot_rev = ((df_results['P_discharge_MW'] - df_results['P_charge_MW']) * df_results['Spot_DA_EUR_MWh']).sum()
    df_blocks = df_results.groupby('Block_4h').first()
    afrr_rev = (4 * (df_blocks['R_aFRR_Pos_MW'] * df_blocks['aFRR_Pos_EUR_MW'] + 
                     df_blocks['R_aFRR_Neg_MW'] * df_blocks['aFRR_Neg_EUR_MW'])).sum()
    deg_cost = (config['deg_cost'] * (df_results['P_charge_MW'] + df_results['P_discharge_MW'])).sum()
    efc = df_results['P_discharge_MW'].sum() / config['E_max']
    inverter_usage = np.maximum(
        df_results['P_discharge_MW'] + df_results['R_aFRR_Pos_MW'],
        df_results['P_charge_MW'] + df_results['R_aFRR_Neg_MW']
    )
    avg_utilization = (inverter_usage.mean() / config['P_max']) * 100
    
    return {
        'Net Profit': obj_val,
        'Spot Revenue': spot_rev,
        'aFRR Revenue': afrr_rev,
        'Degradation Cost': deg_cost,
        'EFC': efc,
        'Inverter Utilization': avg_utilization
    }

# --- Sidebar UI ---
st.sidebar.header("⚙️ BESS Configuration")
p_max = st.sidebar.number_input("Power Capacity (MW)", value=10.0, step=1.0)
e_max = st.sidebar.number_input("Energy Capacity (MWh)", value=20.0, step=1.0)
deg_cost_val = st.sidebar.slider("Degradation Cost (€/MWh)", 0.0, 20.0, 5.0, 0.5)
soc_init = st.sidebar.slider("Initial SOC (%)", 0, 100, 50) / 100.0

# --- Main UI ---
st.title("🔋 German BESS Co-Optimization Dashboard")
st.markdown("Optimize battery scheduling across EPEX Spot and aFRR markets.")

if st.button("🚀 Run Optimization", type="primary"):
    config = {
        'P_max': p_max, 'E_max': e_max, 'SOC_min_pct': 0.10, 'SOC_max_pct': 0.90,
        'SOC_init_pct': soc_init, 'eta_ch': 0.95, 'eta_dis': 0.95, 'deg_cost': deg_cost_val, 'afrr_dur_buffer': 0.5
    }
    
    df_market = create_market_data()
    
    with st.spinner('Running MILP Optimization via OR-Tools...'):
        df_results, status, obj_val = solve_bess_co_optimization(df_market, config)
    
    if status == "Optimal":
        st.success(f"Optimization Status: **{status}**")
        kpis = calculate_kpis(df_results, obj_val, config)
        
        # ذخیره فایل‌ها در پوشه (برای بک‌آپ سیستم محلی)
        os.makedirs('outputs', exist_ok=True)
        df_results.to_csv('outputs/bess_co_optimization_results.csv', index=False)
        
        # --- KPI Cards ---
        st.subheader("💰 Financial KPIs")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Daily Net Profit", f"€ {kpis['Net Profit']:,.0f}")
        col2.metric("Spot Revenue", f"€ {kpis['Spot Revenue']:,.0f}")
        col3.metric("aFRR Revenue", f"€ {kpis['aFRR Revenue']:,.0f}")
        col4.metric("Degradation Cost", f"€ -{kpis['Degradation Cost']:,.0f}")
        
        st.subheader("⚙️ Technical KPIs")
        col5, col6, col7 = st.columns(3)
        col5.metric("Equivalent Full Cycles", f"{kpis['EFC']:.2f}")
        col6.metric("Avg Inverter Utilization", f"{kpis['Inverter Utilization']:.1f} %")
        col7.metric("Final SOC", f"{df_results['SOC_Pct'].iloc[-1]:.1f} %")
        
        # --- Plots ---
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1)
        fig.add_trace(go.Scatter(x=df_results['Hour'], y=df_results['Spot_DA_EUR_MWh'], name='Spot Price', mode='lines+markers', line=dict(color='blue')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_results['Hour'], y=df_results['aFRR_Pos_EUR_MW'], name='aFRR Pos Price', mode='lines', line=dict(color='green', dash='dash')), row=1, col=1)
        
        fig.add_trace(go.Bar(x=df_results['Hour'], y=df_results['P_discharge_MW'], name='Discharge (MW)', marker_color='orange'), row=2, col=1)
        fig.add_trace(go.Bar(x=df_results['Hour'], y=-df_results['P_charge_MW'], name='Charge (MW)', marker_color='lightblue'), row=2, col=1)
        fig.add_trace(go.Scatter(x=df_results['Hour'], y=df_results['SOC_Pct'], name='SOC (%)', mode='lines+markers', line=dict(color='purple', width=2), yaxis='y3'), row=2, col=1)
        
        fig.update_layout(height=600, template='plotly_white', barmode='relative', hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("📊 View Raw Results Dataframe"):
            st.dataframe(df_results, use_container_width=True)
            
    else:
        st.error(f"Optimization failed. Status: {status}")
