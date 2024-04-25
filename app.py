import streamlit as st
import pandas as pd
import plotly.graph_objects as go


# Load the data from s3 bucket
#fixing cache so the lastest data is loaded
df = pd.read_csv('monthly_vix.csv')

# Convert 'time' column to datetime format
df['time'] = pd.to_datetime(df['time'])

print(df['time'].unique())


# Sidebar layout
st.sidebar.title("Filters")
selected_put_date = st.sidebar.selectbox("Put - Lookup Date", df['time'].dt.date.unique())
selected_put_strike = st.sidebar.selectbox("Put Strike Price", df['strikePrice'].unique())
selected_call_date = st.sidebar.selectbox("Call - Lookup Date", df['time'].dt.date.unique())  
selected_call_strike = st.sidebar.selectbox("Call Strike Price", df['strikePrice'].unique())

# Filtered data for put and call
filtered_put_df = df[(df['time'].dt.date == selected_put_date) & (df['strikePrice'] == selected_put_strike) & (df['optionType'] == 'Put')].sort_values('expirationDate')
filtered_call_df = df[(df['time'].dt.date == selected_call_date) & (df['strikePrice'] == selected_call_strike) & (df['optionType'] == 'Call')].sort_values('expirationDate')


# Put graph
st.subheader(f'Put Prices and Volatility for {selected_put_date}, Strike: {selected_put_strike}, Type: Put')
put_fig = go.Figure()

# Add put bid price to the plot
put_fig.add_trace(go.Scatter(x=filtered_put_df['expirationDate'], y=filtered_put_df['bidPrice'], mode='lines', name='Put Bid Price'))

# Add put volatility to the plot with a secondary y-axis
put_fig.add_trace(go.Scatter(x=filtered_put_df['expirationDate'], y=filtered_put_df['volatility'], mode='lines', name='Volatility', yaxis='y2'))

# Update layout to add a secondary y-axis
put_fig.update_layout(
    yaxis=dict(title='Bid Price'),
    yaxis2=dict(title='Volatility', overlaying='y', side='right')
)

st.plotly_chart(put_fig)

# Call graph
st.subheader(f'Call Prices and Volatility for {selected_call_date}, Strike: {selected_call_strike}, Type: Call')
call_fig = go.Figure()

# Add call bid price to the plot
call_fig.add_trace(go.Scatter(x=filtered_call_df['expirationDate'], y=filtered_call_df['bidPrice'], mode='lines', name='Call Bid Price'))

# Add call volatility to the plot with a secondary y-axis
call_fig.add_trace(go.Scatter(x=filtered_call_df['expirationDate'], y=filtered_call_df['volatility'], mode='lines', name='Volatility', yaxis='y2'))

# Update layout to add a secondary y-axis
call_fig.update_layout(
    yaxis=dict(title='Bid Price'),
    yaxis2=dict(title='Volatility', overlaying='y', side='right')
)

st.plotly_chart(call_fig)



