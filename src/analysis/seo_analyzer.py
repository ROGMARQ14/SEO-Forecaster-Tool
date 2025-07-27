"""SEO Analysis Module for calculating CTR and identifying opportunities."""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

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


class SEOAnalyzer:
    """Analyzes SEO data to calculate CTR and identify opportunities."""

    def __init__(self):
        """Initialize the SEO analyzer."""
        self.ctr_by_position = None

    def calculate_ctr_by_position(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate CTR statistics by position based on GSC data.

        Args:
            df: DataFrame with GSC data containing 'Current Position' and 'CTR'

        Returns:
            DataFrame with CTR statistics by position
        """
        try:
            # Create position buckets
            df['Position_Bucket'] = pd.cut(
                df['Current Position'],
                bins=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 30, 50, 100],
                labels=['1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
                       '11-15', '16-20', '21-30', '31-50', '51-100']
            )

            # Calculate CTR statistics by position
            ctr_stats = df.groupby('Position_Bucket').agg({
                'CTR': ['mean', 'median', 'std', 'count', 'min', 'max']
            }).round(4)

            # Flatten column names
            ctr_stats.columns = ['CTR_Mean', 'CTR_Median', 'CTR_Std',
                               'Count', 'CTR_Min', 'CTR_Max']
            ctr_stats = ctr_stats.reset_index()

            # Calculate weighted CTR based on volume - using safe_div
            df['Weighted_CTR'] = df['CTR'] * df['Search Volume']
            
            def calculate_weighted_ctr(group):
                total_weighted = group['Weighted_CTR'].sum()
                total_volume = group['Search Volume'].sum()
                return safe_div(total_weighted, total_volume, 0)
            
            weighted_ctr = df.groupby('Position_Bucket').apply(calculate_weighted_ctr).round(4)

            ctr_stats['CTR_Weighted'] = weighted_ctr.values

            self.ctr_by_position = ctr_stats
            return ctr_stats

        except Exception as e:
            logger.error(f"Error calculating CTR by position: {e}")
            raise

    def get_ctr_for_position(self, position: float) -> float:
        """
        Get estimated CTR for a given position.

        Args:
            position: The position to get CTR for

        Returns:
            Estimated CTR value
        """
        if self.ctr_by_position is None:
            logger.warning("CTR data not calculated yet. Using default values.")
            # Default CTR values based on industry averages
            default_ctr = {
                1: 0.315, 2: 0.242, 3: 0.185, 4: 0.142, 5: 0.109,
                6: 0.084, 7: 0.065, 8: 0.050, 9: 0.039, 10: 0.030,
                11: 0.023, 12: 0.018, 13: 0.014, 14: 0.011, 15: 0.008,
                20: 0.003, 30: 0.001, 50: 0.0005, 100: 0.0001
            }

            # Find closest position
            closest_pos = min(default_ctr.keys(),
                            key=lambda x: abs(x - position))
            return default_ctr[closest_pos]

        # Find the appropriate bucket
        if position <= 1:
            bucket = '1'
        elif position <= 2:
            bucket = '2'
        elif position <= 3:
            bucket = '3'
        elif position <= 4:
            bucket = '4'
        elif position <= 5:
            bucket = '5'
        elif position <= 6:
            bucket = '6'
        elif position <= 7:
            bucket = '7'
        elif position <= 8:
            bucket = '8'
        elif position <= 9:
            bucket = '9'
        elif position <= 10:
            bucket = '10'
        elif position <= 15:
            bucket = '11-15'
        elif position <= 20:
            bucket = '16-20'
        elif position <= 30:
            bucket = '21-30'
        elif position <= 50:
            bucket = '31-50'
        else:
            bucket = '51-100'

        ctr_row = self.ctr_by_position[
            self.ctr_by_position['Position_Bucket'] == bucket
        ]

        if not ctr_row.empty:
            return float(ctr_row['CTR_Mean'].iloc[0])
        else:
            return 0.01  # Default fallback

    def identify_opportunities(self, df: pd.DataFrame,
                             min_volume: int = 100,
                             max_position: int = 30) -> pd.DataFrame:
        """
        Identify keyword opportunities based on volume and position.

        Args:
            df: DataFrame with keyword data
            min_volume: Minimum search volume to consider
            max_position: Maximum position to consider (lower is better)

        Returns:
            DataFrame with identified opportunities
        """
        try:
            # Filter for opportunities
            opportunities = df[
                (df['Search Volume'] >= min_volume) &
                (df['Current Position'] <= max_position) &
                (df['Current Position'] > 1)
            ].copy()

            if opportunities.empty:
                logger.warning("No opportunities found with current filters")
                return pd.DataFrame()

            # Calculate opportunity score using safe_div
            opportunities['Opportunity_Score'] = (
                opportunities['Search Volume'] *
                opportunities.apply(lambda row: safe_div(1, row['Current Position'], 0), axis=1) *
                opportunities.apply(lambda row: safe_div(100 - row['Keyword Difficulty'], 100, 0), axis=1)
            )

            # Calculate potential clicks if improved
            opportunities['Current_CTR'] = opportunities['Current Position'].apply(
                self.get_ctr_for_position
            )
            opportunities['Current_Clicks_Est'] = (
                opportunities['Search Volume'] * opportunities['Current_CTR']
            )

            # Calculate potential if moved to position 3
            target_ctr = self.get_ctr_for_position(3)
            opportunities['Potential_Clicks'] = (
                opportunities['Search Volume'] * target_ctr
            )
            opportunities['Click_Increase'] = (
                opportunities['Potential_Clicks'] - opportunities['Current_Clicks_Est']
            )

            # Sort by opportunity score
            opportunities = opportunities.sort_values(
                'Opportunity_Score', ascending=False
            )

            return opportunities[[
                'Keyword', 'Current Position', 'Search Volume',
                'Keyword Difficulty', 'Opportunity_Score',
                'Current_Clicks_Est', 'Potential_Clicks', 'Click_Increase'
            ]]

        except Exception as e:
            logger.error(f"Error identifying opportunities: {e}")
            raise

    def calculate_keyword_difficulty_impact(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze the impact of keyword difficulty on ranking improvements.

        Args:
            df: DataFrame with keyword data

        Returns:
            DataFrame with difficulty impact analysis
        """
        try:
            # Create difficulty buckets
            df['Difficulty_Bucket'] = pd.cut(
                df['Keyword Difficulty'],
                bins=[0, 20, 40, 60, 80, 100],
                labels=['Very Easy', 'Easy', 'Medium', 'Hard', 'Very Hard']
            )

            # Calculate average position by difficulty
            difficulty_analysis = df.groupby('Difficulty_Bucket').agg({
                'Current Position': ['mean', 'median', 'count'],
                'Search Volume': ['mean', 'sum'],
                'Keyword': 'count'
            }).round(2)

            # Flatten column names
            difficulty_analysis.columns = [
                'Avg_Position', 'Median_Position', 'Keyword_Count',
                'Avg_Volume', 'Total_Volume', 'Unique_Keywords'
            ]
            difficulty_analysis = difficulty_analysis.reset_index()

            return difficulty_analysis

        except Exception as e:
            logger.error(f"Error calculating keyword difficulty impact: {e}")
            raise

    def get_competitive_analysis(self, df: pd.DataFrame) -> Dict:
        """
        Get competitive analysis metrics.

        Args:
            df: DataFrame with keyword data

        Returns:
            Dictionary with competitive metrics
        """
        try:
            total_keywords = len(df)
            keywords_top_3 = len(df[df['Current Position'] <= 3])
            keywords_top_10 = len(df[df['Current Position'] <= 10])
            keywords_top_20 = len(df[df['Current Position'] <= 20])

            avg_position = df['Current Position'].mean()
            median_position = df['Current Position'].median()
            avg_difficulty = df['Keyword Difficulty'].mean()

            total_volume = df['Search Volume'].sum()
            captured_volume = df[df['Current Position'] <= 10]['Search Volume'].sum()
            
            # Use safe_div for market share calculation
            market_share = safe_div(captured_volume, total_volume, 0) * 100

            return {
                'total_keywords': total_keywords,
                'keywords_top_3': keywords_top_3,
                'keywords_top_10': keywords_top_10,
                'keywords_top_20': keywords_top_20,
                'avg_position': round(avg_position, 2),
                'median_position': round(median_position, 2),
                'avg_difficulty': round(avg_difficulty, 2),
                'total_search_volume': total_volume,
                'captured_volume': captured_volume,
                'market_share': round(market_share, 2)
            }

        except Exception as e:
            logger.error(f"Error getting competitive analysis: {e}")
            raise
