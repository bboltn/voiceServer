#!/usr/bin/python
'''
Let your voice be heard
'''
import bottle
import json
from votesmart import votesmart
from bottle.ext import redis as redis_plugin

APIKEY = '243e0b6d69b73e6986243a50e7a68a0c'
votesmart.apikey = APIKEY

# setup app
app = application = bottle.Bottle()
app.autojson = True
#bottle.default_app().autojson

# setup plugin
plugin = redis_plugin.RedisPlugin(host='localhost')
app.install(plugin)


def create_key(operation, zipcode):
    return '%s.%s' % (operation, zipcode)


def get_official_by_zip(zipcode, rdb):
    key = create_key('Officials.getByZip', zipcode)
    
    result = rdb.get(key)

    if result:
        return result
    
    result = votesmart.officials.getByZip(zipcode)

    result = json.dumps(result, default=lambda o: o.__dict__)

    rdb.set(key, result)

    return result


@app.route('/officials/<category>/<zipcode>')
def officials(category, zipcode, rdb):
    results = get_official_by_zip(zipcode, rdb)

    filter = filters_funcs.get(category)

    if not filter:
        return

    return filter(results)


# FILTERS
def us_senate_filter(results):
    return results


def us_house_filter(results):
    return results


def state_senate_filter(results):
    return results


def state_house_filter(results):
    return results


def governor_filter(results):
    return results


filters_funcs = {
    'USSenate': us_senate_filter,
    'USHouse': us_house_filter,
    'StateSenate': state_senate_filter,
    'StateHouse': state_house_filter,
    'Governor': governor_filter
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
