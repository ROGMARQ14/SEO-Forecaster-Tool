"""SEO Forecasting Module for predicting future performance."""

import logging
import pandas as pd
import numpy as np
from typing import Dict

logger = logging.getLogger(__name__)


class SEOForecaster:
    """Forecasts SEO performance based on current data."""

    def __init__(self):
        """Initialize the SEO forecaster."""
        self.improvement_curves = {
            90: {'conservative': 0.3, 'moderate': 0.5, 'aggressive': 0.7},
            120: {'conservative': 0.4, 'moderate': 0.6, 'aggressive': 0.8},
            360: {'conservative': 0.6, 'moderate': 0.8, 'aggressive': 0.9}
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

            improvement_factor = self._calculate_improvement_factor(
                days, avg_improvement
            )

            keyword_forecasts = self._forecast_keywords(
                df, improvement_factor, analyzer
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
        months = days / 30
        base_improvement = avg_improvement * months

        if avg_improvement <= 5:
            factor = base_improvement * 0.7
        elif avg_improvement <= 10:
            factor = base_improvement * 0.85
        else:
            factor = base_improvement * 0.95

        return max(0.1, min(factor, avg_improvement * 2))

    def _forecast_keywords(self, df: pd.DataFrame, improvement_factor: float,
                          analyzer) -> pd.DataFrame:
        """Forecast individual keyword performance."""
        forecasts = []

        for _, row in df.iterrows():
            current_pos = row['Current Position']
            search_volume = row['Search Volume']
            keyword = row['Keyword']

            max_improvement = min(improvement_factor, current_pos - 1)
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
            projected_clicks *= np.random.uniform(0.9, 1.1)

            click_increase = projected_clicks - current_clicks
            improvement_pct = (click_increase / max(current_clicks, 1)) * 100

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
        clicks_increase_pct = (
            (total_projected - total_current) /
            max(total_current, 1)
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
            0: 0.50,      # Very low volume
            100: 1.20,    # Low volume
            1000: 2.50,   # Medium volume
            10000: 5.00,  # High volume
            50000: 8.00   # Very high volume
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
            for days in [90, 120, 360]:
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

            roi = ((traffic_value - investment) / max(investment, 1)) * 100
            payback_period = investment / max(traffic_value / 12, 1)

            return {
                'investment': investment,
                'traffic_value_annual': traffic_value,
                'clicks_increase_annual': clicks_increase,
                'roi_percentage': round(roi, 1),
                'payback_months': round(payback_period, 1),
                'monthly_value': round(traffic_value / 12, 0)
            }

        except Exception as e:
            logger.error(f"Error calculating ROI potential: {e}")
            raise
