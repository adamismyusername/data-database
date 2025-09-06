import os
import requests
from datetime import datetime
from supabase import create_client, Client

# Initialize Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def fetch_bls_data(series_id):
    """Fetch data from BLS API v1 - no key needed"""
    
    # BLS API v1 endpoint - NO KEY REQUIRED
    url = "https://api.bls.gov/publicAPI/v1/timeseries/data/"
    
    headers = {'Content-type': 'application/json'}
    data = {
        "seriesid": [series_id],
        "startyear": "2023",
        "endyear": "2024"
    }
    
    response = requests.post(url, json=data, headers=headers)
    result = response.json()
    
    if result['status'] != 'REQUEST_SUCCEEDED':
        print(f"Full API response: {result}")
        raise Exception(f"BLS API failed: {result.get('message', 'Unknown error')}")
    
    # Parse the latest values
    series_data = result['Results']['series'][0]['data']
    
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
    # Fetch CPI (inflation indicator)
    cpi = fetch_bls_data("CUUR0000SA0")
    store_data("cpi", cpi["high"], cpi["low"], cpi["average"], cpi["raw"])
    
    # Fetch gas prices
    gas = fetch_bls_data("APU0000708111")
    store_data("gas_price", gas["high"], gas["low"], gas["average"], gas["raw"])
    
    print("Done fetching BLS data")
