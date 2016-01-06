"""
Viewsets club together list and detail views
providing a clean way of handling requests
"""
import json
import webapp2
import http
from zennla.exceptions import APIException


class ModelViewSet(webapp2.RequestHandler):
    """
    ModelViewSet can be used to handle requests on a resource level
    Can be subclassed to create specialized viewsets for a resource
    The attributes that can be set are:
        - `query`: The base query on which all list operations occur
        - `serializer_class`: The serializers.ModelSerializer class
                which is to be used for serialization
    """
    query = None
    serializer_class = None

    def dispatch(self):
        """Dispatches the request.

        This will first check if there's a handler_method defined in the
        matched route, and if not it'll use the method correspondent to the
        request method (``get()``, ``post()`` etc).
        """
        request = self.request
        method_name = request.route.handler_method or \
            request.method.lower().replace('-', '_')

        method = getattr(self, method_name, None)
        if method is None:
            # 405 Method Not Allowed.
            # The response MUST include an Allow header containing a
            # list of valid methods for the requested resource.
            # http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.4.6
            valid = ', '.join(self._get_handler_methods())
            self.abort(405, headers=[('Allow', valid)])

        # The handler only receives *args if no named variables are set.
        args, kwargs = request.route_args, request.route_kwargs
        if kwargs:
            args = ()

        try:
            pre_method_handler = getattr(self, 'pre_' + method_name, None)
            if pre_method_handler is not None:
                pre_method_handler(*args, **kwargs)
            try:
                response = method(*args, **kwargs)
            except APIException as e:
                self.response.headers['Content-Type'] = 'application/json'
                self.response.write(e.detail)
                self.response.status_int = e.status_code
                return
            post_method_handler = getattr(self, 'post_' + method_name, None)
            if post_method_handler is not None:
                post_method_handler(*args, **kwargs)
            self.response.headers['Content-Type'] = 'application/json'
            return response
        except Exception, e:
            return self.handle_exception(e, self.app.debug)

    def get_query(self, *args, **kwargs):
        """
        Return the `query` for the viewset
        Override and add any pre-filtering required on the queryset
        """
        return self.query

    def get_serializer_class(self, *args, **kwargs):
        """
        Return the `serializer_class` for the viewset
        Override this method to dynamically select a serializer class
        based on the request
        """
        return self.serializer_class

    def get(self, *args, **kwargs):
        """
        Correspond to HTTP GET
        """
        if args or kwargs:
            self.retrieve(*args, **kwargs)
        else:
            self.list(*args, **kwargs)

    def list(self, *args, **kwargs):
        """
        Handle GET resource-list
        """
        query = self.get_query(*args, **kwargs)
        serializer = self.get_serializer_class(*args, **kwargs)()
        data = serializer.serialize(query)
        self.response.write(data)

    def retrieve(self, *args, **kwargs):
        """
        Handle GET resource-detail
        """
        serializer = self.get_serializer_class(*args, **kwargs)()
        obj = serializer.get_obj(id=kwargs.values()[0])
        data = serializer.serialize(obj)
        self.response.write(data)

    def post(self, *args, **kwargs):
        """
        Correspond to HTTP POST
        """
        data = json.loads(self.request.body)
        serializer = self.get_serializer_class(*args, **kwargs)()
        obj = serializer.create(data=data)
        self.response.write(serializer.serialize(obj))

    def put(self, *args, **kwargs):
        """
        Correspond to HTTP PUT
        """
        data = json.loads(self.request.body)
        serializer = self.get_serializer_class(*args, **kwargs)()
        updated_obj = serializer.update(data=data, id=kwargs.values()[0])
        self.response.write(serializer.serialize(updated_obj))

    def delete(self, *args, **kwargs):
        """
        Correspond to HTTP DELETE
        """
        serializer = self.get_serializer_class(*args, **kwargs)()
        obj = serializer.get_obj(id=kwargs.values()[0])
        obj.key.delete()
        self.response.status_int = http.HTTP_204_NO_CONTENT

    def patch(self, *args, **kwargs):
        """
        Correspond to HTTP PATCH
        """
        kwargs['partial'] = True
        self.put(*args, **kwargs)
