import plotly.express as px
import pandas as pd
import numpy as np

# function to plot the graph
def interactive_plot(df):
    fig = px.line()
    for i in df.columns[1:]:
        if pd.api.types.is_numeric_dtype(df[i]):  # Only plot numeric columns
            fig.add_scatter(x=df[df.columns[0]], y=df[i], mode='lines', name=i)
    
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Price',
        margin=dict(l=20, r=20, t=60, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.15,
            xanchor="center",
            x=0.5,
            title_text=''
        )
    )
    return fig

# normalize the price
def normalize(df):
    df_norm = df.copy()
    for i in df_norm.columns:
        if pd.api.types.is_numeric_dtype(df_norm[i]):
            first_valid = df_norm[i].dropna().iloc[0] if not df_norm[i].dropna().empty else 1
            if first_valid != 0:
                df_norm[i] = df_norm[i] / first_valid
    return df_norm

# calculate daily returns
def daily_return(df):
    df_ret = df.copy()
    
    # Only apply percentage change to numeric columns (skip Date columns)
    for col in df_ret.columns:
        if pd.api.types.is_numeric_dtype(df_ret[col]) and col not in ['Date', 'DATE']:
            df_ret[col] = df_ret[col].pct_change() * 100
    
    # Drop rows with NaN values and reset index
    df_ret = df_ret.dropna().reset_index(drop=True)
    
    return df_ret

# calculate beta
def calculate_beta(stock_daily_return, stock):
    try:
        # Make sure we're only using numeric data and exclude Date columns
        market_data = stock_daily_return['sp500']
        stock_data = stock_daily_return[stock]
        
        # Remove any non-numeric values and NaN
        market_clean = pd.to_numeric(market_data, errors='coerce').dropna()
        stock_clean = pd.to_numeric(stock_data, errors='coerce').dropna()
        
        # Find common indices
        common_idx = market_clean.index.intersection(stock_clean.index)
        
        if len(common_idx) < 2:
            return 1.0, 0.0  # Default values if insufficient data
        
        x = market_clean.loc[common_idx].values
        y = stock_clean.loc[common_idx].values
        
        b, a = np.polyfit(x, y, 1)
        return b, a
        
    except Exception as e:
        print(f"Error calculating beta for {stock}: {e}")
        return 1.0, 0.0  # Return default values on error