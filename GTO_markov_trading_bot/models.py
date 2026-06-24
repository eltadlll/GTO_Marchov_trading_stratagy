import numpy as np

def calculate_markov_params(df):
    """Calculates transition probabilities, state drift, and market volatility."""
    States = df['State'].values
    transition_count = np.zeros((3, 3))
    
    for t in range(len(States) - 1):
        transition_count[States[t], States[t+1]] += 1
        
    p = transition_count / transition_count.sum(axis=1, keepdims=True)

    State_Drift = [
        df[df['State'] == 0]['Price_Change'].mean(),
        df[df['State'] == 1]['Price_Change'].mean(),
        df[df['State'] == 2]['Price_Change'].mean()
    ]
    
    # Ensure drift values are not NaN
    State_Drift = [0.0 if np.isnan(d) else d for d in State_Drift]
    market_volatility = df['Price_Change'].std()

    return p, State_Drift, market_volatility

def run_monte_carlo_simulation(current_state, current_price, steps, simulations, State_Drift, market_volatility):
    """Simulates future price paths to calculate a risk premium."""
    drift = State_Drift[current_state]
    terminal_prices = np.zeros(simulations)
    
    for i in range(simulations):
        random_shocks = np.random.normal(0, 1, steps)
        price = current_price
        for shock in random_shocks:
            price *= np.exp((drift - 0.5 * market_volatility**2) + market_volatility * shock)
        terminal_prices[i] = price
        
    percentile_5th = np.percentile(terminal_prices, 5)
    return max(0, current_price - percentile_5th)