# GTO Market Making Strategy Dashboard

An interactive, modular quantitative trading terminal that builds a predictive Markov Chain transition matrix and pairs it with a multi-path Monte Carlo simulation engine to execute an inventory-skew-adjusted Game-Theoretic Optimal (GTO) market-making algorithm.
to try the app: https://gtomarchovtradingstratagy-rowddxycwxohtso3djf6r6.streamlit.app/

---

## System Architecture

The project has been refactored from a monolithic notebook architecture into a highly maintainable, discrete multi-file framework:

```text
gto-trading-engine/
│
├── data_handler.py     # Network session spoofing, yfinance ingest, and state classification
├── models.py           # Core mathematics: Markov transition matrices & Monte Carlo simulations
├── strategy.py         # Game-Theoretic Optimal (GTO) spread sizing & inventory skew adjustment
├── backtest.py         # Event loop ledger simulation, fee deductions, and absolute PnL tracking
├── app.py              # Front-end Streamlit UI engine with Plotly 2D/3D visualizations
└── requirements.txt    # Frozen environment dependencies

```

---

## Core Quantitative Framework

### 1. Markov State Micro-States

Asset price changes are continuously categorized into discrete market micro-states based on a user-defined percentage threshold:

* **State 0 (Sell Heavy):** $\Delta \text{Price} < -\text{threshold}$
* **State 1 (Balance Hold):** $-\text{threshold} \le \Delta \text{Price} \le \text{threshold}$
* **State 2 (Buy Heavy):** $\Delta \text{Price} > \text{threshold}$

The empirical transition counts are tracked sequentially and normalized row-by-row to build a state transition probability matrix $P$:

$$p_{i,j} = \frac{N_{i,j}}{\sum_{k=0}^{2} N_{i,k}}$$

### 2. Monte Carlo Risk Premium Projection

For each time tick, the system samples random market shocks drawn from a normal distribution $\mathcal{N}(0,1)$ to project thousands of potential future terminal prices using an asset drift model derived per state:

$$\text{Price}_t = \text{Price}_{t-1} \times \exp\left(\left(\mu_{\text{state}} - \frac{1}{2}\sigma^2\right)\Delta t + \sigma \sqrt{\Delta t} \, Z\right)$$

Where $\mu_{\text{state}}$ is the isolated mean price change of the current state, $\sigma$ is global market volatility, and $Z \sim \mathcal{N}(0,1)$. The dynamic risk premium is computed as the distance from the current mid-market price to the **5th percentile (Value-at-Risk)** of the simulated distribution.

### 3. Inventory-Skew Spread Calibration

To neutralize directional exposure, the mid-market price is shifted inversely to the accumulated inventory buffer before placing quotes:

$$\text{Adjusted Mid} = \text{Mid Price} - (\text{Inventory} \times \text{Mid Price} \times \lambda)$$

$$\text{Bid} = \text{Adjusted Mid} - \left(\text{Adjusted Mid} \times \frac{\text{Spread}_{\%}}{2}\right)$$

$$\text{Ask} = \text{Adjusted Mid} + \left(\text{Adjusted Mid} \times \frac{\text{Spread}_{\%}}{2}\right)$$

Where $\lambda$ represents the sensitivity to inventory imbalance.

---

##  Installation & Quick Start

### 1. Clone or Initialize the Directory

Ensure all five modular Python script files (`data_handler.py`, `models.py`, `strategy.py`, `backtest.py`, `app.py`) along with your `requirements.txt` are stored cleanly within a dedicated folder on your local drive.

### 2. Install Project Dependencies

Open your terminal inside the project directory and batch install the environment dependencies using pip:

```bash
pip install -r requirements.txt

```

### 3. Spin Up the App Engine

Launch the dashboard locally by initializing Streamlit directly through your terminal terminal prompt:

```bash
streamlit run app.py

```

---

##  Interactive UI Visualizations

Once booted, the terminal dashboard exposes three core interactive modules:

* **Active Order Book Boundary Tracking (2D):** A responsive, zoomable timeline that visualizes the asset's mid-market historical trail wrapped cleanly inside shaded teal GTO bid/ask liquidity boundaries.
* **Cumulative Realized Yield Curve (2D):** Tracks structural alpha accumulation over time, overlaying explicit red markers exactly when random market volatility spikes hit and fill an outstanding order quote.
* **3D State Engine Dynamics Space:** A rotatable, multi-dimensional scatter map charting Asset Price ($X$), Monte Carlo Risk Premium ($Y$), and Net Profit ($Z$) styled completely across your three classified structural market states. Use this space to visually inspect clustering patterns where the algorithm performs optimally.

---


