from bottle import route, run, template

@route('/hello/:name')
def index(name='World'):
    return template('<b>Hello {{name}}</b>!', name=name)

@route('/events/:id', method='GET')
def get_event(id):
    return dict(name = 'Event ' + str(id))
    
run(host='localhost', port=8888)
