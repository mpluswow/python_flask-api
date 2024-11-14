from flask import Blueprint, render_template, session, flash, redirect, url_for, request
from functools import wraps
from modules.db_models import db, Galaxy, Planet, Account  # Import models

# Create a blueprint for the game module
game_bp = Blueprint('game', __name__, template_folder='../data/html/game')

def login_required(f):
    """Decorator to require login for certain routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You must be logged in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@game_bp.route('/main-menu')
@login_required
def main_menu():
    """Render the main menu page for the game."""
    return render_template('main_menu.html', username=session['username'])

@game_bp.route('/select-galaxy')
@login_required
def select_galaxy():
    """Allow players to choose a galaxy to play on or navigate to their existing planet."""
    user_id = session.get('user_id')

    # Fetch all galaxies with the player count
    galaxies = Galaxy.query.all()

    # Check if the user has a planet in any galaxy
    user_planets = Planet.query.filter_by(owner_id=user_id).all()
    user_planet_map = {planet.galaxy_id: planet for planet in user_planets}

    return render_template('select_galaxy.html', galaxies=galaxies, user_planet_map=user_planet_map)


@game_bp.route('/start-game')
@login_required
def start_game():
    """Redirect player to the galaxy selection page."""
    return redirect(url_for('game.select_galaxy'))


@game_bp.route('/galaxy/<int:galaxy_id>')
@login_required
def galaxy_overview(galaxy_id):
    """Display a paginated list of positions in the galaxy, including empty ones."""
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '').strip()
    positions_per_page = 50

    # Fetch the galaxy
    galaxy = Galaxy.query.get_or_404(galaxy_id)
    highlighted_position = None

    if search_query:
        # Search using "position:page:galaxy_id" format
        try:
            pos, search_page, search_galaxy = map(int, search_query.split(":"))
            if search_galaxy == galaxy_id:
                page = search_page
                highlighted_position = f"{pos}:{page}:{galaxy_id}"
            else:
                flash('No matching galaxy found for the coordinates.', 'danger')
                return redirect(url_for('game.galaxy_overview', galaxy_id=galaxy_id))
        except ValueError:
            # Search by username
            user = Account.query.filter(Account.username.ilike(f"%{search_query}%")).first()
            if user:
                user_planet = Planet.query.filter_by(owner_id=user.id, galaxy_id=galaxy_id).first()
                if user_planet:
                    position_number = int(user_planet.position.split(':')[0])
                    page = (position_number - 1) // positions_per_page + 1
                    highlighted_position = user_planet.position
            else:
                flash('No matching results found.', 'danger')
                return redirect(url_for('game.galaxy_overview', galaxy_id=galaxy_id))

    # Determine start and end position for pagination
    start_position = (page - 1) * positions_per_page + 1
    end_position = start_position + positions_per_page - 1
    all_positions = [f"{i}:{page}:{galaxy_id}" for i in range(start_position, end_position + 1)]

    # Fetch planets in the current range
    existing_planets = Planet.query.filter(Planet.galaxy_id == galaxy_id, Planet.position.in_(all_positions)).all()

    planet_map = {planet.position: planet for planet in existing_planets}
    positions = [{"position": pos, "planet": planet_map.get(pos)} for pos in all_positions]

    user_id = session.get('user_id')
    user_planet = Planet.query.filter_by(galaxy_id=galaxy_id, owner_id=user_id).first()

    return render_template(
        'galaxy_overview.html',
        galaxy=galaxy,
        positions=positions,
        page=page,
        user_planet=user_planet,
        highlighted_position=highlighted_position
    )




@game_bp.route('/galaxy/<int:galaxy_id>/develop/<int:planet_id>', methods=['GET'])
@login_required
def develop_planet(galaxy_id, planet_id):
    """Allow the user to manage their planet development."""
    user_id = session.get('user_id')

    # Ensure the planet belongs to the current user
    planet = Planet.query.filter_by(id=planet_id, owner_id=user_id, galaxy_id=galaxy_id).first_or_404()

    return render_template('develop_planet.html', planet=planet)


@game_bp.route('/galaxy/<int:galaxy_id>/migrate/<string:new_position>', methods=['POST'])
@login_required
def migrate_planet(galaxy_id, new_position):
    """Allow the user to migrate their planet to a new position."""
    user_id = session.get('user_id')
    user_planet = Planet.query.filter_by(galaxy_id=galaxy_id, owner_id=user_id).first_or_404()

    # Check if the new position is empty
    existing_planet = Planet.query.filter_by(galaxy_id=galaxy_id, position=new_position).first()
    if existing_planet:
        flash('Position is already occupied.', 'danger')
        return redirect(url_for('game.galaxy_overview', galaxy_id=galaxy_id))

    # Update the user's planet position
    user_planet.position = new_position
    db.session.commit()

    flash('Planet migrated successfully.', 'success')
    return redirect(url_for('game.galaxy_overview', galaxy_id=galaxy_id))


@game_bp.route('/galaxy/<int:galaxy_id>/inspect/<int:planet_id>', methods=['GET'])
@login_required
def inspect_planet(galaxy_id, planet_id):
    """Allow the user to inspect another player's planet."""
    planet = Planet.query.filter_by(id=planet_id, galaxy_id=galaxy_id).first_or_404()
    return render_template('inspect_planet.html', planet=planet)


@game_bp.route('/galaxy/<int:galaxy_id>/colonize/<string:position>', methods=['POST'])
@login_required
def colonize_planet(galaxy_id, position):
    """Allow player to colonize an empty position in the galaxy if they don't already have one."""
    user_id = session.get('user_id')

    if not user_id:
        flash('You must be logged in to colonize a planet.', 'danger')
        return redirect(url_for('login'))

    # Check if the user already has a planet in this galaxy
    existing_user_planet = Planet.query.filter_by(galaxy_id=galaxy_id, owner_id=user_id).first()
    if existing_user_planet:
        flash('You already have a planet in this galaxy.', 'danger')
        return redirect(url_for('game.galaxy_overview', galaxy_id=galaxy_id))

    # Ensure the position is available
    existing_planet = Planet.query.filter_by(galaxy_id=galaxy_id, position=position).first()
    if existing_planet:
        flash('This position is already occupied.', 'danger')
        return redirect(url_for('game.galaxy_overview', galaxy_id=galaxy_id))

    # Create the new planet for the player
    new_planet = Planet(
        name=f"Planet {position}",
        galaxy_id=galaxy_id,
        position=position,
        owner_id=user_id
    )
    db.session.add(new_planet)

    # Update the galaxy's player count
    galaxy = Galaxy.query.get(galaxy_id)
    galaxy.player_count += 1

    db.session.commit()

    flash(f'You have successfully colonized position {position}.', 'success')
    return redirect(url_for('game.galaxy_overview', galaxy_id=galaxy_id))

