import webapp2
from webapp2_extras import routes
from routers import route


app = webapp2.WSGIApplication([
    webapp2.Route('/', handler='pulsar.home_page_handler', name='home'),
    routes.PathPrefixRoute('/items', [
        webapp2.Route('/', handler='items.views.ItemListHandler', name='items-list'),
        webapp2.Route('<id:\d+>', handler='items.views.ItemHandler', name='items-detail'),
    ])
], debug=True)


def home_page_handler(request, *args, **kwargs):
    return webapp2.Response('Hello, world!')


if __name__ == '__main__':
    run_wsgi_app(app)
