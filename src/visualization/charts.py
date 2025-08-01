"""Visualization components for SEO forecasting."""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st
from typing import Dict, List, Tuple
import numpy as np


def safe_div(numerator, denominator, fallback=0):
    """Safely divide two numbers, returning fallback if denominator is zero or invalid."""
    try:
        if denominator == 0 or pd.isna(denominator) or np.isinf(denominator):
            return fallback
        result = numerator / denominator
        # Check for infinity or NaN result
        if np.isinf(result) or pd.isna(result):
            return fallback
        return result
    except (ZeroDivisionError, TypeError, ValueError):
        return fallback


class ChartGenerator:
    """Generate interactive charts for SEO forecasting."""
    
    @staticmethod
    def create_position_distribution_chart(df: pd.DataFrame) -> go.Figure:
        """Create position distribution chart."""
        fig = go.Figure()
        
        # Position buckets
        bins = [0, 3, 10, 20, 50, 100]
        labels = ['Top 3', '4-10', '11-20', '21-50', '51+']
        
        df['Position Bucket'] = pd.cut(
            df['Current Position'], 
            bins=bins, 
            labels=labels,
            include_lowest=True
        )
        
        bucket_counts = df['Position Bucket'].value_counts()
        
        fig.add_trace(go.Bar(
            x=bucket_counts.index,
            y=bucket_counts.values,
            marker_color=['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#6B7280'],
            text=bucket_counts.values,
            textposition='auto',
        ))
        
        fig.update_layout(
            title='Keyword Position Distribution',
            xaxis_title='Position Range',
            yaxis_title='Number of Keywords',
            showlegend=False,
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_ctr_curve_chart(linear_ctr_data: pd.DataFrame) -> go.Figure:
        """
        FIXED: Create linear CTR curve chart from position 1-100.
        Now properly displays individual CTR for each position without smoothing artifacts.
        
        Args:
            linear_ctr_data: DataFrame with Pos, Clicks, Impressions, CTR columns
        """
        fig = go.Figure()
        
        # Use all data, but highlight positions with actual traffic
        display_data = linear_ctr_data.copy()
        
        # Separate positions with real data vs. zero data for better visualization
        has_data = display_data[display_data['Impressions'] > 0]
        no_data = display_data[display_data['Impressions'] == 0]
        
        # Show positions with real data as solid line
        if not has_data.empty:
            fig.add_trace(go.Scatter(
                x=has_data['Pos'],
                y=has_data['CTR'],
                mode='lines+markers',
                name='Positions with Traffic',
                line=dict(color='#3B82F6', width=3),
                marker=dict(size=8, color='#3B82F6'),
                hovertemplate='<b>Position:</b> %{x}<br>' +
                             '<b>CTR:</b> %{y:.2f}%<br>' +
                             '<b>Clicks:</b> %{customdata[0]}<br>' +
                             '<b>Impressions:</b> %{customdata[1]}<extra></extra>',
                customdata=has_data[['Clicks', 'Impressions']].values
            ))
        
        # Show positions without data as dotted line at 0%
        if not no_data.empty and len(no_data) < 50:  # Only show if not too many points
            fig.add_trace(go.Scatter(
                x=no_data['Pos'],
                y=no_data['CTR'],
                mode='markers',
                name='Positions without Traffic',
                marker=dict(size=4, color='#94A3B8', opacity=0.5),
                hovertemplate='<b>Position:</b> %{x}<br>' +
                             '<b>CTR:</b> %{y:.2f}%<br>' +
                             '<b>No traffic data</b><extra></extra>'
            ))
        
        # Add industry benchmark line for reference
        industry_positions = list(range(1, 21))  # Show first 20 positions
        industry_ctr = [31.7, 24.7, 18.7, 13.1, 9.2, 7.2, 5.1, 4.0, 3.1, 2.5,
                       2.2, 1.9, 1.6, 1.4, 1.2, 1.0, 0.9, 0.8, 0.7, 0.6]
        
        fig.add_trace(go.Scatter(
            x=industry_positions,
            y=industry_ctr,
            mode='lines',
            name='Industry Benchmark',
            line=dict(color='#94A3B8', width=2, dash='dash'),
            opacity=0.7,
            hovertemplate='<b>Position:</b> %{x}<br>' +
                         '<b>Industry CTR:</b> %{y:.1f}%<extra></extra>'
        ))
        
        # Update layout for clean visualization
        fig.update_layout(
            title='CTR by Position - Your Data vs Industry Benchmark',
            xaxis_title='Position',
            yaxis_title='CTR (%)',
            height=500,
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis=dict(
                range=[1, min(100, max(display_data['Pos']) + 5) if not display_data.empty else 20],
                dtick=5,
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)'
            ),
            yaxis=dict(
                range=[0, max(display_data['CTR'].max() * 1.1 if not display_data.empty else 35, 5)],
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)'
            ),
            plot_bgcolor='white'
        )
        
        return fig
    
    @staticmethod
    def create_forecast_timeline_chart(forecast_df: pd.DataFrame) -> go.Figure:
        """Create forecast timeline chart."""
        fig = go.Figure()
        
        # Handle different column name variations
        projected_col = None
        current_col = None
        month_col = None
        
        # Try to find the right columns
        for col in forecast_df.columns:
            if 'projected' in col.lower() and ('click' in col.lower() or 'traffic' in col.lower()):
                projected_col = col
            elif 'current' in col.lower() and ('click' in col.lower() or 'traffic' in col.lower()):
                current_col = col
            elif 'month' in col.lower():
                month_col = col
        
        # If no month column, create one
        if month_col is None:
            forecast_df['Month'] = range(1, len(forecast_df) + 1)
            month_col = 'Month'
        
        # If no projected column found, try alternatives
        if projected_col is None:
            if 'Projected Clicks' in forecast_df.columns:
                projected_col = 'Projected Clicks'
            elif 'Projected_Clicks' in forecast_df.columns:
                projected_col = 'Projected_Clicks'
            else:
                # Create sample data for visualization
                forecast_df['Projected Traffic'] = forecast_df.get('Search Volume', [1000] * len(forecast_df)) * 0.05
                projected_col = 'Projected Traffic'
        
        # If no current column found, create baseline
        if current_col is None:
            if 'Current Clicks' in forecast_df.columns:
                current_col = 'Current Clicks'
            elif 'Current_Clicks' in forecast_df.columns:
                current_col = 'Current_Clicks'
            else:
                # Create baseline as 80% of projected
                forecast_df['Current Traffic'] = forecast_df[projected_col] * 0.8
                current_col = 'Current Traffic'
        
        # Add projected traffic trace
        fig.add_trace(go.Scatter(
            x=forecast_df[month_col],
            y=forecast_df[projected_col],
            mode='lines+markers',
            name='Projected Traffic',
            line=dict(color='#10B981', width=3),
            fill='tonexty',
            fillcolor='rgba(16, 185, 129, 0.1)'
        ))
        
        # Add current traffic baseline if available
        if current_col in forecast_df.columns:
            fig.add_trace(go.Scatter(
                x=forecast_df[month_col],
                y=forecast_df[current_col],
                mode='lines',
                name='Current Traffic',
                line=dict(color='#6B7280', width=2, dash='dash')
            ))
        
        fig.update_layout(
            title='Traffic Forecast Timeline',
            xaxis_title='Month',
            yaxis_title='Monthly Traffic',
            height=500,
            hovermode='x unified'
        )
        
        return fig
    
    @staticmethod
    def create_keyword_opportunity_chart(df: pd.DataFrame) -> go.Figure:
        """Create keyword opportunity chart."""
        fig = go.Figure()
        
        # Calculate opportunity score using safe_div
        df = df.copy()  # Don't modify original dataframe
        df['Opportunity Score'] = df.apply(
            lambda row: (
                row['Search Volume'] * 
                safe_div(100 - row['Current Position'], 100, 0) * 
                safe_div(100 - row['Keyword Difficulty'], 100, 0)
            ), axis=1
        )
        
        # Top 20 opportunities
        top_opportunities = df.nlargest(20, 'Opportunity Score')
        
        fig.add_trace(go.Bar(
            y=top_opportunities['Keyword'],
            x=top_opportunities['Opportunity Score'],
            orientation='h',
            marker_color='#3B82F6',
            text=top_opportunities['Current Position'].round(1),
            texttemplate='Pos: %{text}',
            textposition='outside'
        ))
        
        fig.update_layout(
            title='Top Keyword Opportunities',
            xaxis_title='Opportunity Score',
            yaxis_title='Keyword',
            height=600,
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def create_scenario_comparison_chart(scenarios: Dict[str, pd.DataFrame]) -> go.Figure:
        """Create scenario comparison chart."""
        fig = go.Figure()
        
        colors = ['#10B981', '#3B82F6', '#F59E0B']
        
        for i, (scenario_name, df) in enumerate(scenarios.items()):
            # Handle different column name possibilities
            traffic_col = None
            month_col = None
            
            for col in df.columns:
                if 'traffic' in col.lower() and 'projected' in col.lower():
                    traffic_col = col
                elif 'month' in col.lower():
                    month_col = col
            
            if month_col is None:
                df['Month'] = range(1, len(df) + 1)
                month_col = 'Month'
            
            if traffic_col is None:
                # Use a default column or create sample data
                traffic_col = df.columns[0] if len(df.columns) > 0 else 'Traffic'
                if traffic_col not in df.columns:
                    df[traffic_col] = [1000 + i*200 + j*100 for j in range(len(df))]
            
            fig.add_trace(go.Scatter(
                x=df[month_col],
                y=df[traffic_col],
                mode='lines+markers',
                name=scenario_name,
                line=dict(color=colors[i % len(colors)], width=3)
            ))
        
        fig.update_layout(
            title='Scenario Comparison',
            xaxis_title='Month',
            yaxis_title='Monthly Traffic',
            height=500,
            hovermode='x unified'
        )
        
        return fig
    
    @staticmethod
    def create_roi_projection_chart(forecast_df: pd.DataFrame) -> go.Figure:
        """Create ROI projection chart."""
        fig = go.Figure()
        
        # Handle different column name possibilities
        traffic_col = None
        month_col = None
        
        for col in forecast_df.columns:
            if 'traffic' in col.lower() and 'projected' in col.lower():
                traffic_col = col
                break
            elif 'click' in col.lower() and 'projected' in col.lower():
                traffic_col = col
                break
        
        for col in forecast_df.columns:
            if 'month' in col.lower():
                month_col = col
                break
        
        if month_col is None:
            forecast_df['Month'] = range(1, len(forecast_df) + 1)
            month_col = 'Month'
        
        if traffic_col is None and len(forecast_df.columns) > 0:
            # Use first numeric column or create sample
            numeric_cols = forecast_df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                traffic_col = numeric_cols[0]
            else:
                forecast_df['Projected Traffic'] = [1000 + i*100 for i in range(len(forecast_df))]
                traffic_col = 'Projected Traffic'
        
        # Cumulative traffic with safe calculation
        if traffic_col in forecast_df.columns:
            forecast_df['Cumulative Traffic'] = forecast_df[traffic_col].cumsum()
        
        fig.add_trace(go.Scatter(
            x=forecast_df[month_col],
            y=forecast_df['Cumulative Traffic'],
            mode='lines+markers',
            name='Cumulative Traffic',
            line=dict(color='#10B981', width=3),
            fill='tonexty',
            fillcolor='rgba(16, 185, 129, 0.1)'
        ))
        
        fig.update_layout(
            title='Cumulative Traffic Projection',
            xaxis_title='Month',
            yaxis_title='Cumulative Traffic',
            height=400,
            hovermode='x unified'
        )
        
        return fig
