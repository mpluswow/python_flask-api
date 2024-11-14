from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Existing Account model
class Account(db.Model):
    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    joined = db.Column(db.DateTime, default=db.func.current_timestamp())
    last_login = db.Column(db.DateTime, default=None)
    online = db.Column(db.Boolean, default=False)

# New Galaxy model
class Galaxy(db.Model):
    __tablename__ = 'galaxies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    player_count = db.Column(db.Integer, default=0)

    # Relationship to planets
    planets = db.relationship('Planet', backref='galaxy', lazy=True)

# New Planet model
class Planet(db.Model):
    __tablename__ = 'planets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    galaxy_id = db.Column(db.Integer, db.ForeignKey('galaxies.id'), nullable=False)
    position = db.Column(db.String(20), nullable=False)  # Example: "1:1:1"
    owner_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True)  # Nullable until claimed

    # Relationship to account
    owner = db.relationship('Account', backref='planets', lazy=True)

    # Resource fields
    metal = db.Column(db.Integer, default=0)
    crystal = db.Column(db.Integer, default=0)
    deuterium = db.Column(db.Integer, default=0)

    # Building levels
    metal_mine = db.Column(db.Integer, default=1)
    crystal_mine = db.Column(db.Integer, default=1)
    deuterium_synthesizer = db.Column(db.Integer, default=1)

    # Fleet units
    small_cargo = db.Column(db.Integer, default=0)
    large_cargo = db.Column(db.Integer, default=0)
    light_fighter = db.Column(db.Integer, default=0)

