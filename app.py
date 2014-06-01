#!/usr/bin/python
'''
Let your voice be heard
'''
import bottle
import json
import pickle
from votesmart import votesmart
from bottle.ext import redis as redis_plugin

ONEDAY = 60 * 60 * 24

APIKEY = '243e0b6d69b73e6986243a50e7a68a0c'
votesmart.apikey = APIKEY

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
        rdb.expire(key, ONEDAY)
    else:
        result = pickle.loads(result)
    
    return result


def get_candidate_info(candidates, rdb):
    candidate_list = candidates.split('.')

    keys = [create_key('Address.getOffice', c) for c in candidate_list]

    redis_key = pickle.dumps(keys)

    results = rdb.get(redis_key)

    if not results:
        results = [votesmart.address.getOffice(id) for id in candidate_list]
        rdb.set(redis_key, pickle.dumps(results))
        rdb.expire(redis_key, ONEDAY)
    else:
        results = pickle.loads(results)

    return results


@app.route('/')
def home():
    return 'everything is running'


@app.route('/officials/<category>/<zipcode>')
def officials(category, zipcode, rdb):
    results = get_official_by_zip(zipcode, rdb)

    filter_values = filter_lookup.get(category)

    if not filter_values:
        return

    return json.dumps(filter_results(results, filter_values), default=lambda o: o.__dict__)


@app.route('/candidate/<candidates>')
def candidate(candidates, rdb):
    #candidates is a csv list
    results = get_candidate_info(candidates, rdb)

    return json.dumps(results, default=lambda o: o.__dict__)


# FILTERS
def filter_results(results, filter_values):
    return [i for i in results if i.__dict__.get(filter_values[0]) == filter_values[1]]


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
    return bottle.static_file(
        filename, root='{}/static'.format(conf.get('bottle', 'root_path')))


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
        #server='python_server',
        host='localhost',
        port=8888)
