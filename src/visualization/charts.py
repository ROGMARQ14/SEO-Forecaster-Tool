"""Visualization components for SEO forecasting."""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st
from typing import Dict, List, Tuple
import numpy as np


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
    def create_ctr_curve_chart(df: pd.DataFrame) -> go.Figure:
        """Create CTR curve chart."""
        fig = go.Figure()
        
        # Group by position and calculate average CTR
        position_ctr = df.groupby('Current Position')['CTR'].agg(['mean', 'count']).reset_index()
        position_ctr = position_ctr[position_ctr['Current Position'] <= 50]
        
        fig.add_trace(go.Scatter(
            x=position_ctr['Current Position'],
            y=position_ctr['mean'] * 100,
            mode='lines+markers',
            name='CTR',
            line=dict(color='#3B82F6', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title='CTR by Position',
            xaxis_title='Position',
            yaxis_title='CTR (%)',
            height=400,
            hovermode='x unified'
        )
        
        return fig
    
    @staticmethod
    def create_forecast_timeline_chart(forecast_df: pd.DataFrame) -> go.Figure:
        """Create forecast timeline chart."""
        fig = go.Figure()
        
        # Ensure we have the right columns
        if 'Month' not in forecast_df.columns:
            # Create month column if missing
            forecast_df['Month'] = range(1, len(forecast_df) + 1)
        
        # Traffic forecast
        fig.add_trace(go.Scatter(
            x=forecast_df['Month'],
            y=forecast_df['Projected Traffic'],
            mode='lines+markers',
            name='Projected Traffic',
            line=dict(color='#10B981', width=3),
            fill='tonexty',
            fillcolor='rgba(16, 185, 129, 0.1)'
        ))
        
        # Current traffic baseline
        if 'Current Traffic' in forecast_df.columns:
            fig.add_trace(go.Scatter(
                x=forecast_df['Month'],
                y=forecast_df['Current Traffic'],
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
        
        # Calculate opportunity score
        df['Opportunity Score'] = (
            (df['Search Volume'] * (1 - df['Current Position'] / 100)) * 
            (1 - df['Keyword Difficulty'] / 100)
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
            if 'Month' not in df.columns:
                df['Month'] = range(1, len(df) + 1)
                
            fig.add_trace(go.Scatter(
                x=df['Month'],
                y=df['Projected Traffic'],
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
        
        if 'Month' not in forecast_df.columns:
            forecast_df['Month'] = range(1, len(forecast_df) + 1)
        
        # Cumulative traffic
        forecast_df['Cumulative Traffic'] = forecast_df['Projected Traffic'].cumsum()
        
        fig.add_trace(go.Scatter(
            x=forecast_df['Month'],
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
