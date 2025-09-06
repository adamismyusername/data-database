import os
import requests
from datetime import datetime
from supabase import create_client, Client

# Initialize Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def fetch_bls_data(series_id):
    """Fetch data from BLS API"""
    api_key = os.environ.get("BLS_API_KEY")
    
    # BLS API v2 endpoint (with registration key)
    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    
    # Get latest data
    params = {
        "seriesid": [series_id],
        "registrationkey": api_key,
        "latest": "true"  # Just get recent data
    }
    
    response = requests.post(url, json=params)
    data = response.json()
    
    if data['status'] != 'REQUEST_SUCCEEDED':
        raise Exception(f"BLS API failed: {data.get('message', 'Unknown error')}")
    
    # Parse the latest values
    series_data = data['Results']['series'][0]['data']
    
    # Get high, low, average from recent periods
    values = [float(d['value']) for d in series_data[:12]]  # Last 12 periods
    
    return {
        "high": max(values),
        "low": min(values),
        "average": sum(values) / len(values),
        "latest": float(series_data[0]['value']),
        "raw": series_data[:3]  # Store last 3 periods
    }

def store_data(data_type, high, low, average, raw_data=None):
    """Store in database"""
    try:
        result = supabase.table('market_data').insert({
            'data_type': data_type,
            'high': high,
            'low': low,
            'average': average,
            'raw_data': raw_data
        }).execute()
        print(f"Stored {data_type}: {average}")
    except Exception as e:
        print(f"Failed to store {data_type}: {e}")
        raise

if __name__ == "__main__":
    # Common BLS series IDs
    # CUUR0000SA0 - CPI All Urban Consumers
    # LNS14000000 - Unemployment Rate
    # CES0000000001 - Total Nonfarm Employment
    
    # Fetch unemployment rate
    unemployment = fetch_bls_data("LNS14000000")
    store_data("unemployment_rate", 
               unemployment["high"], 
               unemployment["low"], 
               unemployment["average"], 
               unemployment["raw"])
    
    # Fetch CPI (inflation indicator)
    cpi = fetch_bls_data("CUUR0000SA0")
    store_data("cpi", cpi["high"], cpi["low"], cpi["average"], cpi["raw"])
    
    print("Done fetching BLS data")