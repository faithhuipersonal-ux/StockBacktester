import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from plotly.subplots import make_subplots
from datetime import datetime, timedelta



st.set_page_config(
	page_title = "Stock Backtester",
	page_icon = "📈",
	layout = "wide",
	initial_sidebar_state = "expanded"
)

st.markdown("""
<style>
/*Main page spacing */
.block-container {
	max-width: 1700px;
	padding: 2rem 3 rem;
}

/* Widen the sidebar */
section[data-testid="stSidebar"] {
	max-width: 310px;
}

section[data-tesid="stSidebar"] label {
	font-size: 17px;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] .stMarkdown {
	font-size: 16px;
}

.stTextInput input label,
.stDateInput input label,
.stMultiSelect label {
	font-size: 17px !important;
}

.stButton button {
	min-height: 48px;
	font-size: 17px;
	
	
}

h1 {
	font-size: 2.6rem !important;
}
	
h2 {
	font-size: 1.9rem !important;
}

h3 {
	font-size: 1.5 rem !important;
}

div[data-testid="stVerticalBlock"] {
	gap: 1rem;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Interface ✓
# --------------------------------------------------

st.title("Welcome to a Free Stock Backtester!")

st.write(
    "This is my first Python project. "
    "The goal is to allow users to input any stock or index, "
    "look up historical charts, and eventually run backtests "
    "on basic trading strategies."
)



# --------------------------------------------------
# Variables for ticker and date ✓
# --------------------------------------------------

ticker = st.text_input("Enter a stock ticker:")

start_date = st.date_input(
    "Start Date",
    value=datetime.now().date() - timedelta(days=365)
)

end_date = st.date_input(
    "End Date",
    value=datetime.now().date()
)

indicator = st.multiselect(
    "Indicators",
    ["Moving Average", "RSI", "Bollinger Bands"]
)

#---------------------------------------------------
# Side Bar Backtest Settings ✓
#---------------------------------------------------

st.sidebar.header("Backtest Settings")

initial_cash = st.sidebar.number_input(
	"Initial Investment ($)",
	min_value=1000,
	value=10000,
	step=1000
)

fee_percent = st.sidebar.number_input(
	"Transaction Fee (%)",
	min_value=0.0,
	value=0.1,
	step=0.05,
	help="Estimate fee charged on each buy or sell."
)

slippage_percent = st.sidebar.number_input(
	"Slippage (%)",
	min_value=0.0,
	value=0.05,
	step=0.05,
	help="Estimated adverse price movement on each trade."
)

strategy = st.sidebar.selectbox(
	"Strategy",
	[
	"Moving Average Crossover",
	"RSI", 
	"Bollinger Bands",
	]
)

years = st.sidebar.number_input(
	"Years of Historical Data",
	min_value = 1,
	max_value = 20,
	value = 5,
	step = 1
	)

# ----------------------------
# STRATEGY PARAMETERS ✓
# -----------------------------

if strategy == "Moving Average Crossover":
	short_window = st.sidebar.number_input(
		"Short MA",
		min_value=2,
		max_value=200,
		value=20
	)
	
	long_window = st.sidebar.number_input(
		"Long MA",
		min_value = 2,
		max_value=300,
		value=50
	)
elif strategy == "RSI":
	
	rsi_period = st.sidebar.number_input(
		"RSI Period",
		min_value=2,
		max_value=50,
		value=14
	)
	
	rsi_buy = st.sidebar.number_input(
		"Buy when RSI is below",
		min_value=1,
		max_value=50,
		value=30
	)

	rsi_sell = st.sidebar.number_input(
		"Sell when RSI is above",
		min_value = 50,
		max_value = 100,
		value = 70
	)

elif strategy == "Bollinger Bands":
	
	bb_period = st.sidebar.number_input(
		"BB Period",
		min_value = 2,
		max_value = 100,
		value = 20
	)
	
	bb_std = st.sidebar.number_input(
		"Standard Deviations",
		min_value = 0.5,
		max_value = 4.0,
		value = 2.0
	)
run_backtest = st.sidebar.button ("RUN BACKTEST!")

# --------------------------------------------------
# Initialize session state ✓
# --------------------------------------------------

if "data" not in st.session_state:
    st.session_state.data = None

if "searched_ticker" not in st.session_state:
    st.session_state.searched_ticker = ""

data = st.session_state.data


# --------------------------------------------------
# Search button ✓
# --------------------------------------------------

if st.button("Search"):

	if not ticker.strip():
		st.error("Please enter a stock ticker.")

	elif start_date >= end_date:
        	st.error("End Date must be after Start Date.")
	else:
		try:
			data = yf.download(
				ticker.strip().upper(),
				start=start_date,
				end=end_date + timedelta(days=1),
				auto_adjust=False,
				multi_level_index=False,
				progress=False
		)

			if data.empty:
				st.error("No stock data found. Check your ticker.")
			else:
				st.session_state.data = data
				st.session_state.searched_ticker = ticker.strip().upper()

		except Exception as e:
			st.error(f"Could not download stock data: {e}")


# --------------------------------------------------
# Indicator calculations ✓
# --------------------------------------------------

if st.session_state.data is not None:
	data = st.session_state.data.copy()
	searched_ticker = st.session_state.searched_ticker

	if "Moving Average" in indicator:
		data["MA20"] = data["Close"].rolling(window=20).mean()

	if "Bollinger Bands" in indicator:
		data["MA20"] = data["Close"].rolling(window=20).mean()
		data["STD20"] = data["Close"].rolling(window=20).std()
		data["BB Upper"] = data["MA20"] + 2 * data["STD20"]
		data["BB Lower"] = data["MA20"] - 2 * data["STD20"]

	if "RSI" in indicator:
		delta = data["Close"].diff()
		gain = delta.clip(lower=0)
		loss = -delta.clip(upper=0)
		average_gain = gain.rolling(window=14).mean()
		average_loss = loss.rolling(window=14).mean()

		rs = average_gain / average_loss
		data["RSI"] = 100 - (100 / (1 + rs))

	st.subheader("Historical Data")
	
	st.dataframe(data)
	# --------------------------------------------------
	# Candlestick chart ✓
	# --------------------------------------------------

	fig = make_subplots(
		rows=2,
		cols=1,
		shared_xaxes=True,
		row_heights=[0.7, 0.3],
		vertical_spacing=0.05
		)

	fig.add_trace(
		go.Candlestick(
		x=data.index,
		open=data["Open"],
		high=data["High"],
		low=data["Low"],
		close=data["Close"],
		name="Price"
		),
		row=1,
		col=1
	)
	
	fig.update_layout(
		height=500,
		autosize=True,
		margin=dict(l=40, r=40, t=80, b=40),
		xaxis_rangeslider_visible=False
	)
	
	


	# --------------------------------------------------
	# Moving Average ✓
	# --------------------------------------------------

	if "Moving Average" in indicator:
		fig.add_trace(
			go.Scatter(
				x=data.index,
				y=data["MA20"],
				mode="lines",
				name="MA20"
		),
		row=1,
		col=1
	)


    # --------------------------------------------------
    # Bollinger Bands ✓
    # --------------------------------------------------

	if "Bollinger Bands" in indicator:
		fig.add_trace(
			go.Scatter(
				x=data.index,
				y=data["BB Upper"],
				mode="lines",
				name="Upper Band"
		),
		row=1,
		col=1
	)

		fig.add_trace(
			go.Scatter(
				x=data.index,
			y=data["BB Lower"],
			mode="lines",
			name="Lower Band"
		),
		row=1,
		col=1
	)


    # --------------------------------------------------
    # RSI ✓
    # --------------------------------------------------

	if "RSI" in indicator:
		fig.add_trace(
			go.Scatter(
				x=data.index,
				y=data["RSI"],
				mode="lines",
				name="RSI"
		),
		row=2,
		col=1
	)

        # RSI reference lines
		fig.add_hline(
			y=70,
			line_dash="dash",
			line_color="red",
			row=2,
			col=1
		)

		fig.add_hline(
			y=30,
			line_dash="dash",
			line_color="green",
			row=2,
			col=1
		)

		fig.update_yaxes(
			range=[0, 100],
			title_text="RSI",
			row=2,
			col=1
		)


    # --------------------------------------------------
    # Chart styling ✓
    # --------------------------------------------------

	fig.update_layout(
		title=f"{searched_ticker} Stock Price",
		xaxis_title="Date",
		yaxis_title="Price (USD)",
		xaxis_rangeslider_visible=False,
		dragmode="pan",
		hovermode="x unified",
		height=1000
		)

	fig.update_xaxes(
		rangeslider_visible=False,
		showgrid=True
		)

	fig.update_yaxes(
		fixedrange=False)


    # --------------------------------------------------
    # Display chart ✓
    # --------------------------------------------------

	chart_col, data_col = st.columns([70,.5])

	with chart_col:
		st.plotly_chart(
			fig,
			use_container_width=True,
			config={
				"scrollZoom": True,
				"displaylogo": False
			}
		)


# ---------------------------------------------------
# Run Backtest
# ---------------------------------------------------



if run_backtest:
# Make sure the user searched for a stock first

	end_date = pd.Timestamp.today()
	start_date = end_date - pd.DateOffset(years=years)
	
	data = yf.download(
		ticker,
		start=start_date,
		end=end_date,
		auto_adjust=False,
		multi_level_index=False
	)

	if data.empty:
		st.error("Could not find data for that ticker.")
		st.stop()
	
	st.write("Downloading historical data...")

        # ---------------------------------------------------
        # MOVING AVERAGE CROSSOVER
        # ---------------------------------------------------

	if strategy == "Moving Average Crossover":

		data["Short_MA"] = (
			data["Close"].rolling(short_window).mean()
		)

		data["Long_MA"] = (
                data["Close"].rolling(long_window).mean()
		)

#Create signal
		data["Signal"] = 0

		data.loc[data["Short_MA"] > data["Long_MA"],"Signal"] = 1
		data.loc[data["Short_MA"] < data["Long_MA"],"Signal"] = 0

		data["Signal"] = (
			data["Short_MA"] > data["Long_MA"]
		).astype(int)

        # ---------------------------------------------------
        # RSI STRATEGY
        # ---------------------------------------------------

	elif strategy == "RSI":

		delta = data["Close"].diff()

		gain = delta.clip(lower=0)
		loss = -delta.clip(upper=0)
		average_gain = (
        	        gain
			.rolling(rsi_period)
        	        .mean()
		)

		average_loss = (
			loss
			.rolling(rsi_period)
			.mean()
		)

		rs = average_gain / average_loss

		data["RSI"] = (
			100 - (100 / (1 + rs))
			)

#Start with no position
		data["Signal"] = np.nan

#Buy when RSI is below threshold, Sell when its below

		data.loc[data["RSI"] < rsi_buy, "Signal"] = 1
		data.loc[data["RSI"] > rsi_sell, "Signal"] = 0
		
		data["Signal"] = data["Signal"].ffill().fillna(0)

        # ---------------------------------------------------
        # BOLLINGER BANDS
        # ---------------------------------------------------

	elif strategy == "Bollinger Bands":

		data["BB_MA"] = data["Close"].rolling(bb_period).mean()
		data["BB_STD"] = data["Close"].rolling(bb_period).std()
            

		data["BB_Upper"] = (
			data["BB_MA"] + bb_std * data["BB_STD"]
		)
            

		data["BB_Lower"] = (
			data["BB_MA"] - bb_std * data["BB_STD"]
            )

		data["Signal"] = 0

# Buy when price falls below lower band, Sell when its above

		data.loc[data["Close"] < data["BB_Lower"],"Signal"] = 1
		data.loc[data["Close"] > data["BB_Upper"],"Signal"] = 0

		data["Signal"] = data["Signal"].ffill().fillna(0)

	# ---------------------------------------------------
        # BACKTEST
        # ---------------------------------------------------
	
	data["Daily_Return"] = data["Close"].pct_change()
	
	data["Position"] = data["Signal"].shift(1).fillna(0)

#Strategy return BEFORE trading costs

	data["Gross_Return"] = (
		data["Position"] * data["Daily_Return"]
	)

# Identify changes in position: 0-->1 (buy); 1-->0 (sell)

	data["Turnover"] = (
		data["Position"].diff().abs().fillna(0)
	)

#Convert percentages into decimal rates

	fee_rate = fee_percent / 100
	slippage_rate = slippage_percent / 100
	
# estimate costs as a fraction of portfolio value

	data["Trading_Costs"] = (
		data["Turnover"] * (fee_rate + slippage_rate)
	)

# Strategy return AFTER trading costs

	data["Strategy_Return"] = (
		data["Gross_Return"].fillna(0) - data["Trading_Costs"]
	)

# Portfolio Values

	data["Portfolio_Before_Costs"] = (
		initial_cash
		* ( 1 + data["Gross_Return"].fillna(0)).cumprod()
	)
	
	data["Portfolio"] = (
		initial_cash
		* (1+ data["Strategy_Return"]).cumprod()
	)
	
# Buy and Hold before trading costs

	data["Buy_Hold"] = (
		initial_cash 
		* (1+data["Daily_Return"].fillna(0)).cumprod()
	)

	
	# ---------------------------------------------------
        # PERFORMANCE
        # ---------------------------------------------------
	
	final_portfolio = (
		data["Portfolio"].iloc[-1]
	)
	
	final_buy_hold = (
		data["Buy_Hold"].iloc[-1]
	)
	
	strategy_return = (
		(final_portfolio / initial_cash) - 1)*100

	buy_hold_return = (
		(final_buy_hold / initial_cash) - 1)*100
	
	trading_days = len(data)
	
	if trading_days>0 and final_portfolio > 0:
		annualized_return = (
			(final_portfolio / initial_cash)
			** (252 / trading_days) - 1
		)*100
	else:
		annualized_return = np.nan
	
	daily_returns = (
		data["Strategy_Return"].replace([np.inf, -np.inf], np.nan)
		.dropna()
	)

	daily_volatility = daily_returns.std()

	if len(daily_returns) > 1 and daily_volatility > 0:
		sharpe_ratio = (
			daily_returns.mean() / daily_volatility
		)* np.sqrt(252)
	else: 
		sharpe_ratio = np.nan

	running_peak = data["Portfolio"].cummax()
	drawdown = (
		data["Portfolio"] / running_peak -1)*100
	max_drawdown = drawdown.min()
	# ---------------------------------------------------
        # RESULTS
        # ---------------------------------------------------

	st.subheader("Backtest Results")
	
	metric1, metric2, metric3 = st.columns(3)
	
	metric1.metric(
		"Annualized Return",
		f"{annualized_return:.2f}%"
		if pd.notna(annualized_return) else "N/A"
	)
	
	metric2.metric(
		"Sharpe Ratio",
		f"{sharpe_ratio:.2f}%"
		if pd.notna(sharpe_ratio) else "N/A"
	)

	metric3.metric(
		"Maximum Drawdown",
		f"{max_drawdown:.2f}%"
	)
	
	st.markdown("""
		**Annualized return:**
		The strategy's compounded yearly return,estimated using 252 trading days per year. 
		This helps compare backtests of different lengths.
		
		**Sharpe ratio:**
		Compares average daily return with daily volatility, then annualizes the result. A higher value generally means more return per unit of volatility. 
		This version assumes a zero risk-free rate.

		**Maximum drawdown:**
		The largest percentage decline in portfolio value from a previous peak.
		For example, -15% means the portfolio experienced a peak-to-trough decline of 15%.
	
	""")

	col1, col2, col3 = st.columns(3)
	
	col1.metric(
		"Final Portfolio",
		f"${final_portfolio:,.2f}"
	)

	col2.metric(
		"Strategy Return",
		f"${strategy_return:.2f}%"
	)

	col3.metric(
		"Buy & Hold",
		f"{buy_hold_return:2f}%"
	)

	gross_final = data["Portfolio_Before_Costs"].iloc[-1]
	net_final = data["Portfolio"].iloc[-1]

	gross_return = (gross_final / initial_cash - 1) * 100
	net_return = (net_final / initial_cash -1) * 100
	
	st.subheader("Impact of Trading Costs")
	col1, col2, col3 = st.columns(3)
	
	col1.metric(
		"Return Before Costs",
		f"{gross_return:.2f}%"
	)
	
	col2.metric(
		"Return after Costs",
		f"{net_return:.2f}%"
	)

	col3.metric(
		"Estimated Cost Impact",
		f"{gross_return - net_return:.2f} percentage points"
	)
	# ---------------------------------------------------
        # EQUITY CURVE
        # ---------------------------------------------------

	st.subheader("Portfolio Performance")
	
	portfolio_fig = go.Figure()
	
	portfolio_fig.add_trace(
		go.Scatter(
			x=data.index,
			y=data["Portfolio"],
			name="Trading Strategy",
			mode="lines"
		)
	)

	portfolio_fig.add_trace(
		go.Scatter(
			x=data.index,
			y=data["Buy_Hold"],
			name="Buy & Hold",
			mode="lines"
		)
	)
	portfolio_fig.add_trace(
		go.Scatter(
			x=data.index,
			y=data["Portfolio_Before_Costs"],
			name="Before Trading Costs",
			mode="lines"
		)
	)
	portfolio_fig.update_layout(
		title=f"{ticker.strip().upper()} Backtest",
		yaxis_title="Portfolio Value ($)",
		xaxis_title="Date",
		hovermode="x unified",
		height=500
	)

	st.plotly_chart(
		portfolio_fig,
		use_container_width=True
	)

	# ---------------------------------------------------
        # TRADE LOG
        # ---------------------------------------------------

#Tracking trades in position

	data["Trade"] = data["Position"].diff().fillna(0)
	
	trades = data.loc[
		data["Trade"]!= 0,
		["Close", "Position", "Trade"]
	].copy()

#Change to position 1 means BUY change to 0 means SELL

	trades["Action"] = trades["Position"].map({
		1.0: "BUY",
		0.0: "SELL"
	})
	
	st.subheader("Trade Log")

	st.dataframe(
		trades[["Action", "Close"] ].rename(
			columns={"Close": "Price"}
		)
	)
			





















