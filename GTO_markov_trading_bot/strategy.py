def calculate_gto_spread(current_price, risk_premium, inventory_imbalance, 
                         base_spread_percentage=0.001, 
                         risk_premium_multiplier=0.15, 
                         inventory_skew_sensitivity=0.0002, 
                         min_display_spread_percentage=0.0002):
    """Calculates risk-adjusted GTO bid/ask spreads."""
    
    raw_risk_adjusted_spread_percentage = base_spread_percentage + (risk_premium / current_price) * risk_premium_multiplier
    total_spread_percentage = max(raw_risk_adjusted_spread_percentage, min_display_spread_percentage)

    # Inventory adjustment
    inventory_price_offset = inventory_imbalance * current_price * inventory_skew_sensitivity
    adjusted_mid_price = current_price - inventory_price_offset

    half_spread_abs = adjusted_mid_price * (total_spread_percentage / 2)
    bid_price = adjusted_mid_price - half_spread_abs
    ask_price = adjusted_mid_price + half_spread_abs

    return bid_price, ask_price