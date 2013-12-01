#!/usr/bin/env python
# coding=utf8

# Author: Paolo Di Prodi
# email: paolo@robomotic.com
# Copyright 2013 Robomotic ltd

#
#This file is part of Google Plus Social Graph.
#
#Google Plus Social Graph is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Google Plus Social Graph is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with Foobar. If not, see <http://www.gnu.org/licenses/>.


__author__ = 'robomotic@google.com (Paolo Di Prodi)'

import json
import random
import string
from apiclient.discovery import build


from flask import Flask, render_template
from flask.ext.bootstrap import Bootstrap
from flask.ext.wtf import Form, TextField, HiddenField, ValidationError,\
                          Required, RecaptchaField
from flask import make_response
from flask import request
from flask import session

import httplib2
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

from simplekv.memory import DictStore
from flaskext.kvsession import KVSessionExtension
from GraphGen import GraphResource

import log
logger = log.setup_custom_logger('root')


APPLICATION_NAME = 'Google+ Social Graph'

app = Flask(__name__, static_folder='reports')
Bootstrap(app)

app.config['BOOTSTRAP_USE_MINIFIED'] = True
app.config['BOOTSTRAP_USE_CDN'] = True
app.config['BOOTSTRAP_JQUERY_VERSION']='None'
app.config['BOOTSTRAP_FONTAWESOME'] = True
app.config['SECRET_KEY'] = 'devkey'
app.config['RECAPTCHA_PUBLIC_KEY'] = '6Lfol9cSAAAAADAkodaYl9wvQCwBMr3qGR_PPHcw'
app.secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits)
                         for x in xrange(32))

logger.debug("Secret key "+app.secret_key)

# See the simplekv documentation for details
store = DictStore()


# This will replace the app's session handling
KVSessionExtension(store, app)


# Update client_secrets.json with your Google API project information.
# Do not change this assignment.
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
SERVICE = build('plus', 'v1')

class SearchForm(Form):
    origin = TextField('Origin', description='Source of the graph.',validators=[Required()], default = 'Nobody')
    destination= TextField('Destination', description='Sink of the graph.',validators=[Required()])
    origin_id = HiddenField('Origin_ID', description='Nope', default = '0')
    destination_id = HiddenField('Destination_ID', description='Nope', default = '0')
    #recaptcha = RecaptchaField('A sample recaptcha field')

    def validate_hidden_field(form, field):
        raise ValidationError('Always wrong')


@app.route('/graph', methods=('GET',))
def graphgen():
    """Generate a graph"""
    credentials = session.get('credentials')
  # Only fetch a list of people for connected users.
    if credentials is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    entries=None
    error=None
    graph_resource=GraphResource()
    url_resource=None
    if request.method=='GET':
        if request.args['oid']:
            if request.args['format']!= None and request.args['format'] is str:
                url_resource=graph_resource.fetch(request.args['oid'], format=request.args['format'], max_age=360)
                response = make_response(url_resource, 200)
                response.headers['Content-Type'] = 'application/json'
                return response
    else:
        logger.debug("Bad request "+request.args)
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
@app.route('/', methods=('GET', 'POST',))
def index():
	"""Initialize a session for the current user, and render index.html."""
	# Create a state token to prevent request forgery.
	# Store it in the session for later validation.
	state = ''.join(random.choice(string.ascii_uppercase + string.digits)
		  for x in xrange(32))
	session['state'] = state
	logger.debug("State token "+state)
	# Set the Client ID, Token State, and Application Name in the HTML while
	# serving it.
	form = SearchForm()
	if form.validate_on_submit():
		return "PASSED"
	return render_template('index.html',form=form,CLIENT_ID=CLIENT_ID,STATE=state,APPLICATION_NAME=APPLICATION_NAME)

@app.route('/connect', methods=['POST'])
def connect():
  """Exchange the one-time authorization code for a token and
  store the token in the session."""
  # Ensure that the request is not a forgery and that the user sending
  # this connect request is the expected user.
  if request.args.get('state', '') != session['state']:
    response = make_response(json.dumps('Invalid state parameter.'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response
  # Normally, the state is a one-time token; however, in this example,
  # we want the user to be able to connect and disconnect
  # without reloading the page.  Thus, for demonstration, we don't
  # implement this best practice.
  # del session['state']

  code = request.data

  try:
    # Upgrade the authorization code into a credentials object
    oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
    oauth_flow.redirect_uri = 'postmessage'
    credentials = oauth_flow.step2_exchange(code)
  except FlowExchangeError:
    response = make_response(
        json.dumps('Failed to upgrade the authorization code.'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response

  # An ID Token is a cryptographically-signed JSON object encoded in base 64.
  # Normally, it is critical that you validate an ID Token before you use it,
  # but since you are communicating directly with Google over an
  # intermediary-free HTTPS channel and using your Client Secret to
  # authenticate yourself to Google, you can be confident that the token you
  # receive really comes from Google and is valid. If your server passes the
  # ID Token to other components of your app, it is extremely important that
  # the other components validate the token before using it.
  gplus_id = credentials.id_token['sub']

  stored_credentials = session.get('credentials')
  stored_gplus_id = session.get('gplus_id')
  if stored_credentials is not None and gplus_id == stored_gplus_id:
    response = make_response(json.dumps('Current user is already connected.'),
                             200)
    response.headers['Content-Type'] = 'application/json'
    return response
  # Store the access token in the session for later use.
  session['credentials'] = credentials
  session['gplus_id'] = gplus_id
  response = make_response(json.dumps('Successfully connected user.', 200))
  response.headers['Content-Type'] = 'application/json'
  return response


@app.route('/disconnect', methods=['POST'])
def disconnect():
  """Revoke current user's token and reset their session."""

  # Only disconnect a connected user.
  credentials = session.get('credentials')
  if credentials is None:
    response = make_response(json.dumps('Current user not connected.'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response

  # Execute HTTP GET request to revoke current token.
  access_token = credentials.access_token
  url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
  h = httplib2.Http()
  result = h.request(url, 'GET')[0]

  if result['status'] == '200':
    # Reset the user's session.
    del session['credentials']
    response = make_response(json.dumps('Successfully disconnected.'), 200)
    response.headers['Content-Type'] = 'application/json'
    return response
  else:
    # For whatever reason, the given token was invalid.
    response = make_response(
        json.dumps('Failed to revoke token for given user.', 400))
    response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/people', methods=['GET'])
def people():
  """Get list of people user has shared with this app."""
  credentials = session.get('credentials')
  # Only fetch a list of people for connected users.
  if credentials is None:
    response = make_response(json.dumps('Current user not connected.'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response
  try:
    # Create a new authorized API client.
    http = httplib2.Http()
    http = credentials.authorize(http)
    # Get a list of people that this user has shared with this app.
    google_request = SERVICE.people().list(userId='me', collection='visible')
    result = google_request.execute(http=http)

    response = make_response(json.dumps(result), 200)
    response.headers['Content-Type'] = 'application/json'
    return response
  except AccessTokenRefreshError:
    response = make_response(json.dumps('Failed to refresh access token.'), 500)
    response.headers['Content-Type'] = 'application/json'
    return response
if '__main__' == __name__:
  app.debug = True
  app.run(host='localhost', port=8080)
