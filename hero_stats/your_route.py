from flask import Flask, render_template, jsonify
from hero_stats.v2_tablegenerator import TableGenerator
from v2_sheets import generate_nav_template

app = Flask(__name__)

@app.route('/')
def index():
    # Generate the initial page with empty table
    html = generate_nav_template(table_html="")
    return html

@app.route('/api/hero-stats')
def get_hero_stats():
    # Get query parameters
    number = request.args.get('number')
    stat_type = request.args.get('type')
    
    # Generate table HTML
    table_generator = TableGenerator()
    table_html = table_generator.fetch_data('default')
    
    # Return JSON response
    return jsonify({
        'html': table_html
    })

if __name__ == '__main__':
    app.run(debug=True)