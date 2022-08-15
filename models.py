import array
from flask import Flask
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import func


#I really need a review on this one, I am not sure if this is a good way of seperating models from main
#plus when  I don't initialize all of these here and just import them from app.js I get circular import when
#then import the modules to app.py, SO PLEASE SOME ADVICE WOULD do here
app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)



Shows = db.Table('shows',
    db.Column('id', db.Integer, primary_key = True ),
    db.Column('venue_id', db.Integer, db.ForeignKey('venue_info.id'), nullable = False),
    db.Column('artist_id', db.Integer, db.ForeignKey('artist_info.id'), nullable = False),
    db.Column('start_time',db.DateTime(timezone=True))
)

class Venue(db.Model):
    __tablename__ = 'venue_info'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String(120)))
    image_link = db.Column(db.String(1000))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean,nullable = False,default = False)
    seeking_description = db.Column(db.String(1000))
    website_link = db.Column(db.String(120))

    artists = db.relationship('Artist', secondary=Shows,backref=db.backref('venues', lazy='select'))

    def __repr__(self):
        return f'<Venue {self.id} {self.name} {self.city} {self.state}>'


class Artist(db.Model):
    __tablename__ = 'artist_info'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String(120)))
    image_link = db.Column(db.String(1000))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean,nullable = False,default = False)
    seeking_description = db.Column(db.String(1000))
    website_link = db.Column(db.String(120))

    def __repr__(self):
        return f'<Artist {self.id} {self.name }>'