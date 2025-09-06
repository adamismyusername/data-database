import os
import requests
from datetime import datetime
from supabase import create_client, Client

# Initialize Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
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

def update_or_insert(data_type, series_data):
    """Check each data point and insert if new"""
    
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

if __name__ == "__main__":
    # Update CPI
    cpi_data = fetch_latest_bls("CUUR0000SA0")
    update_or_insert("cpi", cpi_data)
    
    # If you want to add more series later:
    # gas_data = fetch_latest_bls("APU0000708111")
    # update_or_insert("gas_price", gas_data)
    
    print("BLS data check complete")
