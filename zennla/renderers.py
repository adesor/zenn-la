"""
Renderers are used to serialize a response into specific media types.
They give us a generic way of being able to handle various media types
on the response, such as JSON encoded data or HTML output.
"""
import json
from xml.etree import ElementTree


class BaseRenderer(object):
    """
    All renderers should extend this class, setting the `media_type`
    and `format` attributes, and override the `.render()` method.
    """
    media_type = None
    format = None

    def render(self, data):
        raise NotImplementedError(
            'Renderer class requires .render() to be implemented'
        )


class JSONRenderer(BaseRenderer):
    """
    Renderer which serializes to JSON
    """
    media_type = 'application/json'
    format = 'json'

    def render(self, data):
        if data is None:
            return bytes()
        return json.dumps(data)


class XMLRenderer(BaseRenderer):
    """
    Renderer which serializes to XML
    """
    media_type = 'application/xml'
    format = 'xml'

    def _data_to_xml(self, data, tag=None):
        """
        Convert the input data to XML
        """
        tag = tag or 'response'
        elem = ElementTree.Element(tag)
        if isinstance(data, (list, tuple)):
            for item in data:
                elem.append(self._dict_to_xml(item, tag=tag or 'list'))
        elif isinstance(data, dict):
            for key, value in data.iteritems():
                elem.append(self._dict_to_xml(value, tag=key))
        else:
            elem.text = unicode(data)
        return elem

    def render(self, data, tag=None):
        if data is None:
            return bytes()
        return ElementTree.tostring(self._data_to_xml(data, tag))
