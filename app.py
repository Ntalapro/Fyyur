#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from datetime import date
import sys
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for,abort, jsonify 
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import func
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import pytz

utc=pytz.UTC
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


#I added a non-composite primary-key to this tables coz we sometimes get an artist performing at the same
#venue multiples times, so with  the composite p-key we can't have this.
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
    genres = db.Column(db.String(120))
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
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(1000))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean,nullable = False,default = False)
    seeking_description = db.Column(db.String(1000))
    website_link = db.Column(db.String(120))

    def __repr__(self):
        return f'<Artist {self.id} {self.name }>'
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  artists_ = Artist.query.order_by('id').limit(10)
  venues_ = Venue.query.order_by('id').limit(10)
  return render_template('pages/home.html',artists=artists_,area=venues_)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  #I kinda have no better algorithm for this one, this one can't be well scaled
  data1= db.session.query(Venue).all()
  data =[] 
  venues_=[]

  #Remove duplicte cities
  for i in data1:
    if {"city" : i.city,"state":i.state}  not in data:
      data.append({"city" : i.city,"state":i.state})

  for i in data:
    v = Venue.query.filter_by(city=i['city']).all()
    for j in v:
      venues_.append({
          "id": j.id,
          "name": j.name,
          "num_upcoming_shows": len(db.session.query(Shows).filter(Shows.c.venue_id==j.id , 
                                Shows.c.start_time > utc.localize(datetime.today())).all())
          })
      i["venues"]=venues_
    venues_ = []

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search = Venue.query.filter(Venue.name.ilike("%"+ request.form.get('search_term', '') +"%")).all()
  data=[]
  for i in search:
    data.append({
      "id": i.id,
      "name": i.name,
      "num_upcoming_shows":len(db.session.query(Shows).filter(Shows.c.venue_id==i.id , 
                                Shows.c.start_time > utc.localize(datetime.today())).all()),
    })
  response={
    "count": len(search),
  }
  response["data"]=data
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  
  venue = Venue.query.filter_by(id=venue_id).first()
  output = venue.__dict__
  genres = list(output['genres'])
  output_genres_to_list = (((''.join(genres)).removeprefix('{')).removesuffix('}')).split(',')
  output['genres'] = output_genres_to_list 

  output_pastshows_list=[]
  output_futureshows_list=[]
  past_shows = db.session.query(Shows).filter(Shows.c.venue_id==venue_id , Shows.c.start_time < utc.localize(datetime.today())).all()
  for i in past_shows:
      output_pastshows_list.append({
        "artist_id":i.artist_id ,
        "artist_name": Artist.query.get(i.artist_id).name,
        "artist_image_link": Artist.query.get(i.artist_id).image_link,
        "start_time": i.start_time.strftime("%Y/%m/%d"+"T"+ "%H:%M:%S"+"Z")
      })
  future_shows = db.session.query(Shows).filter(Shows.c.venue_id==venue_id , Shows.c.start_time > utc.localize(datetime.today())).all()
  for i in future_shows:
      output_futureshows_list.append({
        "artist_id":i.artist_id ,
        "artist_name": Artist.query.get(i.artist_id).name,
        "artist_image_link": Artist.query.get(i.artist_id).image_link,
        "start_time": i.start_time.strftime("%Y/%m/%d"+"T"+ "%H:%M:%S"+"Z")
      })

  past_shows_count = len(output_pastshows_list)
  upcoming_shows_count = len(output_futureshows_list)

  return render_template('pages/show_venue.html', venue=output,past_shows =output_pastshows_list,
                                upcoming_shows=output_futureshows_list,
                        past_shows_count = past_shows_count,upcoming_shows_count=upcoming_shows_count)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['GET','POST'])
def create_venue_submission():
  form = VenueForm()
  if form.validate_on_submit():
        venue = Venue.query.filter_by(address=form.address.data).first() # only address is unique if u think about it
        if venue is None:
            try:
              venue = Venue(name=form.name.data,city=form.city.data,state = form.state.data,address=form.address.data,
                            phone=form.phone.data,genres = form.genres.data,image_link = form.image_link.data,facebook_link = form.facebook_link.data,
                            website_link  = form.website_link.data,seeking_talent=form.seeking_talent.data,seeking_description = form.seeking_description.data)
              db.session.add(venue)  
              db.session.commit()
              flash('Venue ' + request.form['name'] + ' was successfully listed!')
            except:
                db.session.rollback()
                #flash(sys.exc_info())
                flash('An error occurred. '+ request.form['name'] +' Venue could not be listed.')
                return render_template('forms/new_venue.html',form=form)
            finally:
                db.session.close() 
        else:
            flash('venue exists')
            return render_template('forms/new_venue.html',form = form)
  else:
      flash('Form not validated')
      return render_template('forms/new_venue.html',form=form)
  return render_template('pages/home.html')

  

