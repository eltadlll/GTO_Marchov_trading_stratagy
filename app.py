import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from data_handler import load_and_prep_data
from models import calculate_markov_params
from backtest import run_full_backtest

# Set page config
st.set_page_config(layout="wide", page_title="GTO Market Making Strategy Dashboard")

st.title("📊 GTO Market Making Strategy Dashboard")
st.write("Adjust parameters in the sidebar to dynamically tune the Markov-Monte Carlo-GTO Engine.")

# --- Sidebar for Parameter Tuning ---
st.sidebar.header("1. Data Configuration")
ticker = st.sidebar.text_input("Asset Ticker (e.g., ETH-USD)", "ETH-USD")
period = st.sidebar.selectbox("Data Period", ["1d", "5d", "1mo", "3mo", "6mo", "1y"], index=1)
interval = st.sidebar.selectbox("Data Interval", ["1m", "2m", "5m", "15m", "30m", "60m"], index=0)

st.sidebar.header("2. Market State Classification")
threshold = st.sidebar.slider("Price Change Threshold", min_value=0.00001, max_value=0.001, value=0.0001, step=0.00001, format="%.5f")

# Load Data via our handler
df, close_col = load_and_prep_data(ticker, period, interval, threshold)

if df.empty:
    st.error("Could not load data for the specified ticker/period/interval. Please check your inputs.")
    st.stop()

# Calculate Markov params
p, State_Drift, market_volatility = calculate_markov_params(df)

# --- Additional Sidebar Parameters ---
st.sidebar.header("3. Monte Carlo Simulation")
monte_carlo_steps = st.sidebar.slider("MC Steps", min_value=5, max_value=20, value=10, step=1)
monte_carlo_simulations = st.sidebar.slider("MC Simulations", min_value=10000, max_value=100000, value=50000, step=10000)

st.sidebar.header("4. GTO Spread Parameters")
base_spread_percentage = st.sidebar.slider("Base Spread Percentage", min_value=0.0001, max_value=0.005, value=0.001, step=0.0001, format="%.4f")
risk_premium_multiplier = st.sidebar.slider("Risk Premium Multiplier", min_value=0.0, max_value=0.5, value=0.15, step=0.01)
inventory_skew_sensitivity = st.sidebar.slider("Inventory Skew Sensitivity", min_value=0.00001, max_value=0.0005, value=0.0002, step=0.00001, format="%.5f")
min_display_spread_percentage = st.sidebar.slider("Min Display Spread Percentage", min_value=0.0001, max_value=0.001, value=0.0002, step=0.00001, format="%.5f")

st.sidebar.header("5. Backtesting Configuration")
trading_size_usd = st.sidebar.slider("Trading Size (USD)", min_value=1000.0, max_value=50000.0, value=10000.0, step=1000.0)
exchange_fee_rate = st.sidebar.slider("Exchange Fee Rate", min_value=0.0001, max_value=0.005, value=0.001, step=0.0001, format="%.4f")
fill_rate_probability = st.sidebar.slider("Fill Rate Probability", min_value=0.1, max_value=1.0, value=0.4, step=0.05)
backtest_minutes = st.sidebar.slider("Backtest Last N Minutes", min_value=10, max_value=min(len(df)-1, 120), value=60, step=1)

