import json
from pages.hero_stats.build_static import TableGenerator

# Generate static HTML files
def generate_static_files():
    table_generator = TableGenerator()
    
    # Load all data at once
    with open('pages/hero_stats/hero_stats.json', 'w') as f:
        json_data = json.dumps(table_generator.fetch_data('default')[0])
        f.write(json_data)
    
    # Generate initial HTML
    with open('index.html', 'w') as f:
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Hero Stats</title>
            <script src="app.js"></script>
        </head>
        <body>
            <div id="table-container"></div>
        </body>
        </html>
        """
        f.write(html_template)

if __name__ == '__main__':
    generate_static_files()