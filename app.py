# app.py

import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.optimization_model import solve_bess_co_optimization

def create_market_data():
    """تولید داده‌های نمونه در صورتی که فایل دیتای واقعی در دسترس نباشد"""
    hours = list(range(24))
    np.random.seed(42)
    # قیمت‌های فرضی اسپات و رزرو
    spot_prices = np.random.uniform(30, 150, 24)
    afrr_pos = np.repeat(np.random.uniform(10, 50, 6), 4)
    afrr_neg = np.repeat(np.random.uniform(10, 50, 6), 4)
    
    return pd.DataFrame({
        'Hour': hours,
        'Spot_DA_EUR_MWh': spot_prices,
        'aFRR_Pos_Cap_EUR_MW': afrr_pos,
        'aFRR_Neg_Cap_EUR_MW': afrr_neg
    })

def calculate_kpis(df_results, obj_val, config):
    """محاسبه شاخص‌های کلیدی عملکرد (KPIs) مالی و فنی"""
    # 1. Financial KPIs
    spot_rev = ((df_results['P_discharge_MW'] - df_results['P_charge_MW']) * df_results['Spot_DA_EUR_MWh']).sum()
    
    # برای aFRR قیمت‌ها و رزروها را فقط در ساعت شروع هر بلاک ۴ ساعته حساب می‌کنیم
    df_blocks = df_results.groupby('Block_4h').first()
    afrr_rev = (4 * (df_blocks['R_aFRR_Pos_MW'] * df_blocks['aFRR_Pos_EUR_MW'] + 
                     df_blocks['R_aFRR_Neg_MW'] * df_blocks['aFRR_Neg_EUR_MW'])).sum()
    
    deg_cost = (config['deg_cost'] * (df_results['P_charge_MW'] + df_results['P_discharge_MW'])).sum()
    
    # 2. Technical KPIs
    efc = df_results['P_discharge_MW'].sum() / config['E_max']
    
    # ضریب استفاده از اینورتر (بیشترین درگیری اینورتر در حالت شارژ یا دشارژ در هر ساعت)
    inverter_usage = np.maximum(
        df_results['P_discharge_MW'] + df_results['R_aFRR_Pos_MW'],
        df_results['P_charge_MW'] + df_results['R_aFRR_Neg_MW']
    )
    avg_utilization = (inverter_usage.mean() / config['P_max']) * 100
    
    min_soc = df_results['SOC_Pct'].min()
    max_soc = df_results['SOC_Pct'].max()
    final_soc = df_results['SOC_Pct'].iloc[-1]
    
    return {
        'Net Profit': obj_val,
        'Spot Revenue': spot_rev,
        'aFRR Revenue': afrr_rev,
        'Degradation Cost': deg_cost,
        'EFC': efc,
        'Inverter Utilization': avg_utilization,
        'Min SOC': min_soc,
        'Max SOC': max_soc,
        'Final SOC': final_soc
    }

