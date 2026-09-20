# 🔋 German BESS Co-Optimization Framework

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://german-bess-co-optimization-9mlfajfycdsubtkxim8gkk.streamlit.app/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Optimization](https://img.shields.io/badge/Solver-Google_OR--Tools_(CBC)-orange.svg)](https://developers.google.com/optimization)
[![Tests](https://img.shields.io/badge/pytest-passing-success.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A robust Mixed-Integer Linear Programming (MILP) framework designed to optimize the 24-hour dispatch schedule of a utility-scale Battery Energy Storage System (BESS) participating simultaneously in the **German EPEX Spot (Day-Ahead)** and **aFRR (Automatic Frequency Restoration Reserve)** markets.

Deployed interactively via Streamlit: **[Live Dashboard](https://german-bess-co-optimization-9mlfajfycdsubtkxim8gkk.streamlit.app/)**

---

## 🎯 Project Overview & Objective

Operating a BESS purely for energy arbitrage (buy low, sell high) leaves hardware underutilized. This project implements a **co-optimization strategy** that allows the battery to dynamically allocate its power capacity between the Day-Ahead market and the reserve market (aFRR - Positive and Negative). 

The MILP algorithm considers critical technical constraints, degradation costs, and SOC management to maximize daily net profit while ensuring complete hardware safety and market compliance.

---

## 📊 Key Performance Indicators (KPIs)

The optimization engine outputs precise metrics to evaluate both commercial viability and technical health. Based on a standard 10 MW / 20 MWh configuration:

### 💰 Financial Performance
* **Daily Net Profit:** Maximized total revenue minus degradation penalties.
* **Revenue Split:** Transparent tracking of Spot Market Arbitrage vs. aFRR Capacity Remuneration.
* **Total Degradation Cost:** Financial penalization incorporated directly into the objective function to prevent destructive cycling.

### ⚙️ Technical & Operational Metrics
* **Equivalent Full Cycles (EFC):** Monitors battery lifespan impact per day.
* **Inverter Utilization:** Measures how effectively the 10 MW power electronics are utilized across the 24-hour horizon.
* **SOC Operating Range & Neutrality:** Ensures the battery stays within the safe 10%-90% margins and returns to its initial State of Charge by midnight to guarantee continuous daily operation.

---

## 🛠️ Technical Architecture

* **Mathematical Modeling:** Google OR-Tools (MILP) with the CBC solver.
* **Data Manipulation:** `pandas`, `numpy`.
* **Data Visualization:** `plotly.graph_objects` for interactive financial and technical plotting.
* **Web Deployment:** `streamlit` for the interactive cloud-hosted UI.
* **Quality Assurance:** `pytest` for unit testing model constraints and boundaries.

---

## 📂 Project Structure

```text
german-bess-co-optimization/
├── app.py                      # Main Streamlit application and UI logic
├── requirements.txt            # Environment dependencies
├── src/
│   └── optimization_model.py   # Core MILP OR-Tools optimization engine
├── tests/
│   └── test_optimization.py    # Pytest unit tests for BESS constraints
├── outputs/                    # Local storage for CSV, HTML, and TXT reports
└── README.md
