"""
Contains shortcut functions to map a resource to URLs
"""
import webapp2
from webapp2_extras import routes
import http


def route(base_url, viewset, detail_field='id',
          allowed_list_methods=None, allowed_detail_methods=None):
    """
    Return a routes.PathPrefixRoute (See:)
    https://webapp-improved.appspot.com/guide/routing.html#path-prefix-routes
    mapping a request handler (`viewset`) with a url (`base_url`)

    The `viewset` must:
        - have `get()`, `post()`, `put()`, `delete()` defined
        or
        - extend `viewset.ModelViewSet`

    The `routes.PathPrefixRoute` has two routes:
        - The list view at `base_url`/ with URI: `base_url`-list
        - The detail view at `base_url`/<id> with URL `base_url`-detail

    Optional Parameters:
        - `detail_field`: The name of the field used to identify a resource
        - `allowed_list_methods`: List of HTTP methods allowed for list view.
                Default is [GET, POST]
        - `allowed_detail_methods`: List of HTTP methods allowed for
                detail view. Default is [GET, PUT, DELETE]
    """
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
            methods=allowed_detail_methods or [http.GET, http.PUT, http.DELETE]
        )
    ])
