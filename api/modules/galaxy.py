from flask import Blueprint, render_template, session, flash, redirect, url_for, request
from modules.db_models import db, Galaxy, Planet, Account
from modules.game import login_required

galaxy_bp = Blueprint('galaxy', __name__, template_folder='../data/html/galaxy')

@galaxy_bp.route('/select-galaxy')
@login_required
def select_galaxy():
    """Allow players to choose a galaxy to play on or navigate to their existing planet."""
    user_id = session.get('user_id')
    galaxies = Galaxy.query.all()
    user_planets = Planet.query.filter_by(owner_id=user_id).all()
    user_planet_map = {planet.galaxy_id: planet for planet in user_planets}
    return render_template('select_galaxy.html', galaxies=galaxies, user_planet_map=user_planet_map)

@galaxy_bp.route('/galaxy/<int:galaxy_id>')
@login_required
def galaxy_overview(galaxy_id):
    """Display a paginated list of positions in the galaxy."""
    page = request.args.get('page', 1, type=int)
    positions_per_page = 50
    galaxy = Galaxy.query.get_or_404(galaxy_id)

    start_position = (page - 1) * positions_per_page + 1
    end_position = start_position + positions_per_page - 1
    all_positions = [f"{i}:{page}:{galaxy_id}" for i in range(start_position, end_position + 1)]

    existing_planets = Planet.query.filter(Planet.galaxy_id == galaxy_id, Planet.position.in_(all_positions)).all()
    planet_map = {planet.position: planet for planet in existing_planets}
    positions = [{"position": pos, "planet": planet_map.get(pos)} for pos in all_positions]

    user_id = session.get('user_id')
    user_planet = Planet.query.filter_by(galaxy_id=galaxy_id, owner_id=user_id).first()

    return render_template('galaxy_overview.html', galaxy=galaxy, positions=positions, page=page, user_planet=user_planet)

