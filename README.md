# SEO Performance Forecaster

A comprehensive Python application for forecasting SEO performance based on Google Search Console and SEMrush data. Built with Streamlit for easy deployment and interactive analysis.

## 🎯 Features

- **Multi-period forecasting**: 90, 120, and 360-day forecasts
- **CTR-based traffic estimation**: Uses actual CTR data by position
- **Scenario modeling**: Conservative, moderate, aggressive, and custom improvement scenarios
- **Interactive visualizations**: Charts and graphs for data exploration
- **Data quality validation**: Built-in data quality checks and metrics
- **Export capabilities**: Download processed data and forecasts

## 📊 How It Works

The application uses a sophisticated forecasting model that:

1. **Analyzes current performance** from Google Search Console data
2. **Cross-references keyword metrics** from SEMrush (search volume, difficulty, current positions)
3. **Calculates CTR curves** based on actual position data
4. **Projects traffic improvements** based on ranking improvements
5. **Estimates traffic value** using industry-standard CPC rates

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone [your-repo-url]
   cd seo-forecaster-tool
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python run.py
   ```
   Or directly:
   ```bash
   streamlit run app.py
   ```

### Streamlit Cloud Deployment

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin [your-repo-url]
   git push -u origin main
   ```

2. **Deploy to Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub account
   - Select the repository
   - Set the main file path to `app.py`
   - Click "Deploy"

## 📁 Project Structure

```
seo-forecaster-tool/
├── app.py                 # Main Streamlit application
├── run.py                 # Entry point script
├── requirements.txt       # Python dependencies
├── setup.py              # Package setup
├── README.md             # This file
├── .gitignore            # Git ignore rules
├── src/                  # Source code
│   ├── __init__.py
│   ├── data/            # Data loading and processing
│   │   ├── __init__.py
│   │   └── data_loader.py
│   ├── analysis/        # SEO analysis and forecasting
│   │   ├── __init__.py
│   │   ├── seo_analyzer.py
│   │   └── forecaster.py
│   └── visualization/   # Charts and visualizations
│       ├── __init__.py
│       └── charts.py
└── examples/            # Sample data files
    ├── sample_gsc_data.csv
    └── sample_semrush_data.csv
```

## 📊 Data Requirements

### Google Search Console Data
Required columns:
- **Query**: Search query/keyword
- **Clicks**: Number of clicks
- **Impressions**: Number of impressions
- **CTR**: Click-through rate (as percentage)
- **Average Position**: Average ranking position

### SEMrush Data
Required columns:
- **Keyword**: Search keyword
- **Search Volume**: Monthly search volume
- **Keyword Difficulty**: SEO difficulty score (0-100)
- **Current Position**: Current ranking position
- **URL**: Ranking URL

## 🎛️ Usage Guide

### 1. Upload Data
- Upload your Google Search Console CSV/Excel file
- Upload your SEMrush CSV/Excel file
- Or use sample data for testing

### 2. Configure Forecasting
- **Improvement Scenario**: Choose how much you expect to improve rankings
  - Conservative: 5 positions average improvement
  - Moderate: 10 positions average improvement
  - Aggressive: 15 positions average improvement
  - Custom: Set your own improvement value

- **Forecast Periods**: Select 90, 120, and/or 360 days

### 3. Analyze Results
- **Overview Tab**: High-level metrics and top keywords
- **Analysis Tab**: CTR analysis and opportunity identification
- **Forecast Tab**: Detailed projections for each time period
- **Data Tab**: Raw data and export options

## 🔍 Key Metrics

- **Projected Clicks**: Estimated clicks based on ranking improvements
- **Traffic Value**: Estimated value of traffic (based on CPC rates)
- **Keywords in Top 10**: Number of keywords expected to reach top 10
- **CTR by Position**: Click-through rates for different ranking positions
- **Opportunity Score**: Keywords with highest potential for improvement

## 🛠️ Technical Details

### Dependencies
- **streamlit**: Web application framework
- **pandas**: Data manipulation
- **numpy**: Numerical computations
- **plotly**: Interactive visualizations
- **scikit-learn**: Machine learning utilities

### Forecasting Model
The forecasting model uses:
- **CTR curves**: Derived from actual GSC data
- **Search volume**: From SEMrush data
- **Keyword difficulty**: To adjust improvement probability
- **Current position**: Baseline for improvement calculations

### Traffic Value Calculation
Traffic value is estimated using:
- Industry average CPC rates by keyword category
- Projected clicks based on CTR and search volume
- Conservative estimates for reliability

## 🐛 Troubleshooting

### Common Issues

1. **Import errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version (3.7+ required)

2. **Data loading issues**
   - Verify file formats (CSV, Excel)
   - Check required columns are present
   - Ensure data is clean (no missing values in key columns)

3. **Streamlit deployment issues**
   - Check requirements.txt includes all dependencies
   - Verify file paths in the repository
   - Check Streamlit Cloud logs for specific errors

### Data Quality Tips
- Use recent data (last 3-6 months)
- Ensure sufficient keyword volume (>100 keywords recommended)
- Remove branded keywords for more accurate forecasting
- Filter out very low-volume keywords (<10 searches/month)

## 📈 Example Use Cases

1. **Client Reporting**: Generate 90-day forecasts for client presentations
2. **Campaign Planning**: Estimate traffic impact of SEO campaigns
3. **Budget Allocation**: Prioritize keywords with highest ROI potential
4. **Performance Tracking**: Compare actual vs. forecasted performance

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support, please:
1. Check the troubleshooting section above
2. Review the Streamlit documentation
3. Open an issue on GitHub with detailed error information

## 🔄 Updates

To update the application:
1. Pull latest changes: `git pull origin main`
2. Update dependencies: `pip install -r requirements.txt --upgrade`
3. Restart the application

---

**Built with ❤️ for the SEO community**
