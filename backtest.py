import numpy as np
import pandas as pd
from models import run_monte_carlo_simulation
from strategy import calculate_gto_spread

def run_full_backtest(df_data, close_col, p_matrix, State_Drift_list, market_volatility_val,
                      mc_steps, mc_sims, bs_pct, rp_mult, is_sens, mds_pct,
                      ts_usd, ef_rate, fr_prob, n_minutes):
    """Executes the simulation and calculates performance metrics."""
    test_data = df_data.tail(n_minutes)
    inventory = 0
    history_dashboard_data = []

    dashboard_total_trades_filled = 0
    dashboard_gross_spread_profit_usd = 0.0
    dashboard_total_fees_paid_usd = 0.0
    dashboard_winning_trades = 0
    dashboard_all_trade_profits = []
    dashboard_running_net_profit_from_trades = 0.0

    for index, row in test_data.iterrows():
        current_price = row[close_col]
        current_state = int(row['State'])

        risk_premium_value = run_monte_carlo_simulation(
            current_state, current_price, mc_steps, mc_sims, State_Drift_list, market_volatility_val
        )

        inventory += np.random.choice([-1, 0, 1], p=p_matrix[current_state])

        bid_price, ask_price = calculate_gto_spread(
            current_price, risk_premium_value, inventory,
            bs_pct, rp_mult, is_sens, mds_pct
        )

        is_trade_filled = False
        trade_net_profit = 0.0

        market_hit = np.random.choice([True, False], p=[fr_prob, 1 - fr_prob])

        if market_hit:
            is_trade_filled = True
            dashboard_total_trades_filled += 1
            trade_gross_profit = ((ask_price - bid_price) / current_price) * ts_usd
            dashboard_gross_spread_profit_usd += trade_gross_profit

            trade_fees = ts_usd * ef_rate
            dashboard_total_fees_paid_usd += trade_fees

            trade_net_profit = trade_gross_profit - trade_fees
            dashboard_all_trade_profits.append(trade_net_profit)

            if trade_net_profit > 0:
                dashboard_winning_trades += 1

            dashboard_running_net_profit_from_trades += trade_net_profit

        history_dashboard_data.append({
            'Timestamp': index,
            'Market Price': current_price,
            'GTO Bid (Buy)': bid_price,
            'GTO Ask (Sell)': ask_price,
            'Market State': current_state,
            'Risk Premium': risk_premium_value,
            'Is Trade Filled': is_trade_filled,
            'Trade Net Profit': trade_net_profit,
            'Cumulative Trade Net Profit': dashboard_running_net_profit_from_trades
        })

    df_dashboard = pd.DataFrame(history_dashboard_data)

    if df_dashboard.empty:
        return None, 0, 0, 0 

    initial_price = df_dashboard['Market Price'].iloc[0]
    final_price = df_dashboard['Market Price'].iloc[-1]

    position_size_in_units = 0 if final_price == 0 else (inventory * ts_usd) / final_price
    inventory_pnl_usd = position_size_in_units * (final_price - initial_price)
    
    net_profit_usd = dashboard_gross_spread_profit_usd + inventory_pnl_usd - dashboard_total_fees_paid_usd
    win_rate = (dashboard_winning_trades / dashboard_total_trades_filled) * 100 if dashboard_total_trades_filled > 0 else 0

    # Calculate Risk-to-Reward Ratio
    risk_to_reward_ratio = 0.0
    if dashboard_all_trade_profits:
        winning_profits = [p for p in dashboard_all_trade_profits if p > 0]
        losing_losses = [abs(p) for p in dashboard_all_trade_profits if p <= 0]
        
        avg_winning_profit = np.mean(winning_profits) if winning_profits else 0
        avg_losing_loss = np.mean(losing_losses) if losing_losses else 0

        if avg_losing_loss > 0:
            risk_to_reward_ratio = avg_winning_profit / avg_losing_loss
        else:
            risk_to_reward_ratio = float('inf')

    return df_dashboard, net_profit_usd, win_rate, risk_to_reward_ratio