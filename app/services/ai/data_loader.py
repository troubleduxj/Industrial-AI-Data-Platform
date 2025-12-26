import pandas as pd
from typing import Optional, List
from app.services.tdengine_service import TDengineService
import logging

logger = logging.getLogger(__name__)

class TDengineLoader:
    def __init__(self):
        self.td_service = TDengineService()

    async def load(self, device_id: str, start_time: str, end_time: str) -> pd.DataFrame:
        """
        Load data from TDengine for a specific device within a time range.
        
        Args:
            device_id: The ID of the device to fetch data for.
            start_time: Start time string (e.g. '2023-01-01 00:00:00').
            end_time: End time string.
            
        Returns:
            pd.DataFrame: DataFrame containing the queried data.
        """
        # Assuming query on 'device_data' supertable or similar.
        # We need to ensure we select relevant columns.
        # For now, let's select 'ts' and 'value'.
        # TODO: Make columns configurable or dynamic based on model requirements.
        
        sql = f"""
            SELECT ts, value 
            FROM device_data 
            WHERE device_id = '{device_id}' 
            AND ts >= '{start_time}' AND ts <= '{end_time}'
        """
        
        try:
            result = await self.td_service.execute_query(sql)
            
            if result and 'data' in result and 'head' in result:
                df = pd.DataFrame(result['data'], columns=result['head'])
                return df
            else:
                logger.warning(f"No data found or invalid format for device {device_id}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error loading data from TDengine: {e}")
            raise

    async def preprocess(self, df: pd.DataFrame, strategy: str = 'standard') -> pd.DataFrame:
        """
        Preprocess the loaded data.
        """
        if df.empty:
            return df
            
        # Example preprocessing
        if strategy == 'fill_na':
            df = df.fillna(method='ffill').fillna(method='bfill')
        
        return df
