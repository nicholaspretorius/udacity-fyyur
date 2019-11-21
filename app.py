# ---------------------------------------------------------------------------- #
# Imports
# ---------------------------------------------------------------------------- #
# import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from sqlalchemy.dialects.postgresql import ARRAY
import logging
from logging import Formatter, FileHandler
from forms import ArtistForm, ShowForm, VenueForm
from flask_migrate import Migrate
import sys
from datetime import datetime
# ---------------------------------------------------------------------------- #
# App Config.
# ---------------------------------------------------------------------------- #

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

# ---------------------------------------------------------------------------- #
# Models.
# ---------------------------------------------------------------------------- #


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    shows = db.relationship('Show', backref='venue', lazy=True)
    website = db.Column(db.String)
    genres = db.Column(ARRAY(db.String(120)))
    seeking_talent = db.Column(db.Boolean, nullable=True, default=False)
    seeking_description = db.Column(db.String)

    def __repr__(self):
        return f'<Venue id: {self.id}, name: {self.name}, city: {self.city}, state: {self.state}, shows: {self.shows}>'

    # TODO: implement any missing fields, as a database migration using Flask-Migrate


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(ARRAY(db.String(120)))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String)
    seeking_venue = db.Column(db.Boolean, nullable=True, default=False)
    seeking_description = db.Column(db.String)

    def __repr__(self):
        return f'''<Artist id: {self.id}, name: {self.name} city: {self.city} state: {self.state} phone: {self.phone} genres: {self.genres} image_link: {self.image_link}
        fb: {self.facebook_link} website: {self.website} s_venue: {self.seeking_venue} s_desc: {self.seeking_description}>'''

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.


