# src/visualization.py

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

def create_market_dashboard(df_results, config):
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=(
            "<b>1. German Market Price Signals (Spot vs. aFRR Capacity)</b>",
            "<b>2. BESS Power Dispatch & Reserve Allocation</b>",
            "<b>3. Battery State of Charge (SOC) & Cumulative Revenue Stacking</b>"
        ),
        specs=[[{"secondary_y": True}], [{"secondary_y": False}], [{"secondary_y": True}]]
    )

    time_labels = [f"{h:02d}:00" for h in df_results['Hour']]

    # Chart 1: Market Prices
    fig.add_trace(go.Scatter(x=time_labels, y=df_results['Spot_DA_EUR_MWh'], name="Spot Price (€/MWh)",
                             line=dict(color='#2b5c8f', width=2.5)), row=1, col=1, secondary_y=False)
    fig.add_trace(go.Scatter(x=time_labels, y=df_results['aFRR_Pos_EUR_MW'], name="+aFRR Capacity Price (€/MW)",
                             line=dict(color='#2ca02c', dash='dot', width=2)), row=1, col=1, secondary_y=True)
    fig.add_trace(go.Scatter(x=time_labels, y=df_results['aFRR_Neg_EUR_MW'], name="-aFRR Capacity Price (€/MW)",
                             line=dict(color='#d62728', dash='dot', width=2)), row=1, col=1, secondary_y=True)

    # Chart 2: Dispatch & Reserves
    fig.add_trace(go.Bar(x=time_labels, y=df_results['P_discharge_MW'], name="Spot Discharge (MW)",
                         marker_color='#1f77b4'), row=2, col=1)
    fig.add_trace(go.Bar(x=time_labels, y=-df_results['P_charge_MW'], name="Spot Charge (MW)",
                         marker_color='#ff7f0e'), row=2, col=1)
    fig.add_trace(go.Scatter(x=time_labels, y=df_results['R_aFRR_Pos_MW'], name="+aFRR Committed (MW)",
                             mode='lines+markers', line=dict(color='#2ca02c', width=2.5)), row=2, col=1)
    fig.add_trace(go.Scatter(x=time_labels, y=df_results['R_aFRR_Neg_MW'], name="-aFRR Committed (MW)",
                             mode='lines+markers', line=dict(color='#d62728', width=2.5)), row=2, col=1)

    # Chart 3: SOC & Cumulative Profit
    hourly_profit = (
        (df_results['Spot_DA_EUR_MWh'] * df_results['P_discharge_MW'] - df_results['Spot_DA_EUR_MWh'] * df_results['P_charge_MW']) +
        (df_results['aFRR_Pos_EUR_MW'] * df_results['R_aFRR_Pos_MW']) +
        (df_results['aFRR_Neg_EUR_MW'] * df_results['R_aFRR_Neg_MW']) -
        (config['deg_cost'] * (df_results['P_charge_MW'] + df_results['P_charge_MW']))
    )
    cumulative_profit = np.cumsum(hourly_profit)

    fig.add_trace(go.Scatter(x=time_labels, y=df_results['SOC_Pct'], name="Battery SOC (%)",
                             line=dict(color='#9467bd', width=3), fill='tozeroy', fillcolor='rgba(148, 103, 189, 0.15)'), row=3, col=1, secondary_y=False)
    fig.add_trace(go.Scatter(x=time_labels, y=cumulative_profit, name="Cumulative Net Profit (€)",
                             line=dict(color='#00cc96', width=3)), row=3, col=1, secondary_y=True)

    # Layout Customization
    fig.update_layout(
        height=1100,
        title_text="<b>Utility-Scale BESS Multi-Market Co-Optimization (EPEX Spot DA + Regelleistung aFRR)</b>",
        title_font_size=15,
        title_x=0.5,
        margin=dict(t=120, b=60, l=60, r=220),
        hovermode="x unified",
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.95,
            xanchor="left",
            x=1.02,
            font=dict(color="black", size=11),
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="rgba(0, 0, 0, 0.2)",
            borderwidth=1
        )
    )

    fig.update_yaxes(title_text="Spot Price (€/MWh)", row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text="aFRR Cap. (€/MW)", row=1, col=1, secondary_y=True)
    fig.update_yaxes(title_text="Power/Reserve (MW)", row=2, col=1)
    fig.update_yaxes(title_text="Battery SOC (%)", row=3, col=1, secondary_y=False)
    fig.update_yaxes(title_text="Cum. Profit (€)", row=3, col=1, secondary_y=True)

    return fig
