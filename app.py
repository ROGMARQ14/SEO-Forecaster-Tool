"""SEO Performance Forecaster - Streamlit Application."""

import logging
import os
import sys

import streamlit as st

# Add the src directory to the path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

from src.data.data_loader import DataLoader
from src.analysis.seo_analyzer import SEOAnalyzer
from src.analysis.forecaster import SEOForecaster
from src.visualization.charts import ChartGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="SEO Performance Forecaster",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .forecast-highlight {
        background-color: #e8f4f8;
        padding: 1rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">SEO Performance Forecaster</div>',
            unsafe_allow_html=True)
st.markdown("Forecast your website's SEO performance for the next 90, 180, "
            "and 360 days")

# Sidebar for data upload
with st.sidebar:
    st.header("📊 Data Upload")

    # File uploaders
    gsc_file = st.file_uploader(
        "Upload Google Search Console Data",
        type=['csv', 'xlsx', 'xls'],
        help="Upload your GSC performance report with Query, Clicks, "
             "Impressions, CTR, and Average Position"
    )

    semrush_file = st.file_uploader(
        "Upload SEMrush Data",
        type=['csv', 'xlsx', 'xls'],
        help="Upload your SEMrush keyword report with Keyword, Search Volume, "
             "Keyword Difficulty, Current Position, and URL"
    )

    # Sample data toggle
    use_sample = st.checkbox("Use Sample Data", help="Load sample data for testing")

    # Forecasting parameters
    st.header("⚙️ Forecasting Settings")

    improvement_scenarios = {
        "Conservative": 5,
        "Moderate": 10,
        "Aggressive": 15,
        "Custom": None
    }

    scenario = st.selectbox(
        "Improvement Scenario",
        options=list(improvement_scenarios.keys()),
        help="Select how much you expect to improve keyword rankings"
    )

    if scenario == "Custom":
        avg_improvement = st.slider(
            "Average Position Improvement",
            min_value=1,
            max_value=30,
            value=10,
            help="Average number of positions to improve per keyword"
        )
    else:
        avg_improvement = improvement_scenarios[scenario]

    # Time periods
    forecast_periods = st.multiselect(
        "Forecast Periods (days)",
        options=[90, 180, 360],
        default=[90, 180, 360],
        help="Select time periods for forecasting"
    )

