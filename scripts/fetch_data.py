import os
import requests
from datetime import datetime
from supabase import create_client, Client

# Initialize Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
metals_api_key = os.environ.get("METALS_API_KEY")
supabase: Client = create_client(url, key)

def fetch_latest_bls(series_id):
    """Get the latest data from BLS API v1"""
    
    url = "https://api.bls.gov/publicAPI/v1/timeseries/data/"
    headers = {'Content-type': 'application/json'}
    
    # Get current year data
    current_year = datetime.now().year
    data = {
        "seriesid": [series_id],
        "startyear": str(current_year),
        "endyear": str(current_year)
    }
    
    response = requests.post(url, json=data, headers=headers)
    result = response.json()
    
    if result['status'] != 'REQUEST_SUCCEEDED':
        print(f"BLS API failed for {series_id}: {result.get('message', 'Unknown error')}")
        return None
    
    # Get all data points from this year
    series_data = result['Results']['series'][0]['data']
    return series_data

def fetch_metal_price(metal):
    """Get current spot price for gold or silver"""
    
    if not metals_api_key:
        print(f"No METALS_API_KEY found, skipping {metal}")
        return None
    
    url = f"https://api.metals.dev/v1/metal/spot"
    params = {
        'api_key': metals_api_key,
        'metal': metal,
        'currency': 'USD'
    }
    headers = {'Accept': 'application/json'}
    
    try:
        response = requests.get(url, params=params, headers=headers)
        result = response.json()
        
        if result.get('status') != 'success':
            print(f"Metals API failed for {metal}: {result.get('message', 'Unknown error')}")
            return None
        
        return result
    except Exception as e:
        print(f"Error fetching {metal} price: {e}")
        return None

def update_or_insert_bls(data_type, series_data):
    """Check each BLS data point and insert if new"""
    
    if not series_data:
        print(f"No data for {data_type}")
        return
    
    inserted_count = 0
    updated_count = 0
    
    for point in series_data:
        # Skip empty values
        if not point.get('value') or point['value'].strip() == '':
            continue
            
        # Create date from year and period (M01 = January, etc)
        month = point['period'][1:] if point['period'].startswith('M') else '01'
        date_str = f"{point['year']}-{month}-01"
        
        # Check if this data point already exists
        existing = supabase.table('market_data').select("*").eq(
            'data_type', data_type
        ).eq('date', date_str).execute()
        
        value = float(point['value'])
        
        if existing.data:
            # Check if value changed (BLS sometimes revises data)
            if float(existing.data[0]['average']) != value:
                supabase.table('market_data').update({
                    'average': value,
                    'high': value,
                    'low': value,
                    'raw_data': point
                }).eq('id', existing.data[0]['id']).execute()
                updated_count += 1
                print(f"Updated {data_type} for {date_str}: {value}")
        else:
            # Insert new data point
            supabase.table('market_data').insert({
                'data_type': data_type,
                'date': date_str,
                'average': value,
                'high': value,
                'low': value,
                'raw_data': point
            }).execute()
            inserted_count += 1
            print(f"Inserted {data_type} for {date_str}: {value}")
    
    if inserted_count == 0 and updated_count == 0:
        print(f"No new data for {data_type}")
    else:
        print(f"{data_type}: {inserted_count} new, {updated_count} updated")

def update_metal_price(metal, metal_data):
    """Insert or update metal spot price"""
    
    if not metal_data:
        print(f"No data for {metal}")
        return
    
    rate = metal_data['rate']
    # Use current timestamp from API response, but just the date part
    timestamp = metal_data['timestamp']
    date_str = timestamp.split('T')[0]  # Get just YYYY-MM-DD
    
    # Check if today's price already exists
    existing = supabase.table('market_data').select("*").eq(
        'data_type', metal
    ).eq('date', date_str).execute()
    
    if existing.data:
        # Update with latest price
        supabase.table('market_data').update({
            'average': rate['price'],
            'high': rate['high'],
            'low': rate['low'],
            'raw_data': metal_data
        }).eq('id', existing.data[0]['id']).execute()
        print(f"Updated {metal} for {date_str}: ${rate['price']}")
    else:
        # Insert new price
        supabase.table('market_data').insert({
            'data_type': metal,
            'date': date_str,
            'average': rate['price'],
            'high': rate['high'],
            'low': rate['low'],
            'raw_data': metal_data
        }).execute()
        print(f"Inserted {metal} for {date_str}: ${rate['price']}")

if __name__ == "__main__":
    # Update CPI (monthly data)
    cpi_data = fetch_latest_bls("CUUR0000SA0")
    update_or_insert_bls("cpi", cpi_data)
    
    # Update metal prices (daily data)
    gold_data = fetch_metal_price("gold")
    update_metal_price("gold", gold_data)
    
    silver_data = fetch_metal_price("silver")
    update_metal_price("silver", silver_data)
    
    print("Market data update complete")
