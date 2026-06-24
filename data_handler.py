import pandas as pd
import yfinance as yf

def load_and_prep_data(ticker, period='5d', interval='1m', threshold=0.0001):
    """Downloads yfinance data and calculates basic market states."""
    data = yf.download(ticker, period=period, interval=interval)
    df = pd.DataFrame(data)

    # FIX: Return a default string for close_col alongside the empty DataFrame
    if df.empty:
        return df, 'Close'

    # Clean columns for multi-index issues from yfinance
    df.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in df.columns.values]
    
    # Identify the close column dynamically based on the ticker
    close_col = f'Close_{ticker}' if f'Close_{ticker}' in df.columns else 'Close'

    df['Price_Change'] = df[close_col].pct_change()
    df['State'] = 1  # Balance hold
    df.loc[df['Price_Change'] < -threshold, 'State'] = 0  # Sell heavy
    df.loc[df['Price_Change'] > threshold, 'State'] = 2   # Buy heavy

    # Drop NaN values resulting from pct_change
    df.dropna(subset=['Price_Change'], inplace=True)
    
    return df, close_col