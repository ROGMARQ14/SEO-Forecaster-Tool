"""Data loading and validation utilities."""

import pandas as pd
import numpy as np
import streamlit as st
from typing import Tuple, Optional, Dict, List
import logging

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


class DataLoader:
    """Handles loading and validation of SEO data from various sources."""
    
    # Flexible column mapping for different export formats
    GSC_COLUMN_MAPPINGS = {
        'Query': ['Query', 'query', 'Queries', 'Search Query', 'Search Term'],
        'Clicks': ['Clicks', 'clicks', 'Total Clicks', 'Clicks'],
        'Impressions': ['Impressions', 'impressions', 'Total Impressions', 'Impr.'],
        'Avg. Pos': ['Avg. Pos', 'Average Position', 'Avg Position', 'Position']
    }
    
    SEMRUSH_COLUMN_MAPPINGS = {
        'Keyword': ['Keyword', 'keyword', 'Keywords', 'Query', 'Search Term'],
        'Search Volume': ['Search Volume', 'search volume', 'Volume', 'Vol'],
        'Keyword Difficulty': ['Keyword Difficulty', 'keyword difficulty', 'KD', 'Difficulty'],
        'Position': ['Position', 'position', 'Rank', 'Current Position'],
        'URL': ['URL', 'url', 'Landing Page', 'Page']
    }
    
    @staticmethod
    def _find_columns(df_columns: List[str], mappings: Dict[str, List[str]]) -> Dict[str, str]:
        """Find actual column names based on flexible mappings."""
        column_map = {}
        df_columns_lower = [col.lower() for col in df_columns]
        
        for standard_name, possible_names in mappings.items():
            for possible_name in possible_names:
                if possible_name.lower() in df_columns_lower:
                    actual_index = df_columns_lower.index(possible_name.lower())
                    column_map[standard_name] = df_columns[actual_index]
                    break
        
        return column_map
    
    @staticmethod
    def validate_required_columns(df: pd.DataFrame, required_cols: List[str], data_type: str) -> bool:
        """Validate that all required columns are present before processing."""
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"Missing required columns in {data_type} data: {missing_cols}")
            st.info(f"Available columns: {list(df.columns)}")
            st.info(f"Please ensure your {data_type} export contains all required columns.")
            return False
        return True
    
    @staticmethod
    def clean_and_impute_data(df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """Clean data and handle missing values strategically."""
        # Replace infinite values with NaN
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        
        # Track data quality
        df['__row_has_nan__'] = df.isna().any(axis=1)
        nan_rows_count = df['__row_has_nan__'].sum()
        
        if nan_rows_count > 0:
            st.warning(f"Found {nan_rows_count} rows with missing data in {data_type}")
        
        # Handle missing data based on column type
        if data_type == "GSC":
            # For GSC data, handle numerical columns
            df['Clicks'] = pd.to_numeric(df['Clicks'], errors='coerce').fillna(0)
            df['Impressions'] = pd.to_numeric(df['Impressions'], errors='coerce').fillna(0)
            df['Avg. Pos'] = pd.to_numeric(df['Avg. Pos'], errors='coerce')
            
            # Interpolate position data where possible, fallback to median
            df['Avg. Pos'] = df['Avg. Pos'].interpolate().fillna(df['Avg. Pos'].median())
            
            # Calculate CTR safely
            df['CTR'] = df.apply(lambda row: safe_div(row['Clicks'], row['Impressions'], 0), axis=1)
            
        elif data_type == "SEMrush":
            # For SEMrush data
            df['Search Volume'] = pd.to_numeric(df['Search Volume'], errors='coerce').fillna(0)
            df['Keyword Difficulty'] = pd.to_numeric(df['Keyword Difficulty'], errors='coerce').fillna(50)  # median difficulty
            df['Position'] = pd.to_numeric(df['Position'], errors='coerce').fillna(100)  # worst position
            df['URL'] = df['URL'].fillna("Unknown")
        
        # Remove rows where critical columns are still missing
        critical_cols = ['Query', 'Keyword'] if data_type == "GSC" else ['Keyword']
        for col in critical_cols:
            if col in df.columns:
                df = df[df[col].notna() & (df[col] != '')]
        
        return df
    
    @staticmethod
    @st.cache_data
    def load_gsc_data(file) -> Optional[pd.DataFrame]:
        """Load Google Search Console data from uploaded file."""
        try:
            if file.name.endswith('.csv'):
                file.seek(0)
                sample = file.read(2000).decode('utf-8', errors='ignore')
                file.seek(0)
                
                # Detect delimiter
                delimiter = ';' if sample.count(';') > sample.count(',') else ','
                df = pd.read_csv(file, delimiter=delimiter)
            elif file.name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            else:
                st.error("Use CSV or Excel files")
                return None
            
            # Find actual column names
            column_map = DataLoader._find_columns(
                df.columns.tolist(), 
                DataLoader.GSC_COLUMN_MAPPINGS
            )
            
            # Validate required columns early
            if not DataLoader.validate_required_columns(df, list(column_map.values()), "GSC"):
                return None
            
            # Rename columns to standard names
            df = df.rename(columns=column_map)
            
            # Validate we have the expected columns after mapping
            required_cols = ['Query', 'Clicks', 'Impressions', 'Avg. Pos']
            if not DataLoader.validate_required_columns(df, required_cols, "GSC"):
                return None
            
            # Clean and standardize data
            df['Query'] = df['Query'].astype(str).str.strip()
            
            # Clean and impute data
            df = DataLoader.clean_and_impute_data(df, "GSC")
            
            # Select only required columns
            df = df[['Query', 'Clicks', 'Impressions', 'CTR', 'Avg. Pos']].copy()
            
            # Remove invalid data
            df = df[df['Query'] != ''].dropna()
            
            logger.info(f"Loaded {len(df)} GSC records")
            return df
            
        except Exception as e:
            st.error(f"Error loading GSC: {str(e)}")
            logger.error(f"GSC error: {e}")
            return None
    
    @staticmethod
    @st.cache_data
    def load_semrush_data(file) -> Optional[pd.DataFrame]:
        """Load SEMrush data from uploaded file."""
        try:
            if file.name.endswith('.csv'):
                file.seek(0)
                sample = file.read(2000).decode('utf-8', errors='ignore')
                file.seek(0)
                
                # Detect delimiter
                delimiter = ';' if sample.count(';') > sample.count(',') else ','
                df = pd.read_csv(file, delimiter=delimiter)
            elif file.name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            else:
                st.error("Use CSV or Excel files")
                return None
            
            # Find actual column names
            column_map = DataLoader._find_columns(
                df.columns.tolist(), 
                DataLoader.SEMRUSH_COLUMN_MAPPINGS
            )
            
            # Validate required columns early
            if not DataLoader.validate_required_columns(df, list(column_map.values()), "SEMrush"):
                return None
            
            # Rename columns to standard names
            df = df.rename(columns=column_map)
            
            # Validate we have the expected columns after mapping
            required_cols = ['Keyword', 'Search Volume', 'Keyword Difficulty', 'Position', 'URL']
            if not DataLoader.validate_required_columns(df, required_cols, "SEMrush"):
                return None
            
            # Clean and standardize data
            df['Keyword'] = df['Keyword'].astype(str).str.strip()
            
            # Clean and impute data
            df = DataLoader.clean_and_impute_data(df, "SEMrush")
            
            # Select only required columns
            df = df[['Keyword', 'Search Volume', 'Keyword Difficulty', 'Position', 'URL']].copy()
            
            # Remove invalid data
            df = df[df['Keyword'] != ''].dropna()
            
            logger.info(f"Loaded {len(df)} SEMrush records")
            return df
            
        except Exception as e:
            st.error(f"Error loading SEMrush: {str(e)}")
            logger.error(f"SEMrush error: {e}")
            return None
    
    @staticmethod
    def merge_data(gsc_df: pd.DataFrame, semrush_df: pd.DataFrame) -> pd.DataFrame:
        """Merge GSC and SEMrush data on keyword/query."""
        # Standardize column names for merging
        gsc_df = gsc_df.rename(columns={'Query': 'Keyword'})
        semrush_df = semrush_df.rename(columns={'Position': 'Current Position'})
        
        # Ensure CTR is calculated in GSC data
        if 'CTR' not in gsc_df.columns:
            gsc_df['CTR'] = gsc_df.apply(lambda row: safe_div(row['Clicks'], row['Impressions'], 0), axis=1)
        
        # Merge on keyword
        merged_df = pd.merge(
            gsc_df,
            semrush_df,
            on='Keyword',
            how='inner'
        )
        
        # Calculate additional metrics safely
        merged_df['Potential Traffic'] = (
            merged_df['Search Volume'] * 
            merged_df['CTR']
        )
        
        # Remove duplicates, keeping the best ranking
        merged_df = merged_df.sort_values('Current Position')
        merged_df = merged_df.drop_duplicates('Keyword', keep='first')
        
        logger.info(f"Merged data: {len(merged_df)} keywords")
        return merged_df
    
    @staticmethod
    def validate_data_quality(df: pd.DataFrame) -> Dict[str, any]:
        """Validate data quality and provide summary statistics."""
        if df.empty:
            return {
                'total_keywords': 0,
                'avg_position': 0,
                'total_clicks': 0,
                'total_volume': 0,
                'avg_difficulty': 0,
                'quality_score': 0,
                'rows_with_nan': 0,
                'inf_values_replaced': 0,
                'columns_imputed': 0
            }
        
        # Check for data quality issues
        rows_with_nan = df.get('__row_has_nan__', pd.Series([False])).sum()
        
        metrics = {
            'total_keywords': len(df),
            'avg_position': df['Current Position'].mean(),
            'total_clicks': df['Clicks'].sum(),
            'total_volume': df['Search Volume'].sum(),
            'avg_difficulty': df['Keyword Difficulty'].mean(),
            'quality_score': min(
                100, max(
                    0, 100 - (df['Current Position'].mean() / 10)
                )
            ),
            'rows_with_nan': int(rows_with_nan),
            'inf_values_replaced': 0,  # This would be tracked during cleaning
            'columns_imputed': 0  # This would be tracked during cleaning
        }
        
        return metrics
    
    @staticmethod
    def get_data_quality_report(df: pd.DataFrame) -> Dict[str, any]:
        """Generate comprehensive data quality report."""
        if df.empty:
            return {
                'summary': 'No data available',
                'issues': [],
                'recommendations': []
            }
        
        issues = []
        recommendations = []
        
        # Check for common data quality issues
        if '__row_has_nan__' in df.columns:
            nan_count = df['__row_has_nan__'].sum()
            if nan_count > 0:
                issues.append(f"{nan_count} rows contained missing values (handled)")
                recommendations.append("Consider data export settings to minimize missing values")
        
        # Check position data quality
        if 'Current Position' in df.columns:
            avg_pos = df['Current Position'].mean()
            if avg_pos > 50:
                issues.append(f"Average position is high ({avg_pos:.1f})")
                recommendations.append("Focus on improving rankings for better forecasting accuracy")
        
        # Check volume data
        if 'Search Volume' in df.columns:
            low_volume_count = len(df[df['Search Volume'] < 10])
            if low_volume_count > 0:
                issues.append(f"{low_volume_count} keywords have very low search volume")
                recommendations.append("Consider filtering out very low-volume keywords")
        
        return {
            'summary': f"Analyzed {len(df)} keywords with {len(issues)} issues identified",
            'issues': issues,
            'recommendations': recommendations
        }
    
    @staticmethod
    def get_sample_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Generate sample data for testing purposes."""
        # Sample GSC data
        gsc_data = {
            'Query': [
                'seo tools', 'keyword research', 'backlink analysis',
                'technical seo', 'content optimization'
            ],
            'Clicks': [1200, 800, 600, 400, 350],
            'Impressions': [25000, 18000, 12000, 8000, 6000],
            'Avg. Pos': [8.5, 12.3, 15.7, 18.2, 22.1]
        }
        
        # Sample SEMrush data
        semrush_data = {
            'Keyword': [
                'seo tools', 'keyword research', 'backlink analysis',
                'technical seo', 'content optimization'
            ],
            'Search Volume': [8100, 5400, 2900, 1600, 1300],
            'Keyword Difficulty': [78, 65, 72, 68, 58],
            'Position': [8, 12, 16, 18, 22],
            'URL': [
                'https://example.com/seo-tools',
                'https://example.com/keyword-research',
                'https://example.com/backlink-analysis',
                'https://example.com/technical-seo',
                'https://example.com/content-optimization'
            ]
        }
        
        return pd.DataFrame(gsc_data), pd.DataFrame(semrush_data)
