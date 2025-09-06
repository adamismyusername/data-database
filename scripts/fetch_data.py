import os
import requests
from datetime import datetime
from supabase import create_client, Client

# Initialize Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def fetch_gold_price():
    """Get gold price - replace with your actual API"""
    # Example with Alpha Vantage (get your own free key)
    api_key = os.environ.get("ALPHA_VANTAGE_KEY")
    
    # Replace this with your actual gold API
    response = requests.get(f"https://some-gold-api.com/price")
    data = response.json()
    
    # Parse however your API returns it
    return {
        "high": data.get("high", 0),
        "low": data.get("low", 0),
        "average": (data.get("high", 0) + data.get("low", 0)) / 2,
        "raw": data
    }

def fetch_dow_jones():
    """Get Dow Jones - implement based on your API"""
    # Similar to above
    pass

def store_data(data_type, high, low, average, raw_data=None):
    """Shove it in the database"""
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
    # Fetch and store gold
    gold = fetch_gold_price()
    store_data("gold", gold["high"], gold["low"], gold["average"], gold["raw"])
    
    # Fetch and store Dow Jones
    # dow = fetch_dow_jones()
    # store_data("dow_jones", dow["high"], dow["low"], dow["average"], dow["raw"])
    
    print("Done. Go build something useful now.")