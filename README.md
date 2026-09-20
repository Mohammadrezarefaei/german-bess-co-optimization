# 🔋 German BESS Co-Optimization in DA Spot & aFRR Markets

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://german-bess-co-optimization-9mlfajfycdsubtkxim8gkk.streamlit.app/)
![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![Solver](https://img.shields.io/badge/Solver-Google_OR--Tools_(CBC)-orange)
![Build Status](https://img.shields.io/badge/Tests-Passing-brightgreen)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 📌 Executive Summary
This project presents a professional-grade **Mixed-Integer Linear Programming (MILP)** framework for the day-ahead co-optimization of a Utility-Scale Battery Energy Storage System (BESS) in the German electricity market. 

The algorithm determines the optimal bidding strategy for a BESS participating simultaneously in the **EPEX Day-Ahead Spot Market** (energy arbitrage) and the **German aFRR Market** (secondary frequency control reserve), maximizing total daily net profit while strictly adhering to hardware and regulatory constraints.

---

## 🚀 Live Interactive Dashboard
Experience the optimization engine in real-time. Adjust BESS hardware parameters and market conditions to see how the MILP solver adapts the bidding strategy.

👉 **[Launch the Streamlit Web Application](https://german-bess-co-optimization-9mlfajfycdsubtkxim8gkk.streamlit.app/)**

---

## 📊 Key Performance Indicators (KPIs)
The mathematical model evaluates both financial viability and technical battery health. Based on standard utility-scale testing parameters (10 MW / 20 MWh), the framework achieved the following daily performance targets:

### 💰 Financial Performance
| KPI | Description | Sample Result |
| :--- | :--- | :--- |
| **Net Daily Profit** | Total objective function value after degradation penalties | **€ 14,701.95** |
| **Spot Market Revenue** | Income generated via pure energy arbitrage | Dynamic |
| **aFRR Revenue** | Capacity reservation income (Pos & Neg) | Dynamic |
| **Degradation Cost** | Financial penalty modeled for battery cycle aging | € 5.0 / MWh |

### ⚙️ Technical & Operational Metrics
| KPI | Description | Constraint / Target |
| :--- | :--- | :--- |
| **Equivalent Full Cycles (EFC)** | Total discharged energy / Nominal Capacity | Monitored to prevent rapid aging |
| **Inverter Utilization** | Avg % of inverter capacity used in 24h | Maximize hardware efficiency |
| **SOC Operating Range** | Strict boundaries to maintain battery chemistry | `10% ≤ SOC ≤ 90%` |
| **SOC Neutrality** | Ensuring final SOC matches initial SOC for the next day | `SOC(t=23) ≥ SOC(init)` |

---

## 🧠 The Mathematical Model (MILP)
The core optimization engine is built using **Google OR-Tools** (incorporating the CBC solver), bypassing the need for commercial solvers. The formulation involves:

*   **Objective Function:** `Maximize (Spot Revenue + aFRR Reserve Revenue - Degradation Costs)`
*   **Decision Variables:** Continuous variables for charge/discharge power, positive/negative aFRR reserve allocations, and State of Charge (SOC). Binary variables ensure mutually exclusive charging and discharging states.
*   **Key Constraints:**
    *   **Inverter Sharing Limits:** `P_discharge + R_aFRR_Pos ≤ P_max`
    *   **Energy Backing Buffers:** Reserving adequate physical energy (MWh) to fulfill activated aFRR capacity blocks without violating SOC limits.
    *   **Charge/Discharge Efficiency:** Round-trip losses explicitly modeled (`η = 0.95`).

---

## 📈 Visual Analytics
The interactive dashboard uses **Plotly** to provide a deep dive into the operational profile of the BESS:
1.  **Price Overlay:** Compares Day-Ahead Spot volatility with aFRR capacity prices to justify the solver's market allocation.
2.  **Dispatch Schedule:** Bar charts detailing exact MW allocations for charging, discharging, and reserving capacity per hour.
3.  **SOC Trajectory:** A continuous line graph tracking the State of Charge throughout the 24-hour cycle, proving constraint adherence.

---

## 📁 Repository Structure
```text
.
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── src/
│   ├── __init__.py
│   └── optimization_model.py   # Core MILP OR-Tools mathematical formulation
├── tests/
│   ├── __init__.py
│   ├── test_market_data.py     # Unit tests for data ingestion
│   └── test_optimization.py    # Unit tests for constraint validation
├── outputs/                    # Export directory for CSV, HTML, and TXT reports
└── README.md
