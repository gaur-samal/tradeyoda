"""Chart components for visualization."""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


def create_candlestick_chart(df: pd.DataFrame, title: str = "Price Chart"):
    """Create candlestick chart with volume."""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=(title, 'Volume')
    )
    
    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='Price'
        ),
        row=1, col=1
    )
    
    # Volume
    colors = ['red' if row['close'] < row['open'] else 'green' 
              for _, row in df.iterrows()]
    
    fig.add_trace(
        go.Bar(
            x=df['timestamp'],
            y=df['volume'],
            name='Volume',
            marker_color=colors
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        height=600,
        showlegend=False
    )
    
    return fig


def create_volume_profile_chart(volume_data: dict, poc: float, vah: float, val: float):
    """Create volume profile horizontal bar chart."""
    prices = sorted(volume_data.keys())
    volumes = [volume_data[p] for p in prices]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=volumes,
        y=prices,
        orientation='h',
        marker_color='rgba(102, 126, 234, 0.6)',
        name='Volume Profile'
    ))
    
    # Add POC line
    fig.add_hline(
        y=poc, 
        line_dash="dash", 
        line_color="red",
        annotation_text="POC",
        annotation_position="right"
    )
    
    # Add VAH/VAL lines
    fig.add_hline(
        y=vah,
        line_dash="dot",
        line_color="green",
        annotation_text="VAH",
        annotation_position="right"
    )
    fig.add_hline(
        y=val,
        line_dash="dot",
        line_color="green",
        annotation_text="VAL",
        annotation_position="right"
    )
    
    fig.update_layout(
        title="Volume Profile",
        xaxis_title="Volume",
        yaxis_title="Price",
        height=500
    )
    
    return fig


def create_pnl_chart(trades: list):
    """Create P&L curve chart."""
    if not trades:
        return None
    
    cumulative_pnl = []
    pnl_sum = 0
    
    for trade in trades:
        pnl_sum += trade.get('pnl', 0)
        cumulative_pnl.append({
            'timestamp': trade.get('timestamp'),
            'pnl': pnl_sum
        })
    
    df = pd.DataFrame(cumulative_pnl)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['pnl'],
        mode='lines+markers',
        name='Cumulative P&L',
        line=dict(color='blue', width=2),
        fill='tozeroy',
        fillcolor='rgba(102, 126, 234, 0.2)'
    ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    
    fig.update_layout(
        title="Cumulative P&L",
        xaxis_title="Time",
        yaxis_title="P&L (₹)",
        height=400
    )
    
    return fig