# --- Run Backtest ---
st.write("---")
if st.button("🚀 Run Live Engine Simulation", use_container_width=True):
    with st.spinner("Running Monte Carlo chains & generating spreads..."):
        df_dashboard, net_profit, win_rate, r_r_ratio = run_full_backtest(
            df, close_col, p, State_Drift, market_volatility,
            monte_carlo_steps, monte_carlo_simulations,
            base_spread_percentage, risk_premium_multiplier, inventory_skew_sensitivity, min_display_spread_percentage,
            trading_size_usd, exchange_fee_rate, fill_rate_probability,
            backtest_minutes
        )

    if df_dashboard is not None:
        # --- Top-level Performance Indicators ---
        st.subheader("📈 Core Strategy Performance Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Net Bot System Outcome", f"${net_profit:.2f}", delta=f"{'Profit' if net_profit >= 0 else 'Loss'}")
        col2.metric("Execution Win Rate", f"{win_rate:.2f}%")
        col3.metric("Measured Risk/Reward Ratio", f"{r_r_ratio:.2f}" if r_r_ratio != float('inf') else "∞ (No Losses)")

        st.write("---")
        st.subheader("🔍 Interactive Visualization Engine")

        # --- Plot 1: 2D Price tracking & Active GTO Spread Boundaries ---
        st.markdown("#### Active Order Book Boundary Tracking")
        fig_spread = go.Figure()
        # Lower boundary (Bid)
        fig_spread.add_trace(go.Scatter(
            x=df_dashboard['Timestamp'], y=df_dashboard['GTO Bid (Buy)'],
            mode='lines', line=dict(width=0), showlegend=False, name="Bid Threshold"
        ))
        # Upper boundary (Ask) + Fill Area to the Bid line
        fig_spread.add_trace(go.Scatter(
            x=df_dashboard['Timestamp'], y=df_dashboard['GTO Ask (Sell)'],
            mode='lines', line=dict(width=0), fill='tonexty',
            fillcolor='rgba(0, 128, 128, 0.15)', name="Optimal GTO Spread Boundary"
        ))
        # Mid Market Price Line
        fig_spread.add_trace(go.Scatter(
            x=df_dashboard['Timestamp'], y=df_dashboard['Market Price'],
            mode='lines', line=dict(color='black', width=2), name=f"Real {ticker} Mid Price"
        ))
        fig_spread.update_layout(
            xaxis_title="Time Ticks (Minutes)", yaxis_title="Asset Value ($)",
            hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_spread, use_container_width=True)

        # --- Plot 2: Cumulative Net Profit Trend & Execution Matches ---
        st.markdown("#### Cumulative Realized Yield Curve")
        fig_pnl = go.Figure()
        fig_pnl.add_trace(go.Scatter(
            x=df_dashboard['Timestamp'], y=df_dashboard['Cumulative Trade Net Profit'],
            mode='lines', line=dict(color='#0026ff', width=2.5), name="Cumulative Net PnL"
        ))
        # Overlay actual order matches
        trades_filled = df_dashboard[df_dashboard['Is Trade Filled'] == True]
        fig_pnl.add_trace(go.Scatter(
            x=trades_filled['Timestamp'], y=trades_filled['Cumulative Trade Net Profit'],
            mode='markers', marker=dict(color='red', size=8, symbol='circle'), name="Order Filled Match"
        ))
        # Reference Zero Line
        fig_pnl.add_trace(go.Scatter(
            x=df_dashboard['Timestamp'], y=[0]*len(df_dashboard),
            mode='lines', line=dict(color='rgba(255,0,0,0.4)', dash='dash'), name="Baseline Margin"
        ))
        fig_pnl.update_layout(
            xaxis_title="Time Ticks (Minutes)", yaxis_title="Cumulative Net Profit ($)",
            hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_pnl, use_container_width=True)

        # --- Plot 3: 3D Quant Space Scatter Plot ---
        st.markdown("#### 3D State Engine Dynamics Space")
        st.caption("Rotate, pan, and zoom inside this 3D map to see how your Monte Carlo Risk Premiums and Asset Prices generated Net Profits across different structural Market States.")
        
        # Mapping text names to state numbers for clean chart legends
        state_map = {0: "0: Sell Heavy", 1: "1: Balance Hold", 2: "2: Buy Heavy"}
        df_dashboard['State Label'] = df_dashboard['Market State'].map(state_map)
        
        fig_3d = px.scatter_3d(
            df_dashboard,
            x='Market Price',
            y='Risk Premium',
            z='Cumulative Trade Net Profit',
            color='State Label',
            color_discrete_map={"0: Sell Heavy": "#ef553b", "1: Balance Hold": "#636efa", "2: Buy Heavy": "#00cc96"},
            labels={
                'Market Price': 'Asset Price ($)',
                'Risk Premium': 'MC Risk Premium ($)',
                'Cumulative Trade Net Profit': 'Total Profit ($)'
            }
        )
        fig_3d.update_layout(
            margin=dict(l=0, r=0, b=0, t=30),
            scene=dict(
                xaxis=dict(backgroundcolor="rgba(0,0,0,0.05)", gridcolor="white", showbackground=True),
                yaxis=dict(backgroundcolor="rgba(0,0,0,0.05)", gridcolor="white", showbackground=True),
                zaxis=dict(backgroundcolor="rgba(0,0,0,0.05)", gridcolor="white", showbackground=True),
            ),
            legend=dict(title="Classified Market State", orientation="h", yanchor="bottom", y=0.9, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_3d, use_container_width=True)

        # --- Data Table Ledger ---
        st.write("---")
        st.subheader("📋 Raw Transaction Ledger Data Frame")
        st.dataframe(df_dashboard.drop(columns=['State Label']), use_container_width=True)