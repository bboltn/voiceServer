#!/usr/bin/python
'''
Let your voice be heard
'''
import bottle
import json
import pickle
import urllib
import requests
import os.path

from bs4 import BeautifulSoup

from votesmart import votesmart
from bottle.ext import redis as redis_plugin

# CONSTANTS
TIME_TO_EXPIRE = 60 * 60 * 24
VOTE_SMART_API_KEY = '243e0b6d69b73e6986243a50e7a68a0c'

# API Setup
votesmart.apikey = VOTE_SMART_API_KEY

# setup app
app = application = bottle.Bottle()
app.autojson = True


# setup plugin
plugin = redis_plugin.RedisPlugin(host='localhost')
app.install(plugin)


def create_key(operation, zipcode):
    return '%s.%s' % (operation, zipcode)


def get_official_by_zip(zipcode, rdb):
    key = create_key('Officials.getByZip', zipcode)

    result = rdb.get(key)

    if not result:
        result = votesmart.officials.getByZip(zipcode)
        rdb.set(key, pickle.dumps(result))
        rdb.expire(key, TIME_TO_EXPIRE)
    else:
        result = pickle.loads(result)

    return result


def get_candidate_info(candidates, rdb):
    candidate_list = candidates.split('.')

    keys = [create_key('Address.getOffice', c) for c in candidate_list]

    redis_key = pickle.dumps(keys)

    results = rdb.get(redis_key)

    if not results:
        results = []
        for id in candidate_list:
            candidate = votesmart.address.getOffice(id)
            for c in candidate:
                setattr(c, 'imageurl',
                        'http://api.kashew.net/static/%s.jpg' % id)
                setattr(c, 'candidateId', id)
                download_image(id)
            results.append(candidate)

        rdb.set(redis_key, pickle.dumps(results))
        rdb.expire(redis_key, TIME_TO_EXPIRE)
    else:
        results = pickle.loads(results)

    return results

def get_locals_by_zip(zipcode, rdb):
    key = 'get_locals_by_zip.%s' % zipcode
    results = rdb.get(key)
    if not results:
        google_url = 'http://maps.googleapis.com/maps/api/geocode/json?address=%s' % zipcode
        result = requests.get(google_url)
        city_name = ''
        state_id = ''

        results = result.json().get('results')
        if not isinstance(results, list):
            return

        address_components = results[0].get('address_components')
        for a in address_components:
            if not a['short_name'] or not a['types']:
                continue
            if 'locality' in a['types']:
                city_name = a['short_name']
            if 'administrative_area_level_1' in a['types']:
                state_id = a['short_name']
            if city_name and state_id:
                break

        if not city_name or not state_id:
            return

        print 'info!!!!!!!'
        print state_id
        print city_name
        cities = votesmart.local.getCities(state_id)
        locality = filter(lambda local: local.name == city_name, cities)
        if not locality:
            geonames_url = 'http://www.geonames.org/search.html?q=%s&country=US' % zipcode
            print geonames_url
            result = requests.get(geonames_url)
            county_name = get_county_name(result.text)
            if not county_name:
                county_name = get_county_name(result.text, True)
                if not county_name:
                    return

            print 'county_name' + county_name

            counties = votesmart.local.getCounties(state_id)
            if not counties:
                print 'no counties'
                return

            locality = filter(lambda local: local.name == county_name, counties)

            if not locality:
                locality = filter(lambda local: county_name in local.name, counties)

        print locality
        if not isinstance(locality, list):
            print 'no locality'
            return

        localId = locality[0].localId
        print localId

        if not localId:
            return

        results = votesmart.local.getOfficials(localId)
        for r in results:
            setattr(r, 'imageurl', 'http://api.kashew.net/static/%s.jpg' % r.candidateId)
            download_image(r.candidateId)

        rdb.set(key, pickle.dumps(results))
        rdb.expire(key, TIME_TO_EXPIRE)
    else:
        results = pickle.loads(results)

    return results

def get_county_name(entries, shortest=False):
    soup = BeautifulSoup(entries)
    smalls = soup("small")
    potentials = []
    for s in smalls:
        if s.string and 'county' in s.string.lower():
            potentials.append(s.string)

    if shortest:
        return min(potentials, key=len)
    elif isinstance(potentials, list):
        potentials[0]
    else:
        return

def download_image(id):
    file_location = 'static/%s.jpg' % id
    if os.path.isfile(file_location):
        return

    image_url = 'http://votesmart.org/canphoto/%s.jpg' % id
    urllib.urlretrieve(image_url, "%s/%s.jpg" % ('static', id))


#ROUTES
@app.route('/')
def home():
    return 'everything is running'


@app.route('/officials/Local/<zipcode>')
def officials_local(zipcode, rdb):
    results = get_locals_by_zip(zipcode, rdb)
    return json.dumps(results, default=lambda o: o.__dict__)


@app.route('/officials/<category>/<zipcode>')
def officials(category, zipcode, rdb):
    results = get_official_by_zip(zipcode, rdb)

    filter_values = filter_lookup.get(category)

    if not filter_values:
        return

    filtered_results = filter_results(results, filter_values)

    for c in filtered_results:
        download_image(c.candidateId)
        setattr(c, 'imageurl', 'http://api.kashew.net/static/%s.jpg' % c.candidateId)

    return json.dumps(filtered_results, default=lambda o: o.__dict__)


@app.route('/candidate/<candidates>')
def candidate(candidates, rdb):
    # candidates is a list of candidate ids seperated by a period.  
    # Example: 7826.7790
    results = get_candidate_info(candidates, rdb)

    return json.dumps(results, default=lambda o: o.__dict__)


# FILTERS
def filter_results(results, filter_values):
    return [i for i in results
        if i.__dict__.get(filter_values[0]) == filter_values[1]]


filter_lookup = {
    'USSenate': ['officeName', 'U.S. Senate'],
    'USHouse': ['officeName', 'U.S. House'],
    'StateSenate': ['officeName', 'State Senate'],
    'StateHouse': ['officeName', 'State House'],
    'Governor': ['officeTypeId', 'G']
}


# SERVE UP STATIC DATA
@app.route('/static/<filename:path>')
def static(filename):
    '''
    Serve static files
    '''
    return bottle.static_file(filename, root='static')


# HELPERS
class StripPathMiddleware(object):
    '''
    Get that slash out of the request
    '''
    def __init__(self, a):
        self.a = a
    def __call__(self, e, h):
        e['PATH_INFO'] = e['PATH_INFO'].rstrip('/')
        return self.a(e, h)


# SERVER START
if __name__ == '__main__':
    bottle.run(app=StripPathMiddleware(app),
        host='localhost',
        port=8888)
