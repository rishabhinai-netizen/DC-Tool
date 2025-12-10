# file: app/ui.py
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Try import AgGrid, else fallback
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
    HAS_AGGRID = True
except ImportError:
    HAS_AGGRID = False

def render_interactive_table(df, key="table"):
    """
    Renders AgGrid with selection enabled.
    """
    if df.empty:
        st.write("No Data")
        return None

    if HAS_AGGRID:
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_selection('single', use_checkbox=True)
        gb.configure_column("Symbol", pinned=True)
        gridOptions = gb.build()

        grid_response = AgGrid(
            df,
            gridOptions=gridOptions,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            fit_columns_on_grid_load=True,
            theme='streamlit',
            key=key
        )
        
        selected = grid_response['selected_rows']
        if selected:
            # AgGrid v0.3.4+ returns list of dicts. 
            # Depending on version, it might be a DataFrame or list.
            # We assume list of dicts here.
            return selected[0] if len(selected) > 0 else None
        return None
    else:
        st.dataframe(df)
        return None

def plot_stock_chart(df, ticker):
    """
    Creates Plotly Candlestick with Donchian and RSI.
    """
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.1, subplot_titles=(f"{ticker} Price", "RSI"),
                        row_width=[0.2, 0.7])

    # Candlestick
    fig.add_trace(go.Candlestick(x=df.index,
                    open=df['Open'], high=df['High'],
                    low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)

    # Donchian
    fig.add_trace(go.Scatter(x=df.index, y=df['High_20'], line=dict(color='green', width=1, dash='dash'), name="Upper"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Low_20'], line=dict(color='red', width=1, dash='dash'), name="Lower"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Middle'], line=dict(color='blue', width=1), name="Middle"), row=1, col=1)
    
    # SMA
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], line=dict(color='orange', width=2), name="SMA 200"), row=1, col=1)

    # RSI
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple', width=2), name="RSI"), row=2, col=1)
    fig.add_hline(y=70, line_dash="dot", row=2, col=1, line_color="red")
    fig.add_hline(y=30, line_dash="dot", row=2, col=1, line_color="green")

    fig.update_layout(xaxis_rangeslider_visible=False, height=600, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)
