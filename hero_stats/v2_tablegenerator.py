from typing import Dict, List
import json
import psycopg2
from psycopg2.extras import RealDictCursor

def fetch_data(self, view_type, filters=None):
    # Load the full dataset
    with open('pages/hero_stats/hero_stats.json', 'r') as f:
        data = json.load(f)  # data is now directly an array
    
    # Apply filters if any
    if filters:
        for key, value in filters.items():
            data = [row for row in data if row[key] == value]
    
    # Define columns based on view_type
    # You'll need to define these mappings since they're not in the JSON
    view_columns = {
        'default': [
            {'field': 'tournament_unique_key', 'header': 'Tournament'},
            {'field': 'league', 'header': 'League'},
            {'field': 'hero_handle', 'header': 'Handle'},
            {'field': 'hero_name', 'header': 'Name'},
            {'field': 'post_count', 'header': 'Posts'},
            {'field': 'views', 'header': 'Views'},
            {'field': 'reach', 'header': 'Reach'}
        ]
        # Add more view types as needed
    }
    
    columns = view_columns.get(view_type, view_columns['default'])
    
    # Return only the requested columns
    filtered_data = []
    for row in data:
        filtered_row = {col['field']: row[col['field']] for col in columns}
        filtered_data.append(filtered_row)
    
    return filtered_data, columns