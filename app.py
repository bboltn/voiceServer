#!/usr/bin/python
'''
A basic bottle app skeleton
'''

import bottle

from votesmart import votesmart
votesmart.apikey = '243e0b6d69b73e6986243a50e7a68a0c'
addr = votesmart.address.getOffice(26732)[0]


app = application = bottle.Bottle()

@app.route('/static/<filename:path>')
def static(filename):
    '''
    Serve static files
    '''
    return bottle.static_file(filename, root='{}/static'.format(conf.get('bottle', 'root_path')))

@app.route('/')
def show_index():
    '''
    The front "index" page
    '''
    return 'Hello there ' + addr.street

@app.route('/page/<page_name>')
def show_page(page_name):
    '''
    Return a page that has been rendered using a template
    '''
    return theme('page', name=page_name)

class StripPathMiddleware(object):
    '''
    Get that slash out of the request
    '''
    def __init__(self, a):
        self.a = a
    def __call__(self, e, h):
        e['PATH_INFO'] = e['PATH_INFO'].rstrip('/')
        return self.a(e, h)

if __name__ == '__main__':
    bottle.run(app=StripPathMiddleware(app),
        #server='python_server',
        host='localhost',
        port=8888)
