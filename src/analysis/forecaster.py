"""SEO Forecasting Module for predicting future performance."""

import logging
import pandas as pd
import numpy as np
from typing import Dict

logger = logging.getLogger(__name__)


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


class SEOForecaster:
    """Forecasts SEO performance based on current data."""

    def __init__(self):
        """Initialize the SEO forecaster."""
        # FIXED: More logical scaling for different periods
        self.improvement_scaling = {
            90: 0.25,   # 25% of full potential in 3 months
            180: 0.60,  # 60% of full potential in 6 months  
            360: 1.0    # 100% of full potential in 12 months
        }

    def forecast_performance(self, df: pd.DataFrame, days: int,
                           avg_improvement: int) -> Dict:
        """
        Forecast SEO performance for a given time period.

        Args:
            df: DataFrame with current keyword data
            days: Number of days to forecast
            avg_improvement: Average position improvement per keyword

        Returns:
            Dictionary with forecast results
        """
        try:
            from .seo_analyzer import SEOAnalyzer
            analyzer = SEOAnalyzer()
            analyzer.calculate_ctr_by_position(df)

            # FIXED: Use proper scaling based on time period
            time_scaling = self.improvement_scaling.get(days, days / 360)
            actual_improvement = avg_improvement * time_scaling

            keyword_forecasts = self._forecast_keywords(
                df, actual_improvement, analyzer
            )

            total_metrics = self._calculate_aggregate_metrics(
                keyword_forecasts
            )

            traffic_value = self._calculate_traffic_value(
                keyword_forecasts
            )

            return {
                'keyword_forecasts': keyword_forecasts,
                'total_projected_clicks': total_metrics[
                    'total_projected_clicks'
                ],
                'total_current_clicks': total_metrics[
                    'total_current_clicks'
                ],
                'clicks_increase_pct': total_metrics['clicks_increase_pct'],
                'traffic_value': traffic_value,
                'keywords_top_10': total_metrics['keywords_top_10'],
                'top10_increase': total_metrics['top10_increase'],
                'value_increase_pct': total_metrics['value_increase_pct']
            }

        except Exception as e:
            logger.error(f"Error forecasting performance: {e}")
            raise

    def _calculate_improvement_factor(self, days: int,
                                    avg_improvement: int) -> float:
        """Calculate realistic improvement factor based on time period."""
        # REMOVED: Old inconsistent logic
        # NEW: Direct scaling based on time period
        time_scaling = self.improvement_scaling.get(days, days / 360)
        return avg_improvement * time_scaling

    def _forecast_keywords(self, df: pd.DataFrame, improvement_factor: float,
                          analyzer) -> pd.DataFrame:
        """Forecast individual keyword performance."""
        forecasts = []

        for _, row in df.iterrows():
            current_pos = row['Current Position']
            search_volume = row['Search Volume']
            keyword = row['Keyword']

            # Calculate position improvement based on current position
            max_improvement = min(improvement_factor, current_pos - 1)
            
            # Apply diminishing returns for already high-ranking keywords
            if current_pos <= 3:
                max_improvement *= 0.3
            elif current_pos <= 10:
                max_improvement *= 0.6
            else:
                max_improvement *= 0.9

            projected_pos = max(1, current_pos - max_improvement)

            current_ctr = analyzer.get_ctr_for_position(current_pos)
            projected_ctr = analyzer.get_ctr_for_position(projected_pos)

            current_clicks = search_volume * current_ctr
            projected_clicks = search_volume * projected_ctr
            
            # REMOVED: Random variation that made forecasts inconsistent
            # projected_clicks *= np.random.uniform(0.9, 1.1)

            click_increase = projected_clicks - current_clicks
            
            # Use safe_div for improvement percentage calculation
            improvement_pct = safe_div(click_increase, max(current_clicks, 1), 0) * 100

            forecasts.append({
                'Keyword': keyword,
                'Current Position': current_pos,
                'Projected Position': round(projected_pos, 1),
                'Search Volume': search_volume,
                'Current CTR': round(current_ctr, 4),
                'Projected CTR': round(projected_ctr, 4),
                'Current Clicks': round(current_clicks, 0),
                'Projected Clicks': round(projected_clicks, 0),
                'Click Increase': round(click_increase, 0),
                'Click Improvement %': round(improvement_pct, 1)
            })

        return pd.DataFrame(forecasts)

    def _calculate_aggregate_metrics(self, keyword_forecasts: pd.DataFrame) -> Dict:
        """Calculate aggregate forecast metrics."""
        total_current = keyword_forecasts['Current Clicks'].sum()
        total_projected = keyword_forecasts['Projected Clicks'].sum()
        
        # Use safe_div for percentage calculation
        clicks_increase_pct = safe_div(
            (total_projected - total_current),
            max(total_current, 1),
            0
        ) * 100

        current_top_10 = len(
            keyword_forecasts[keyword_forecasts['Current Position'] <= 10]
        )
        projected_top_10 = len(
            keyword_forecasts[keyword_forecasts['Projected Position'] <= 10]
        )
        top10_increase = projected_top_10 - current_top_10

        return {
            'total_current_clicks': int(total_current),
            'total_projected_clicks': int(total_projected),
            'clicks_increase_pct': round(clicks_increase_pct, 1),
            'keywords_top_10': projected_top_10,
            'top10_increase': top10_increase,
            'value_increase_pct': round(clicks_increase_pct * 0.95, 1)
        }

    def _calculate_traffic_value(self, keyword_forecasts: pd.DataFrame) -> float:
        """Calculate estimated traffic value based on clicks and CPC."""
        # Industry average CPC by search volume ranges
        cpc_mapping = {
            0: 0.50,     # Very low volume
            100: 1.20,   # Low volume
            1000: 2.50,  # Medium volume
            10000: 5.00, # High volume
            50000: 8.00  # Very high volume
        }

        total_value = 0
        for _, row in keyword_forecasts.iterrows():
            volume = row['Search Volume']
            clicks = row['Projected Clicks']

            # Find appropriate CPC
            cpc = 0.50  # Default
            for vol_threshold, cpc_value in sorted(cpc_mapping.items(), reverse=True):
                if volume >= vol_threshold:
                    cpc = cpc_value
                    break

            total_value += clicks * cpc

        return round(total_value, 0)

    def generate_scenarios(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """Generate multiple forecasting scenarios."""
        scenarios = {
            'conservative': {
                'improvement': 5,
                'label': 'Conservative (5 positions)'
            },
            'moderate': {
                'improvement': 10,
                'label': 'Moderate (10 positions)'
            },
            'aggressive': {
                'improvement': 15,
                'label': 'Aggressive (15 positions)'
            }
        }

        results = {}
        for scenario_name, config in scenarios.items():
            scenario_results = {}
            for days in [90, 180, 360]:
                forecast = self.forecast_performance(
                    df, days, config['improvement']
                )
                scenario_results[days] = forecast
            results[scenario_name] = scenario_results

        return results

    def create_timeline_forecast(self, df: pd.DataFrame,
                               improvement_rate: int) -> pd.DataFrame:
        """Create a monthly timeline forecast for visualization."""
        timeline_data = []
        months = list(range(1, 13))  # 12 months

        for month in months:
            days = month * 30
            forecast = self.forecast_performance(df, days, improvement_rate)

            timeline_data.append({
                'Month': month,
                'Days': days,
                'Projected_Clicks': forecast['total_projected_clicks'],
                'Current_Clicks': forecast['total_current_clicks'],
                'Traffic_Value': forecast['traffic_value'],
                'Keywords_Top_10': forecast['keywords_top_10']
            })

        return pd.DataFrame(timeline_data)

    def calculate_roi_potential(self, df: pd.DataFrame, investment: float,
                              improvement_rate: int) -> Dict:
        """Calculate ROI potential based on investment and expected improvements."""
        try:
            forecast = self.forecast_performance(df, 360, improvement_rate)

            traffic_value = forecast['traffic_value']
            clicks_increase = (
                forecast['total_projected_clicks'] -
                forecast['total_current_clicks']
            )

            # Use safe_div for ROI and payback calculations
            roi = safe_div((traffic_value - investment), max(investment, 1), 0) * 100
            monthly_value = safe_div(traffic_value, 12, 0)
            payback_period = safe_div(investment, max(monthly_value, 1), 0)

            return {
                'investment': investment,
                'traffic_value_annual': traffic_value,
                'clicks_increase_annual': clicks_increase,
                'roi_percentage': round(roi, 1),
                'payback_months': round(payback_period, 1),
                'monthly_value': round(monthly_value, 0)
            }

        except Exception as e:
            logger.error(f"Error calculating ROI potential: {e}")
            raise