@app.route('/venues/<venue_id>/delete', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error = False
  try:
        #Todo.query.filter_by(id=todo_id).delete()
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
  except:
        db.session.rollback()
        error = True
  finally:
        db.session.close()
  if error:
        abort(500)
  else:
        return jsonify({'success': True})  

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  all_artists =  Artist.query.order_by('id').all()
  return render_template('pages/artists.html', artists=all_artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search = Artist.query.filter(Artist.name.ilike("%"+ request.form.get('search_term', '') +"%")).all()
  data=[]
  for i in search:
    data.append({
      "id": i.id,
      "name": i.name,
      "num_upcoming_shows":len(db.session.query(Shows).filter(Shows.c.artist_id==i.id , 
                                Shows.c.start_time > utc.localize(datetime.today())).all()),
    })
  response={
    "count": len(search),
  }
  response["data"]=data
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.filter_by(id=artist_id).first()
  output = artist.__dict__
  genres = list(output['genres'])
  output_genres_to_list = (((''.join(genres)).removeprefix('{')).removesuffix('}')).split(',')
  output['genres'] = output_genres_to_list 

  
  output_pastshows_list=[]
  output_futureshows_list=[]
  past_shows = db.session.query(Shows).filter(Shows.c.artist_id==artist_id , Shows.c.start_time < utc.localize(datetime.today())).all()
  for i in past_shows:
      output_pastshows_list.append({
        "venue_id":i.venue_id ,
        "venue_name": Venue.query.get(i.venue_id).name,
        "venue_image_link": Venue.query.get(i.venue_id).image_link,
        "start_time": i.start_time.strftime("%Y/%m/%d"+"T"+ "%H:%M:%S"+"Z")
      })
  fucture_shows = db.session.query(Shows).filter(Shows.c.artist_id==artist_id , Shows.c.start_time > utc.localize(datetime.today())).all()
  for i in fucture_shows:
      output_futureshows_list.append({
        "venue_id":i.venue_id ,
        "venue_name": Venue.query.get(i.venue_id).name,
        "venue_image_link": Venue.query.get(i.venue_id).image_link,
        "start_time": i.start_time.strftime("%Y/%m/%d"+"T"+ "%H:%M:%S"+"Z")
      })    

  past_shows_count = len(output_pastshows_list)
  upcoming_shows_count = len(output_futureshows_list)

  return render_template('pages/show_artist.html', artist=output,past_shows =output_pastshows_list,
                        upcoming_shows=output_futureshows_list,
                        past_shows_count = past_shows_count,upcoming_shows_count=upcoming_shows_count)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist= Artist.query.get(artist_id)
  form = ArtistForm(formdata=request.form,obj=artist)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  record_to_update = Artist.query.get(artist_id)
  if request.method == 'POST' :
      form = ArtistForm(formdata = request.form, obj = record_to_update )
      form.populate_obj(record_to_update)
      try:
        db.session.commit()
        flash('updated')
      except:
        db.session.rollback
        flash('could not updated Artist')
      finally:
        db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):  

  venue= Venue.query.get(venue_id)
  form = VenueForm(formdata = request.form, obj = venue)
  
  return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  record_to_update = Venue.query.get(venue_id)
  if request.method == 'POST' :
      form = VenueForm(formdata = request.form, obj = record_to_update )
      form.populate_obj(record_to_update)
      try:
        db.session.commit()
        flash('updated')
      except:
        db.session.rollback
        flash('could not updated Venue')
      finally:
        db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm()
  if form.validate_on_submit():
        artist = Artist.query.filter_by(name=form.name.data).first()
        if artist is None:
            try:
              artist = Artist(name=form.name.data,city=form.city.data,state = form.state.data,phone=form.phone.data,
                            genres = form.genres.data,image_link = form.image_link.data,facebook_link = form.facebook_link.data,
                            website_link  = form.website_link.data,seeking_venue=form.seeking_venue.data,
                            seeking_description = form.seeking_description.data)
              db.session.add(artist)
              db.session.commit()
              flash('Artist ' + request.form['name'] + ' was successfully listed!')
            except:
                db.session.rollback()
                flash('An error occurred. '+ request.form['name'] +' Artist could not be listed.')
                return render_template('forms/new_artist.html',form=form) 
            finally:
                db.session.close() 
        else:
            flash('artist exists')
            return render_template('forms/new_artist.html',form = form)
  return render_template('pages/home.html')  

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows_= db.session.query(Shows).all()
  output_shows_list = []
  for i in shows_:
      output_shows_list.append({
        "venue_id":i.venue_id ,
        "venue_name": Venue.query.get(i.venue_id).name,
        "artist_id":i.artist_id,
        "artist_name": Artist.query.get(i.artist_id).name,
        "artist_image_link": Artist.query.get(i.artist_id).image_link,
        "start_time": i.start_time.strftime("%Y/%m/%d"+"T"+ "%H:%M:%S"+"Z")
      })
  return render_template('pages/shows.html', shows=output_shows_list)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm()
  if form.validate_on_submit():
      try:
          venue_dont_exist = Venue.query.filter_by(id=form.venue_id.data).first()
          artist_dont_exist = Venue.query.filter_by(id=form.venue_id.data).first()

          if venue_dont_exist is not None and artist_dont_exist is not None:
              new_show = Shows.insert().values(
                    artist_id = form.artist_id.data,
                    venue_id = form.venue_id.data ,
                    start_time = form.start_time.data
                    )
              db.session.execute(new_show)
              db.session.commit()
              flash('Show was successfully listed!')
          else:
            flash('ID(s) do exist, check artist page')
            return render_template('forms/new_show.html',form = form)
      except: 
          db.session.rollback()   
          flash('An error occurred. Show could not be listed.')
          return render_template('forms/new_show.html',form = form)
      finally:
          db.session.close() 
              
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
'''
if __name__ == '__main__':
#    app.run()
'''

# Or specify port manually:

if __name__ == '__main__':
    app.debug = True
    app.run(host='10.0.2.15', port=3000)