# Main content area
if gsc_file and semrush_file or use_sample:
    try:
        # Load data
        with st.spinner("Loading and processing data..."):
            if use_sample:
                gsc_df, semrush_df = DataLoader.get_sample_data()
                st.info("Using sample data for demonstration")
            else:
                gsc_df = DataLoader.load_gsc_data(gsc_file)
                semrush_df = DataLoader.load_semrush_data(semrush_file)

            if gsc_df is not None and semrush_df is not None:
                # Merge data
                merged_df = DataLoader.merge_data(gsc_df, semrush_df)

                if not merged_df.empty:
                    # Display data quality metrics
                    col1, col2, col3, col4 = st.columns(4)

                    quality_metrics = DataLoader.validate_data_quality(merged_df)

                    with col1:
                        st.metric("Total Keywords",
                                  f"{quality_metrics['total_keywords']:,}")
                    with col2:
                        st.metric("Avg Position",
                                  f"{quality_metrics['avg_position']:.1f}")
                    with col3:
                        st.metric("Total Clicks",
                                  f"{quality_metrics['total_clicks']:,}")
                    with col4:
                        st.metric("Quality Score",
                                  f"{quality_metrics['quality_score']:.0f}/100")

                    # Create tabs for different views
                    tab1, tab2, tab3, tab4 = st.tabs([
                        "📊 Overview", "🔍 Analysis", "📈 Forecast", "📋 Data"
                    ])

                    with tab1:
                        st.header("Data Overview")

                        # Display sample data
                        col1, col2 = st.columns(2)

                        with col1:
                            st.subheader("Top Keywords by Clicks")
                            top_keywords = merged_df.nlargest(10, 'Clicks')[
                                ['Keyword', 'Clicks', 'Current Position',
                                 'Search Volume']
                            ]
                            st.dataframe(top_keywords, use_container_width=True)

                        with col2:
                            st.subheader("Keyword Distribution")
                            chart_gen = ChartGenerator()
                            fig = chart_gen.create_position_distribution_chart(merged_df)
                            st.plotly_chart(fig, use_container_width=True)

                    with tab2:
                        st.header("SEO Analysis")

                        # CTR Analysis
                        analyzer = SEOAnalyzer()
                        ctr_df = analyzer.calculate_ctr_by_position(merged_df)

                        col1, col2 = st.columns(2)

                        with col1:
                            st.subheader("CTR by Position")
                            fig = chart_gen.create_ctr_curve_chart(merged_df)
                            st.plotly_chart(fig, use_container_width=True)

                        with col2:
                            st.subheader("Opportunity Analysis")
                            opportunities = analyzer.identify_opportunities(merged_df)
                            st.dataframe(opportunities.head(10),
                                         use_container_width=True)

                    with tab3:
                        st.header("SEO Forecast")

                        # Generate forecasts
                        forecaster = SEOForecaster()

                        for period in forecast_periods:
                            with st.expander(f"{period}-Day Forecast",
                                             expanded=True):
                                forecast = forecaster.forecast_performance(
                                    merged_df, period, avg_improvement
                                )

                                col1, col2, col3 = st.columns(3)

                                with col1:
                                    st.metric(
                                        "Projected Clicks",
                                        f"{forecast['total_projected_clicks']:,}",
                                        f"{forecast['clicks_increase_pct']:.1f}%"
                                    )

                                with col2:
                                    st.metric(
                                        "Projected Traffic Value",
                                        f"${forecast['traffic_value']:,.0f}",
                                        f"{forecast['value_increase_pct']:.1f}%"
                                    )

                                with col3:
                                    st.metric(
                                        "Keywords in Top 10",
                                        f"{forecast['keywords_top_10']}",
                                        f"{forecast['top10_increase']}"
                                    )

                                # Forecast details
                                st.subheader("Keyword-Level Forecast")
                                forecast_df = forecast['keyword_forecasts']

                                # Filter and display
                                min_volume = st.slider(
                                    "Minimum Search Volume",
                                    min_value=0,
                                    max_value=int(merged_df['Search Volume'].max()),
                                    value=100,
                                    key=f"volume_{period}"
                                )

                                filtered_forecast = forecast_df[
                                    forecast_df['Search Volume'] >= min_volume
                                ].nlargest(20, 'Projected Clicks')

                                st.dataframe(
                                    filtered_forecast[[
                                        'Keyword', 'Current Position',
                                        'Projected Position', 'Current Clicks',
                                        'Projected Clicks', 'Search Volume'
                                    ]],
                                    use_container_width=True
                                )

                                # Visualize forecast
                                fig = chart_gen.create_forecast_timeline_chart(forecast_df)
                                st.plotly_chart(fig, use_container_width=True)

                    with tab4:
                        st.header("Raw Data")

                        # Data download
                        csv = merged_df.to_csv(index=False)
                        st.download_button(
                            label="Download Merged Data",
                            data=csv,
                            file_name="seo_forecast_data.csv",
                            mime="text/csv"
                        )

                        # Display raw data
                        st.dataframe(merged_df, use_container_width=True)

                        # Data summary
                        st.subheader("Data Summary")
                        summary = merged_df.describe()
                        st.dataframe(summary)

                else:
                    st.error("No matching keywords found between GSC and SEMrush data")
            else:
                st.error("Please upload valid data files or use sample data")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        logger.error(f"Application error: {e}", exc_info=True)

else:
    # Welcome screen
    st.markdown("""
    ### Welcome to SEO Performance Forecaster

    This tool helps you forecast your website's SEO performance based on:

    1. **Google Search Console data** - Current organic performance
    2. **SEMrush data** - Keyword metrics and opportunities

    ### How to use:

    1. **Upload your data files** in the sidebar
    2. **Configure forecasting parameters** (improvement scenarios, time periods)
    3. **View forecasts** for 90, 180, and 360 days

    ### Required file formats:

    **Google Search Console:**
    - Columns: Query, Clicks, Impressions, CTR, Average Position

    **SEMrush:**
    - Columns: Keyword, Search Volume, Keyword Difficulty, Current Position, URL

    ### Get started:
    Upload your files in the sidebar or check "Use Sample Data" to see the tool
    in action.
    """)

# Footer
st.markdown("---")
st.markdown(
    "Built with Streamlit | For support, contact your SEO team",
    help="Version 1.0.0"
)
