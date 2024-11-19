from typing import Dict, List
import json
import psycopg2
from psycopg2.extras import RealDictCursor

class HeroStatsTable:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname="0xthemolt",
            user="postgres",
            password="admin",
            host="localhost",
            port="5432"
        )
        self.load_config()

    def load_config(self):
        with open('pages/hero_stats/table_config.json', 'r') as f:
            self.config = json.load(f)

    def get_table_html(self, number: int, stat_type: str) -> str:
        # Get configuration for this table type
        table_config = self.config.get(stat_type, {})
        
        # Get data from database
        data = self.fetch_data(number, stat_type)
        
        # Generate table HTML
        return self.generate_table(data, table_config)

    def fetch_data(self, number: int, stat_type: str) -> List[Dict]:
        query = self.config[stat_type]['query']
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (number,))
            return cur.fetchall()

    def generate_table(self, data: List[Dict], config: Dict) -> str:
        # Generate table HTML based on config and data
        html = """
        <table class="hero-stats-table">
            <thead>
                <tr>
                    {headers}
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        """
        
        # Generate headers and rows based on config
        headers = ''.join([f'<th>{col["display"]}</th>' for col in config['columns']])
        rows = []
        for row in data:
            cols = []
            for col in config['columns']:
                value = row.get(col['field'], '')
                cols.append(f'<td>{value}</td>')
            rows.append(f'<tr>{"".join(cols)}</tr>')
        
        return html.format(headers=headers, rows='\n'.join(rows))