show_items = db.Table(
    'show_items',
    db.Column('show_id', db.Integer, db.ForeignKey(
        'Show.id'), primary_key=True),
    db.Column('artist_id', db.Integer, db.ForeignKey(
        'Artist.id'), primary_key=True)
)


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    date_time = db.Column(db.DateTime, nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    artists = db.relationship(
        'Artist', secondary=show_items, backref=db.backref('shows', lazy=True))

    def __repr__(self):
        return f'<Show id: {self.id}, venue_id: {self.venue_id}, datetime: {self.date_time} artists: {self.artists}>'

# ---------------------------------------------------------------------------- #
# Filters.
# ---------------------------------------------------------------------------- #


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

# ---------------------------------------------------------------------------- #
# Controllers.
# ---------------------------------------------------------------------------- #


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    city_venues = []
    city_data = Venue.query.with_entities(
        Venue.city, Venue.state).group_by('city', 'state').all()
    venue_data = Venue.query.all()

    for c in city_data:
        venues = []
        for v in venue_data:
            if v.city == c.city:
                venues.append({'id': v.id, 'name': v.name, 'num_upcoming_shows': 0})
            city = {'city': c.city, 'state': c.state, 'venues': venues}
        city_venues.append(city)

    return render_template('pages/venues.html', areas=city_venues)


@app.route('/venues/search', methods=['POST'])
def search_venues():

    term = request.form.get('search_term')
    search = "%{}%".format(term.lower())
    res = Venue.query.filter(or_(Venue.name.ilike(search), Venue.state.ilike(search), Venue.city.ilike(search))).\
        all()
    response = {'count': len(res), 'data': res}

    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)

    past_shows = []
    upcoming_shows = []
    today = datetime.now()

    if hasattr(venue, 'shows'):
        for show in venue.shows:
            artists = db.session.query(show_items, Artist).with_entities(Artist.id, Artist.name, Artist.image_link).\
                filter(show.id == show_items.c.show_id).\
                filter(show_items.c.artist_id == Artist.id).\
                all()

            value_list = [(x.id, x.name, x.image_link) for x in artists]
            for v in value_list:
                artist = {"artist_id": v[0], "artist_name": v[1], "artist_image_link": v[2], "start_time": str(show.date_time)}

                if(show.date_time >= today):
                    upcoming_shows.append(artist)
                else:
                    past_shows.append(artist)

        venue.past_shows = past_shows
        venue.past_shows_count = len(past_shows)
        venue.upcoming_shows = upcoming_shows
        venue.upcoming_shows_count = len(upcoming_shows)

    return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    form = VenueForm()
    try:
        if form.validate_on_submit():
            venue = Venue(name=form.name.data, city=form.city.data, state=form.state.data, address=form.address.data, phone=form.phone.data, image_link='',
                          facebook_link=form.facebook_link.data, genres=form.genres.data, website=form.website.data, seeking_talent=form.seeking_talent.data,
                          seeking_description=form.seeking_description.data)
            db.session.add(venue)
            db.session.commit()
            flash('Venue {} was successfully listed!'.format(form.name.data))
            return redirect(url_for('index'))
        flash('An error occurred. Venue {} could not be listed. {}'.format(
            form.name.data, form.errors))
    except():
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(500)
        flash('There was an error, please try again.')

    return render_template('forms/new_venue.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    error = False
    try:
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
        flash('Venue was successfully deleted.')
    except():
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return jsonify({'success': True})

    return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    artists = Artist.query.order_by('name').all()
    return render_template('pages/artists.html', artists=artists)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    term = request.form.get('search_term')
    search = "%{}%".format(term.lower())
    res = Artist.query.filter(Artist.name.ilike(search)).all()
    response = {'count': len(res), 'data': res}
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    data = Artist.query.get(artist_id)

    past_shows = []
    upcoming_shows = []
    today = datetime.now()

    if hasattr(data, 'shows'):
        for show in data.shows:
            venues = db.session.query(Venue).with_entities(Venue.id, Venue.name, Venue.image_link).\
                filter(show.venue_id == Venue.id).\
                all()

            value_list = [(x.id, x.name, x.image_link) for x in venues]
            for v in value_list:
                venue = {"venue_id": v[0], "venue_name": v[1], "venue_image_link": v[2], "start_time": str(show.date_time)}

                if(show.date_time >= today):
                    upcoming_shows.append(venue)
                else:
                    past_shows.append(venue)

        data.past_shows = past_shows
        data.past_shows_count = len(past_shows)
        data.upcoming_shows = upcoming_shows
        data.upcoming_shows_count = len(upcoming_shows)

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    data = Artist.query.get(artist_id)
    form = ArtistForm(obj=data)
    return render_template('forms/edit_artist.html', form=form, artist=data)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    error = False
    artist = Artist.query.get(artist_id)
    form = ArtistForm()
    try:
        if form.validate_on_submit():
            form.populate_obj(artist)
            db.session.add(artist)
            db.session.commit()
            flash('Artist {} was successfully updated!'.format(form.name.data))
            return redirect(url_for('show_artist', artist_id=artist_id))
        flash('An error occurred. Artist {} could not be listed. {}'.format(
            form.name.data, form.errors))
    except():
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(500)
        flash('There was an error, please try again.')
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
    error = False
    try:
        Artist.query.filter_by(id=artist_id).delete()
        db.session.commit()
        flash('Artist was successfully deleted.')
    except():
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return jsonify({'success': True})

    return None


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    data = Venue.query.get(venue_id)
    form = VenueForm(obj=data)
    return render_template('forms/edit_venue.html', form=form, venue=data)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    error = False
    venue = Venue.query.get(venue_id)
    form = VenueForm()
    try:
        if form.validate_on_submit():
            form.populate_obj(venue)
            db.session.add(venue)
            db.session.commit()
            flash('Venue {} was successfully updated!'.format(form.name.data))
            return redirect(url_for('show_venue', venue_id=venue_id))
        flash('An error occurred. Venue {} could not be listed. {}'.format(
            form.name.data, form.errors))
    except():
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(500)
        flash('There was an error, please try again.')
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False
    form = ArtistForm()
    try:
        if form.validate_on_submit():
            if form.seeking_venue.data == 'True':
                seeking = True
            else:
                seeking = False
            artist = Artist(name=form.name.data, city=form.city.data, state=form.state.data,
                            phone=form.phone.data, image_link='', facebook_link=form.facebook_link.data, genres=form.genres.data, website=form.website.data,
                            seeking_venue=seeking, seeking_description=form.seeking_description.data)
            db.session.add(artist)
            db.session.commit()
            flash('Artist {} was successfully listed!'.format(form.name.data))
            return redirect(url_for('index'))
        flash('An error occurred. Artist {} could not be listed. {}'.format(
            form.name.data, form.errors))
    except():
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(500)
        flash('There was an error, please try again.')
    return render_template('forms/new_artist.html', form=form)


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    shows = db.session.query(Show, Venue, show_items, Artist).\
        filter(Show.venue_id == Venue.id).\
        filter(Show.id == show_items.c.show_id).\
        filter(show_items.c.artist_id == Artist.id).\
        order_by(Show.date_time).\
        all()
    past_venue_shows = []
    upcoming_venue_shows = []
    today = datetime.now()

    for show in shows:
        venue_show = {
            "venue_id": show.Venue.id,
            "venue_name": show.Venue.name,
            "artist_id": show.Artist.id,
            "artist_name": show.Artist.name,
            "artist_image_link": show.Artist.image_link,
            "start_time": str(show.Show.date_time)
        }

        if show.Show.date_time > today:
            upcoming_venue_shows.append(venue_show)
        else:
            past_venue_shows.append(venue_show)

    reverse_past_venue_shows = sorted(past_venue_shows, key=lambda x: datetime.strptime(x['start_time'], '%Y-%m-%d %H:%M:%S'), reverse=True)

    return render_template('pages/shows.html', upcoming_shows=upcoming_venue_shows, upcoming_count=len(upcoming_venue_shows),
                           past_shows=reverse_past_venue_shows, past_count=len(past_venue_shows))


@app.route('/shows/create')
def create_shows():
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error = False
    form = ShowForm()
    try:
        if form.validate_on_submit():
            v_id = int(form.venue_id.data)
            show = Show(date_time=form.start_time.data, venue_id=v_id)
            db.session.add(show)
            db.session.commit()
            artist = Artist.query.get(form.artist_id.data)
            venue = Venue.query.get(v_id)
            show.artists.append(artist)
            venue.shows.append(show)
            db.session.add(venue)
            db.session.commit()
            flash('Show was successfully listed on {}!'.format(form.start_time.data))
            return redirect(url_for('index'))
        flash('An error occurred. Show could not be listed. {}'.format(form.errors))
    except():
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(500)
        flash('There was an error, please try again.')

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
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ---------------------------------------------------------------------------- #
# Launch.
# ---------------------------------------------------------------------------- #

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
