import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_datareader.data as web
import datetime

import capm_function

st.set_page_config(page_title="CAPM Return",
    page_icon="📈",
    layout="wide")

st.title("Capital Asset Pricing Model (CAPM) ")

# getting i/p from user
col1, col2 = st.columns([1,1])
with col1:
    stock_list = st.multiselect("Choose the stock",
                                 ("AAPL", "MSFT", "GOOGL", "AMZN", "TSLA","MGM"),
                                ["AAPL", "GOOGL"], key="stocks")
with col2:
    year = st.number_input("Enter the number of years to fetch data", 1, 10, key="years")

if stock_list:  # Only proceed if stocks are selected
    try:
        # fetching data from SP500
        end = datetime.date.today()
        start = datetime.date(datetime.date.today().year-year, datetime.date.today().month, datetime.date.today().day)
        
        with st.spinner("Fetching S&P 500 data..."):
            SP500 = web.DataReader(['sp500'], 'fred', start, end)
        
        stock_df = pd.DataFrame()
        
        # Fetch stock data with progress
        progress_text = st.empty()
        for i, stock in enumerate(stock_list):
            progress_text.text(f"Fetching data for {stock}... ({i+1}/{len(stock_list)})")
            try:
                data = yf.download(stock, start=start, end=end, progress=False)
                if not data.empty:
                    stock_df[f'{stock}'] = data['Close']
                else:
                    st.warning(f"No data found for {stock}")
            except Exception as e:
                st.error(f"Error fetching {stock}: {e}")
        
        progress_text.empty()
        
        if not stock_df.empty:
            stock_df.reset_index(inplace=True)
            SP500.reset_index(inplace=True)

            # Convert Date column to datetime.date
            stock_df['Date'] = pd.to_datetime(stock_df['Date']).dt.date
            SP500['DATE'] = pd.to_datetime(SP500['DATE']).dt.date   # FRED ka column name 'DATE' hota hai

            # Merge stock_df aur SP500 on Date
            stock_df = pd.merge(stock_df, SP500, left_on='Date', right_on='DATE', how='inner')
            
            # Remove duplicate DATE column
            if 'DATE' in stock_df.columns:
                stock_df.drop('DATE', axis=1, inplace=True)

            if not stock_df.empty:
                col1, col2 = st.columns([1,1])
                with col1:
                    st.markdown("### DataFrame head")
                    st.dataframe(stock_df.head(), use_container_width=True)

                with col2:
                    st.markdown("### DataFrame tail")
                    st.dataframe(stock_df.tail(), use_container_width=True)

                col1, col2 = st.columns([1,1])
                with col1:
                    st.markdown("### Price of the stocks over time")
                    st.plotly_chart(capm_function.interactive_plot(stock_df), use_container_width=True)

                with col2:
                    st.markdown("### Price of the stocks after normalization")
                    st.plotly_chart(capm_function.interactive_plot(capm_function.normalize(stock_df)), use_container_width=True)

                # Calculate daily returns
                stock_daily_returns = capm_function.daily_return(stock_df)
                
                # Debug: Show what columns we have in daily returns
                st.write("Daily returns columns:", stock_daily_returns.columns.tolist())

                beta = {}
                alpha = {}

                for i in stock_daily_returns.columns:
                    if i != 'Date' and i != 'sp500' and pd.api.types.is_numeric_dtype(stock_daily_returns[i]):
                        b, a = capm_function.calculate_beta(stock_daily_returns, i)
                        beta[i] = b
                        alpha[i] = a

                if beta:  # Only proceed if we have beta values
                    beta_df = pd.DataFrame(list(beta.items()), columns=['Stock', 'Beta'])
                    beta_df['Beta Value'] = [str(round(i,2)) for i in beta.values()]

                    with col1:
                        st.markdown("### Beta Values of the stocks")
                        st.dataframe(beta_df, use_container_width=True)

                    # Calculate expected returns
                    rf = 0  # Risk-free rate
                    rm = stock_daily_returns['sp500'].mean() * 252 / 100  # Convert to annual return

                    return_df = pd.DataFrame()
                    return_value = []

                    for stock, value in beta.items():
                        er = round(rf + value * (rm - rf), 4)  # More decimal places for accuracy
                        return_value.append(er)

                    return_df['Stock'] = list(beta.keys())
                    return_df['Return Value'] = return_value

                    with col2:
                        st.markdown("### Expected Return Values of the stocks")
                        st.dataframe(return_df, use_container_width=True)
                else:
                    st.error("Could not calculate beta values. Please check your data.")
            else:
                st.error("No data available after merging with S&P 500 data.")
        else:
            st.error("Could not fetch data for any of the selected stocks.")
            
    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.info("Please try selecting different stocks or a different time period.")
else:
    st.info("Please select at least one stock to begin analysis.")