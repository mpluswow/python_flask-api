from flask import Blueprint, render_template, session, flash, redirect, url_for, request
from functools import wraps
from modules.db_models import db, Galaxy, Planet, Account

game_bp = Blueprint('game', __name__, template_folder='../data/html/game')

def login_required(f):
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
    return render_template('main_menu.html', username=session['username'])

@game_bp.route('/start-game')
@login_required
def start_game():
    return redirect(url_for('galaxy.select_galaxy'))

