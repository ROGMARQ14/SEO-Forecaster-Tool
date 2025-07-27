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
        color: #1f2937;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #6b7280;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-container {
        background: linear-gradient(90deg, #f3f4f6 0%, #e5e7eb 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .data-quality-good {
        background-color: #d1fae5;
        border-left: 4px solid #10b981;
        padding: 1rem;
        margin: 1rem 0;
    }
    .data-quality-warning {
        background-color: #fef3cd;
        border-left: 4px solid #f59e0b;
        padding: 1rem;
        margin: 1rem 0;
    }
    .data-quality-error {
        background-color: #fee2e2;
        border-left: 4px solid #ef4444;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">SEO Performance Forecaster</h1>',
           unsafe_allow_html=True)
st.markdown('<p class="subtitle">Forecast your website\'s SEO performance for the next 90, 180, and 360 days</p>',
           unsafe_allow_html=True)

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

    # Advanced options
    st.header("⚙️ Advanced Options")
    
    # Data handling preferences
    with st.expander("Data Quality Settings"):
        handle_missing_data = st.selectbox(
            "Handle Missing Data",
            options=["Impute with median/interpolation", "Drop rows with missing data"],
            index=0,
            help="Choose how to handle missing data in your exports"
        )
        
        min_search_volume = st.number_input(
            "Minimum Search Volume Filter",
            min_value=0,
            max_value=1000,
            value=10,
            help="Filter out keywords below this search volume"
        )

    # Forecasting parameters
    st.header("📈 Forecasting Settings")

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

                # Apply minimum search volume filter
                if min_search_volume > 0:
                    merged_df = merged_df[merged_df['Search Volume'] >= min_search_volume]
                    st.info(f"Applied minimum search volume filter: {min_search_volume}")

                if not merged_df.empty:
                    # Data Quality Report (Solution 5)
                    st.header("📋 Data Quality Report")
                    
                    with st.expander("📊 Detailed Data Quality Analysis", expanded=True):
                        quality_report = DataLoader.get_data_quality_report(merged_df)
                        quality_metrics = DataLoader.validate_data_quality(merged_df)
                        
                        # Summary
                        st.subheader("Summary")
                        st.write(quality_report['summary'])
                        
                        # Key Metrics
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Keywords", f"{quality_metrics['total_keywords']:,}")
                        with col2:
                            st.metric("Avg Position", f"{quality_metrics['avg_position']:.1f}")
                        with col3:
                            st.metric("Total Clicks", f"{quality_metrics['total_clicks']:,}")
                        with col4:
                            st.metric("Quality Score", f"{quality_metrics['quality_score']:.0f}/100")
                        
                        # Additional Quality Metrics
                        col5, col6, col7, col8 = st.columns(4)
                        with col5:
                            st.metric("Total Search Volume", f"{quality_metrics['total_volume']:,}")
                        with col6:
                            st.metric("Avg Difficulty", f"{quality_metrics['avg_difficulty']:.1f}")
                        with col7:
                            st.metric("Rows with Issues", f"{quality_metrics['rows_with_nan']}")
                        with col8:
                            market_share = quality_metrics.get('market_share', 0)
                            st.metric("Market Share", f"{market_share:.1f}%")
                        
                        # Issues and Recommendations
                        if quality_report['issues']:
                            st.subheader("⚠️ Data Quality Issues")
                            for issue in quality_report['issues']:
                                if "high" in issue.lower() or "missing" in issue.lower():
                                    st.markdown(f'<div class="data-quality-warning">• {issue}</div>', 
                                              unsafe_allow_html=True)
                                else:
                                    st.markdown(f'<div class="data-quality-good">• {issue}</div>', 
                                              unsafe_allow_html=True)
                        
                        if quality_report['recommendations']:
                            st.subheader("💡 Recommendations")
                            for rec in quality_report['recommendations']:
                                st.info(f"• {rec}")
                        
                        # Data Distribution Insights
                        st.subheader("📈 Data Distribution Insights")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Position distribution
                            pos_dist = {
                                "Top 3": len(merged_df[merged_df['Current Position'] <= 3]),
                                "4-10": len(merged_df[(merged_df['Current Position'] > 3) & 
                                                    (merged_df['Current Position'] <= 10)]),
                                "11-20": len(merged_df[(merged_df['Current Position'] > 10) & 
                                                     (merged_df['Current Position'] <= 20)]),
                                "21-50": len(merged_df[(merged_df['Current Position'] > 20) & 
                                                     (merged_df['Current Position'] <= 50)]),
                                "50+": len(merged_df[merged_df['Current Position'] > 50])
                            }
                            st.write("**Position Distribution:**")
                            for pos_range, count in pos_dist.items():
                                pct = (count / len(merged_df)) * 100 if len(merged_df) > 0 else 0
                                st.write(f"• {pos_range}: {count} keywords ({pct:.1f}%)")
                        
                        with col2:
                            # Volume distribution
                            vol_dist = {
                                "High Volume (10K+)": len(merged_df[merged_df['Search Volume'] >= 10000]),
                                "Medium Volume (1K-10K)": len(merged_df[(merged_df['Search Volume'] >= 1000) & 
                                                                       (merged_df['Search Volume'] < 10000)]),
                                "Low Volume (100-1K)": len(merged_df[(merged_df['Search Volume'] >= 100) & 
                                                                   (merged_df['Search Volume'] < 1000)]),
                                "Very Low Volume (<100)": len(merged_df[merged_df['Search Volume'] < 100])
                            }
                            st.write("**Volume Distribution:**")
                            for vol_range, count in vol_dist.items():
                                pct = (count / len(merged_df)) * 100 if len(merged_df) > 0 else 0
                                st.write(f"• {vol_range}: {count} keywords ({pct:.1f}%)")

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
                                try:
                                    fig = chart_gen.create_forecast_timeline_chart(forecast_df)
                                    st.plotly_chart(fig, use_container_width=True)
                                except Exception as e:
                                    st.warning(f"Could not generate timeline chart: {str(e)}")

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
        
        # Show debug information in expander
        with st.expander("🐛 Debug Information"):
            st.code(f"Error: {str(e)}")
            st.write("If this error persists, please check:")
            st.write("• File format is CSV or Excel")
            st.write("• Required columns are present")
            st.write("• Data contains valid values")

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
    3. **Review data quality report** to ensure accurate forecasts
    4. **View forecasts** for 90, 180, and 360 days

    ### Required file formats:

    **Google Search Console:**
    - Columns: Query, Clicks, Impressions, CTR, Average Position

    **SEMrush:**
    - Columns: Keyword, Search Volume, Keyword Difficulty, Current Position, URL

    ### New Features:
    
    ✅ **Data Quality Reporting** - Comprehensive analysis of your data quality  
    ✅ **Safe Division Protection** - Prevents crashes from invalid data  
    ✅ **Advanced Data Handling** - Smart imputation and missing data strategies  
    ✅ **Enhanced Error Handling** - Better error messages and debugging info  

    ### Get started:
    Upload your files in the sidebar or check "Use Sample Data" to see the tool
    in action.
    """)

# Footer
st.markdown("---")
st.markdown(
    "Built with Streamlit | For support, contact your SEO team | Version 1.1.0 - Enhanced with Data Safety Features",
    help="Enhanced version with safe division protection and data quality reporting"
)
