from flask import Blueprint, render_template, session, flash, redirect, url_for
from functools import wraps

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

