import webapp2
from webapp2_extras import routes
import http

def route(base_url, viewset, detail_field='id',
	      allowed_list_methods=None, allowed_detail_methods=None):
	return routes.PathPrefixRoute(base_url, [
		webapp2.Route(
			'/',
			handler=viewset,
			name='{resource}-list'.format(resource=base_url),
			methods=allowed_list_methods or [http.GET, http.POST],
		),
		webapp2.Route(
			'/<{detail_field}:\d+>'.format(detail_field=detail_field),
			handler=viewset,
			name='{resource}-detail'.format(resource=base_url),
			methods=allowed_detail_methods or [http.GET, http.PUT, http.DELETE],
		)
	])
