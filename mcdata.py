"""This is an API for storing myCollar owner data.  Data may be accessed by doing
GET requests to paths like /api/1/av/<key>/.  Access is restricted to IP
addresses owned by Linden Lab.  This allows trusting of the
X-SecondLife-Owner-Key header, which is used to further restrict avatars'
access to their own data and those for whom they are listed as 'owners'.
"""

import os
import logging
import warnings
from functools import wraps

from flask import Flask, Response, abort, request
import mongoengine as mg

from models import Av, Owner
import llip


DEBUG = True if os.environ.get('DEBUG') else False
OWNER_HEADER = 'X-SecondLife-Owner-Key'

if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

try:
    SUPERUSER = os.environ['MCDATA_SUPERUSER']
except KeyError:
    raise SystemExit("You must set the MCDATA_SUPERUSER environment variable.")

# DB stuff.  Here we look a MongoDB connection URI as will be passed in by
# Heroku if you have enabled the MongoLab Addon.  MongoLab offers a free plan
# with 250MB of storage. If that env var isn't set, then fall back to
# MONGODB_URI, then to using a local MongoDB.
db_uri = (os.environ.get('MONGOLAB_URI') 
          or os.environ.get('MONGODB_URI')
          or 'mongodb://localhost/mcdata')
db_name = db_uri.rpartition('/')[-1]

# Connecting using a URI will raise a warning if we don't supply an optional
# username/password.  This is lame, but we can filter the warning out.
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    mg.connect(db_name, host=db_uri)


# Webby stuff
app = Flask(__name__)


def text(txt):
    """Shortcut for returning text/plain"""
    # Was going to return application/x-www-form-urlencoded, but SVC-635 :(
    # That bug's almost old enough to go to kindergarten, LL.  C'mon.
    return Response(txt, mimetype="text/plain")


def inworld(f):
    """Flask view decorator to only allow requests from within SL"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Ensure we have an owner key
        if not OWNER_HEADER in request.headers:
            abort(403)

        # Disable IP checks if debug is turned on.
        # Depending on your proxy situation, you may have to get the remote
        # header from X_FORWARDED_FOR or some other header.
        if not llip.lindenip(request.remote_addr) and not DEBUG:
            abort(403)

        if request.content_type and not request.content_type.startswith('text/plain'):
            msg = ('Content-Type must be text/plain.  Was %s' %
                   request.content_type)
            return msg, 415

        # Parse any data sent in.  Assume it's key=value pairs,
        # newline-delimited.
        if request.data:
            try:
                request.lsldata = dict([x.split('=') for x in
                                        request.data.rstrip().split('\n')])
            except ValueError:
                return 'Could not parse data', 400
        else:
            request.lsldata = {}

        return f(*args, **kwargs)
    return decorated_function


FORBIDDEN_MSG = """Access denied.  You are either accessing from an
unauthorized IP address or did not supply an %(OWNER_HEADER)s header.

If you are running a server for development purposes, you may disable IP
address checks by setting the DEBUG environment variable on the command line,
like this:
$ DEBUG="1" python app.py
""" % globals()

@app.errorhandler(403)
def forbidden(error):
    rv = text(FORBIDDEN_MSG)
    rv.status_code = 403
    return rv


@app.route('/')
def home():
    # A request to the homepage will return the app's docstring, in plain text
    # format.
    return text(__doc__)


@app.route('/api/1/av/<key>/', methods=['GET', 'PUT', 'DELETE'])
@inworld
def av_by_key(key):
    requester = request.headers[OWNER_HEADER]
    try:
        av = Av.objects.get(key=key)
    except Av.DoesNotExist:
        if request.method == 'PUT' and requester==SUPERUSER:
            # Only the superuser may create new records.
            logging.info('Creating new av record for %s' % key)
            av = Av(key=key)
        else:
            # XXX Unauthorized access has to return exactly the same response as
            # an av not existing in the DB.  Otherwise people can make requests to
            # others' urls and use the differing responses to see who has used the
            # service.
            logging.info('Av %s does not exist' % key)
            abort(404)

    # Ensure that this person is allowed to access this data
    if not key == av.key or av.has_owner(requester):
        logging.info('%s denied access to %s' % (requester, av.key))
        abort(404)

    if request.method == 'GET':
        return text(av.to_lsl())
    elif request.method == 'PUT':
        if 'owners' in request.lsldata:
            # owners string will look like avkey,avname,av2key,av2name etc.
            # split it on commas, then zip into tuples of (key,name).  Iterate
            # over those tuples and ensure that there's a record for each one
            # in the DB's owner list.
            vals = request.lsldata['owners'].split(",")
            av.owners = [Owner(**{'key':i[0], 'name':i[1]}) for i in
                         zip(vals[::2], vals[1::2])]

        av.save()
        return text(av.to_lsl())


# The lines below only come into play if you try to run this as a standalone
# program, like "python app.py".  They're not used when the app is run from
# gunicorn.
if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=DEBUG)
