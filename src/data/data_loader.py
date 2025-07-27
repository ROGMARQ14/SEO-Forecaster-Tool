"""Data loading and validation utilities."""

import pandas as pd
import streamlit as st
from typing import Tuple, Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


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
            
            # Check if all required columns are found
            missing_cols = set(DataLoader.GSC_COLUMN_MAPPINGS.keys()) - set(column_map.keys())
            if missing_cols:
                st.error(f"Missing columns: {missing_cols}")
                st.info(f"Available columns: {list(df.columns)}")
                return None
            
            # Rename columns to standard names
            df = df.rename(columns=column_map)
            
            # Clean and standardize data
            df['Query'] = df['Query'].astype(str).str.strip()
            df['Clicks'] = pd.to_numeric(df['Clicks'], errors='coerce').fillna(0)
            df['Impressions'] = pd.to_numeric(df['Impressions'], errors='coerce').fillna(0)
            df['CTR'] = df['Clicks'] / df['Impressions']
            df['CTR'] = df['CTR'].fillna(0)
            df['Avg. Pos'] = pd.to_numeric(df['Avg. Pos'], errors='coerce')
            
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
            
            # Check if all required columns are found
            missing_cols = set(DataLoader.SEMRUSH_COLUMN_MAPPINGS.keys()) - set(column_map.keys())
            if missing_cols:
                st.error(f"Missing columns: {missing_cols}")
                st.info(f"Available columns: {list(df.columns)}")
                return None
            
            # Rename columns to standard names
            df = df.rename(columns=column_map)
            
            # Clean and standardize data
            df['Keyword'] = df['Keyword'].astype(str).str.strip()
            df['Search Volume'] = pd.to_numeric(df['Search Volume'], errors='coerce').fillna(0)
            df['Keyword Difficulty'] = pd.to_numeric(df['Keyword Difficulty'], errors='coerce').fillna(0)
            df['Position'] = pd.to_numeric(df['Position'], errors='coerce').fillna(100)
            df['URL'] = df['URL'].astype(str).str.strip()
            
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
            gsc_df['CTR'] = gsc_df['Clicks'] / gsc_df['Impressions']
            gsc_df['CTR'] = gsc_df['CTR'].fillna(0)
        
        # Merge on keyword
        merged_df = pd.merge(
            gsc_df,
            semrush_df,
            on='Keyword',
            how='inner'
        )
        
        # Calculate additional metrics
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
                'quality_score': 0
            }
        
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
            )
        }
        
        return metrics
    
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
