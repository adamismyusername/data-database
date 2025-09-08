# Pulling Data from Supabase Database

Dead simple guide to accessing your economic data from the Supabase database. No fluff, just what you need.

## What This Is

You've got a Supabase database that automatically updates with economic data twice a day via GitHub Actions. This README shows you how to pull that data into your apps.

## Quick Setup

Grab these from your Supabase dashboard:
- **URL**: `https://[your-project].supabase.co`
- **Anon Key**: That long public key (starts with `eyJ...`)

## JavaScript/React

### Install
```bash
npm install @supabase/supabase-js
```

### Connect
```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  'https://your-project.supabase.co',
  'your-anon-key'
)
```

### Common Queries

#### Get Latest CPI
```javascript
const { data, error } = await supabase
  .from('market_data')
  .select('*')
  .eq('data_type', 'cpi')
  .order('date', { ascending: false })
  .limit(1)
  .single()

// data.average has your latest CPI value
```

#### Get Historical Data for Charts
```javascript
const { data, error } = await supabase
  .from('market_data')
  .select('date, average')
  .eq('data_type', 'cpi')
  .order('date', { ascending: true })
  .gte('date', '2020-01-01')  // Last 5 years

// Returns array ready for Chart.js, Recharts, etc.
```

#### Calculate Inflation Rate
```javascript
// Compare this year to last year
const currentYear = new Date().getFullYear()
const { data } = await supabase
  .from('market_data')
  .select('date, average')
  .eq('data_type', 'cpi')
  .in('date', [
    `${currentYear}-01-01`,
    `${currentYear - 1}-01-01`
  ])

const inflation = ((data[1].average - data[0].average) / data[0].average) * 100
```

## Python

### Install
```bash
pip install supabase
```

### Usage
```python
from supabase import create_client
import os

supabase = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)

# Get latest CPI
result = supabase.table('market_data') \
    .select("*") \
    .eq('data_type', 'cpi') \
    .order('date', desc=True) \
    .limit(1) \
    .execute()

latest_cpi = result.data[0]['average']
```

## Direct SQL Queries

For complex analysis, use raw SQL in Supabase's SQL editor:

```sql
-- Monthly CPI changes with percentages
SELECT 
  date,
  average as cpi,
  average - LAG(average) OVER (ORDER BY date) as monthly_change,
  ROUND(((average - LAG(average) OVER (ORDER BY date)) / 
    LAG(average) OVER (ORDER BY date)) * 100, 2) as percent_change
FROM market_data
WHERE data_type = 'cpi'
ORDER BY date DESC
LIMIT 12;
```

## Environment Variables

### Local Development (.env file)
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-key-here
```

### Usage in Code
```javascript
// Vite/React
const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
)

// Next.js
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
)
```

## Real-time Updates

Subscribe to data changes as they happen:

```javascript
const channel = supabase
  .channel('cpi-updates')
  .on('postgres_changes', 
    { 
      event: 'INSERT', 
      schema: 'public', 
      table: 'market_data',
      filter: 'data_type=eq.cpi'
    }, 
    (payload) => {
      console.log('New CPI data:', payload.new)
      // Update your UI here
    }
  )
  .subscribe()

// Clean up when component unmounts
channel.unsubscribe()
```

## Error Handling

Supabase doesn't throw errors - always check the error object:

```javascript
const { data, error } = await supabase
  .from('market_data')
  .select()

if (error) {
  console.error('Query failed:', error)
  return
}

// Safe to use data now
```

## Available Data Types

Current data types in the database:
- `cpi` - Consumer Price Index (updates monthly)

Coming soon:
- `gas_price` - Gas prices
- `unemployment` - Unemployment rate
- `import_index` - Import price index
- `export_index` - Export price index

## Database Schema

```sql
market_data
├── id (bigserial, primary key)
├── date (timestamp)
├── data_type (text) 
├── high (decimal)
├── low (decimal)
├── average (decimal)
└── raw_data (jsonb - original API response)
```

## Rate Limits

Free tier limits (you're nowhere near these):
- 500MB database storage
- 2GB bandwidth/month
- 50,000 requests/month

## Example: Simple React Component

```jsx
import { useEffect, useState } from 'react'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
)

export function CPIDisplay() {
  const [cpi, setCpi] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchCPI() {
      const { data, error } = await supabase
        .from('market_data')
        .select('date, average')
        .eq('data_type', 'cpi')
        .order('date', { ascending: false })
        .limit(1)
        .single()

      if (error) {
        console.error('Failed to fetch CPI:', error)
      } else {
        setCpi(data)
      }
      setLoading(false)
    }

    fetchCPI()
  }, [])

  if (loading) return <div>Loading...</div>
  if (!cpi) return <div>Error loading CPI data</div>

  return (
    <div>
      <h2>Current CPI: {cpi.average}</h2>
      <p>As of: {new Date(cpi.date).toLocaleDateString()}</p>
    </div>
  )
}
```

## Troubleshooting

**Getting null data?**
- Check your environment variables are loaded
- Verify the data_type you're querying exists
- Make sure dates are formatted as 'YYYY-MM-DD'

**Getting 401 errors?**
- Your anon key is wrong
- Check row-level security (RLS) policies in Supabase

**Data seems old?**
- Check GitHub Actions tab - workflow might have failed
- BLS releases new data around the 10th-12th of each month

## Questions?

The database updates automatically via GitHub Actions. If something's broken, check the Actions tab first. If the workflow is green but data isn't showing up, check Supabase logs.
