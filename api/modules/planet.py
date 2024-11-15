from flask import Blueprint, render_template, session, flash, redirect, url_for, request
from modules.db_models import db, Planet, Galaxy
from modules.game import login_required

planet_bp = Blueprint('planet', __name__, template_folder='../data/html/planet')

@planet_bp.route('/galaxy/<int:galaxy_id>/develop/<int:planet_id>', methods=['GET'])
@login_required
def develop_planet(galaxy_id, planet_id):
    """Allow the user to manage their planet development."""
    user_id = session.get('user_id')
    planet = Planet.query.filter_by(id=planet_id, owner_id=user_id, galaxy_id=galaxy_id).first_or_404()
    return render_template('develop_planet.html', planet=planet)

@planet_bp.route('/galaxy/<int:galaxy_id>/migrate/<string:new_position>', methods=['POST'])
@login_required
def migrate_planet(galaxy_id, new_position):
    """Allow the user to migrate their planet to a new position."""
    user_id = session.get('user_id')
    user_planet = Planet.query.filter_by(galaxy_id=galaxy_id, owner_id=user_id).first_or_404()

    existing_planet = Planet.query.filter_by(galaxy_id=galaxy_id, position=new_position).first()
    if existing_planet:
        flash('Position is already occupied.', 'danger')
        return redirect(url_for('galaxy.galaxy_overview', galaxy_id=galaxy_id))

    user_planet.position = new_position
    db.session.commit()

    flash('Planet migrated successfully.', 'success')
    return redirect(url_for('galaxy.galaxy_overview', galaxy_id=galaxy_id))

@planet_bp.route('/galaxy/<int:galaxy_id>/inspect/<int:planet_id>', methods=['GET'])
@login_required
def inspect_planet(galaxy_id, planet_id):
    """Allow the user to inspect another player's planet."""
    planet = Planet.query.filter_by(id=planet_id, galaxy_id=galaxy_id).first_or_404()
    return render_template('inspect_planet.html', planet=planet)

@planet_bp.route('/galaxy/<int:galaxy_id>/colonize/<string:position>', methods=['POST'])
@login_required
def colonize_planet(galaxy_id, position):
    """Allow player to colonize an empty position in the galaxy."""
    user_id = session.get('user_id')
    existing_planet = Planet.query.filter_by(galaxy_id=galaxy_id, position=position).first()

    if existing_planet:
        flash('This position is already occupied.', 'danger')
        return redirect(url_for('galaxy.galaxy_overview', galaxy_id=galaxy_id))

    new_planet = Planet(name=f"Planet {position}", galaxy_id=galaxy_id, position=position, owner_id=user_id)
    db.session.add(new_planet)
    db.session.commit()

    flash(f'You have successfully colonized position {position}.', 'success')
    return redirect(url_for('galaxy.galaxy_overview', galaxy_id=galaxy_id))

