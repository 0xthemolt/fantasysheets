from flask import Blueprint, jsonify, request
from hero_stats.v2_tablegenerator import HeroStatsTable

bp = Blueprint('hero_stats', __name__)
table_generator = HeroStatsTable()

@bp.route('/api/hero-stats')
def get_hero_stats():
    number = request.args.get('number', type=int)
    stat_type = request.args.get('type')
    
    try:
        table_html = table_generator.get_table_html(number, stat_type)
        return jsonify({'html': table_html})
    except Exception as e:
        return jsonify({'error': str(e)}), 500