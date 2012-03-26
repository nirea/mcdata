import os
import unittest
import string
import random

from models import Av, Owner

# To run these tests, 'pip install nose' and then run 'nosetests'

random_chars = lambda x: ''.join([random.choice(string.letters) for y in xrange(x)])

# set uri for testing DB before importing main app
os.environ['MONGODB_URI'] = 'mongodb://localhost/mctest'
os.environ['MCDATA_SUPERUSER'] = random_chars(20)
import mcdata

# An IP address that belongs to LL, for testing the IP filtering.
VALID_IP = '8.2.32.1'


def test_unauthorized_ip():
    # If we make a request without setting the IP to a whitelisted one, then we
    # should get rebuffed
    client = mcdata.app.test_client()
    environ = {'REMOTE_ADDR': '192.168.1.1'} 
    res = client.get('/api/1/av/123/', environ_overrides=environ)
    assert res.status_code == 403


def test_missing_sl_owner():
    # We *always* require an X-SecondLife-Owner-Key header
    client = mcdata.app.test_client()
    # Provide an ll-owned IP address.
    environ = {'REMOTE_ADDR': VALID_IP} 
    res = client.get('/api/1/av/123/', environ_overrides=environ)
    assert res.status_code == 403


class MCBaseTestCase(unittest.TestCase):
    """TestCase class that provides a random av key and methods for making
    Flask requests that look like they're coming from that av's inworld
    objects
    """

    def setUp(self):
        self.client = mcdata.app.test_client()
        self.key = random_chars(20) # Av key of object making request
        self.url = '/api/1/av/%s/' % self.key

    def open(self, path, **kwargs):
        """Wraps test client's get() method to set the IP to an allowed LL one,
        and also set the X-SecondLife-Owner header"""
        kwargs['environ_overrides'] = {'REMOTE_ADDR': VALID_IP}
        kwargs['headers'] = {
            'X-SecondLife-Owner-Key': self.key,
        }
        # default content type for llHTTPRequest
        kwargs['content_type'] = 'text/plain;charset=utf-8'
        return self.client.open(path, **kwargs)

    def get(self, path, **kwargs):
        kwargs['method'] = 'GET'
        return self.open(path, **kwargs)

    def put(self, path, data, **kwargs):
        kwargs['method'] = 'PUT'
        return self.open(path, data=data, **kwargs)


class SuperuserTestCase(MCBaseTestCase):
    # For requests that come from the app superuser's objects.
    def setUp(self):
        self.client = mcdata.app.test_client()
        self.key = mcdata.SUPERUSER

    def test_create_user(self):
        # superuser should be able to create new user
        new = random_chars(20)
        url = '/api/1/av/%s/' % new 
        res = self.put(url, 'owners=foo,bar')
        assert res.status_code == 200

        av = Av.objects.get(key=new)
        assert len(av.owners) == 1
        owner = av.owners[0]

        assert owner.key == 'foo'
        assert owner.name == 'bar'


class MCDataTestCase(MCBaseTestCase):
    # For requests that come from regular people.

    def test_good_get(self):
        # existing user should be able to get own data
        av = Av(key=self.key)
        av.save()
        res = self.get(self.url)
        assert res.status_code == 200

        # The first line of responses should have "MCDATA", followed by a
        # space, followed by the key of the av whose data was just fetched.
        assert res.data.split('\n')[0] == 'MCDATA ' + self.key 

    def test_unsubscribed_put(self):
        # non-existent user should not be able to save data
        res = self.put(self.url, 'owners=foo,bar')
        assert Av.objects(key=self.key).count() == 0
        assert res.status_code == 404

    def test_bad_create_user(self):
        # non-superuser should not be able to create new user
        regular_joe = Av(key=self.key)
        regular_joe.save()

        other_key = random_chars(20)
        url = '/api/1/av/%s/' % other_key
        res = self.put(url, 'owners=foo,bar')
        assert res.status_code == 404

    def test_put_bad_data(self):
        # invalid request.data should get a 400 response 
        av = Av(key=self.key)
        av.save()
        # Good data would be newline delimited key=val pairs.  Form-encoded
        # data is invalid.
        bad_data = 'owners=foo,bar&favcolor=blue'
        res = self.put(self.url, bad_data)
        assert res.status_code == 400

    def test_own_owner_save_data(self):
        # I saw a bug where someone couldn't edit data because they were in
        # their own owner list and I had misjudged the order of evaluation for
        # a 'not' and an 'or' in the same expression.  This test would fail if
        # that bug were still around.

        # Make an av with himself in owner list
        av = Av(
            key=self.key,
            owners=[Owner(key=self.key, name=self.key)]
        )
        av.save()

        # Now try to PUT new data
        new_owners = [av.key, av.key, random_chars(10), random_chars(10)]
        new_data = 'owners=%s' % new_owners
        res = self.put(self.url, new_data)
        assert res.status_code == 200



def tearDown():
    # delete mctest db
    from pymongo import Connection
    Connection().drop_database('mctest')
