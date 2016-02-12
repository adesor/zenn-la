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

    def _dict_to_xml(self, data_dict, tag=None):
        """
        Convert the input dict to XML
        """
        tag = tag or 'response'
        elem = ElementTree.Element(tag)
        if not isinstance(data_dict, dict):
            elem.text = unicode(data_dict)
        else:
            for key, value in data_dict.iteritems():
                if isinstance(value, dict):
                    child = self._dict_to_xml(value, key)
                    elem.append(child)
                elif not isinstance(value, (list, tuple)):
                    child = ElementTree.Element(key)
                    child.text = str(value)
                    elem.append(child)
                else:
                    for val in value:
                        child = ElementTree.Element(key)
                        child.text = str(val)
                        elem.append(child)
        return elem

    def render(self, data, tag=None):
        if data is None:
            return bytes()
        return ElementTree.tostring(self._dict_to_xml(data, tag))