def main():
    print("--- Starting German BESS Co-Optimization Pipeline ---")
    
    # تنظیمات سیستم باتری (BESS Config)
    BESS_CONFIG = {
        'P_max': 10.0, 'E_max': 20.0, 'SOC_min_pct': 0.10, 'SOC_max_pct': 0.90,
        'SOC_init_pct': 0.50, 'eta_ch': 0.95, 'eta_dis': 0.95, 'deg_cost': 5.0, 'afrr_dur_buffer': 0.5
    }
    
    df_market = create_market_data()
    
    # اجرای مدل بهینه‌سازی
    df_results, status, obj_val = solve_bess_co_optimization(df_market, BESS_CONFIG)
    
    if status != "Optimal":
        print(f"Warning: Optimization finished with status: {status}")
        return

    # محاسبه شاخص‌ها
    kpis = calculate_kpis(df_results, obj_val, BESS_CONFIG)
    
    # اطمینان از وجود پوشه خروجی
    os.makedirs('outputs', exist_ok=True)
    
    # ذخیره فایل CSV
    df_results.to_csv('outputs/bess_co_optimization_results.csv', index=False)
    
    # ---------------------------------------------------------
    # 1. تولید گزارش متنی (TXT) با درج KPI ها
    # ---------------------------------------------------------
    report_content = f"""==================================================
 GERMAN BESS CO-OPTIMIZATION SUMMARY REPORT
==================================================
Optimization Status: {status}

[ FINANCIAL KPIs ]
- Daily Net Profit:      € {kpis['Net Profit']:,.2f}
- Spot Market Revenue:   € {kpis['Spot Revenue']:,.2f}
- aFRR Market Revenue:   € {kpis['aFRR Revenue']:,.2f}
- Total Degradation Cost:€ {kpis['Degradation Cost']:,.2f}

[ TECHNICAL KPIs ]
- Equivalent Full Cycles (EFC): {kpis['EFC']:.2f} cycles
- Avg Inverter Utilization:     {kpis['Inverter Utilization']:.1f} %
- SOC Operating Range:          {kpis['Min SOC']:.1f}% to {kpis['Max SOC']:.1f}%
- Final SOC (Hour 23):          {kpis['Final SOC']:.1f}%
=================================================="""
    
    with open('outputs/optimization_summary_report.txt', 'w', encoding='utf-8') as f:
        f.write(report_content)

    # ---------------------------------------------------------
    # 2. تولید داشبورد HTML و تزریق کارت‌های KPI
    # ---------------------------------------------------------
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        subplot_titles=('Market Prices (EUR/MWh & EUR/MW)', 'BESS Operation & SOC (%)'))
    
    # پلات قیمت‌ها
    fig.add_trace(go.Scatter(x=df_results['Hour'], y=df_results['Spot_DA_EUR_MWh'], name='Spot Price', mode='lines+markers', line=dict(color='blue')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_results['Hour'], y=df_results['aFRR_Pos_EUR_MW'], name='aFRR Pos Price', mode='lines', line=dict(color='green', dash='dash')), row=1, col=1)
    
    # پلات عملیات
    fig.add_trace(go.Bar(x=df_results['Hour'], y=df_results['P_discharge_MW'], name='Discharge (MW)', marker_color='orange'), row=2, col=1)
    fig.add_trace(go.Bar(x=df_results['Hour'], y=-df_results['P_charge_MW'], name='Charge (MW)', marker_color='lightblue'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df_results['Hour'], y=df_results['SOC_Pct'], name='SOC (%)', mode='lines+markers', line=dict(color='purple', width=2), yaxis='y3'), row=2, col=1)
    
    fig.update_layout(height=700, template='plotly_white', barmode='relative', hovermode='x unified')
    
    # ساخت فایل HTML نهایی با استایل مدرن
    html_template = f"""
    <html>
    <head>
        <title>BESS Optimization Dashboard</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; margin: 0; padding: 20px; }}
            .header {{ text-align: center; color: #2c3e50; margin-bottom: 30px; }}
            .kpi-container {{ display: flex; justify-content: space-around; flex-wrap: wrap; gap: 20px; margin-bottom: 30px; }}
            .kpi-card {{ background: #fff; border-radius: 10px; padding: 20px; width: 45%; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-top: 4px solid #3498db; }}
            .kpi-card.tech {{ border-top-color: #e67e22; }}
            .kpi-card h3 {{ margin-top: 0; color: #34495e; font-size: 1.2rem; border-bottom: 1px solid #ecf0f1; padding-bottom: 10px; }}
            .kpi-row {{ display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 1rem; color: #555; }}
            .kpi-value {{ font-weight: bold; color: #2c3e50; }}
            .plot-container {{ background: #fff; border-radius: 10px; padding: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔋 German BESS Co-Optimization Dashboard</h1>
        </div>
        <div class="kpi-container">
            <div class="kpi-card">
                <h3>💰 Financial Performance</h3>
                <div class="kpi-row"><span>Daily Net Profit:</span> <span class="kpi-value">€ {kpis['Net Profit']:,.2f}</span></div>
                <div class="kpi-row"><span>Spot DA Revenue:</span> <span class="kpi-value">€ {kpis['Spot Revenue']:,.2f}</span></div>
                <div class="kpi-row"><span>aFRR Revenue:</span> <span class="kpi-value">€ {kpis['aFRR Revenue']:,.2f}</span></div>
            </div>
            <div class="kpi-card tech">
                <h3>⚙️ Technical & Operational</h3>
                <div class="kpi-row"><span>Equivalent Full Cycles (EFC):</span> <span class="kpi-value">{kpis['EFC']:.2f}</span></div>
                <div class="kpi-row"><span>Avg Inverter Utilization:</span> <span class="kpi-value">{kpis['Inverter Utilization']:.1f}%</span></div>
                <div class="kpi-row"><span>SOC Range:</span> <span class="kpi-value">{kpis['Min SOC']:.1f}% - {kpis['Max SOC']:.1f}%</span></div>
            </div>
        </div>
        <div class="plot-container">
            {fig.to_html(full_html=False, include_plotlyjs='cdn')}
        </div>
    </body>
    </html>
    """
    
    with open('outputs/bess_market_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html_template)
        
    print(f"Optimization Status: {status}")
    print(f"Total Objective Value: {obj_val:,.2f} EUR")
    print("Pipeline executed successfully. Outputs saved to /outputs/")

if __name__ == "__main__":
    main()
