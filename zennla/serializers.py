import json
from google.appengine.ext import ndb


class NonSerializableException(Exception):
    pass


class ModelSerializer(object):
    include_fields = None
    exclude_fields = None
    translate_fields = {}
    model = None

    def save(self, data, type, model=None):
        # type = 'create, update, partial update'
        # TODO
        model = model or self.model
        assert (
            isinstance(model, ndb.Model),
            "Expected an NDB model. Got {type} instead".format(
                type=type(model).__name__
            )
        )
        validated_data = self.validate(data)
        obj = model.get_by_id()

    def create(self, data, model=None):
        return self.save(data=data, type='create', model=model)

    def to_dict_repr(self, obj):
        dct = obj.to_dict(
            include=self.include_fields,
            exclude=self.exclude_fields
        )
        for key, value in translate_fields.iteritems():
            dct[value] = dct.pop(key)
        for key in dct:
            dct[key] = getattr(self, 'get_' + key, lambda _: dct[key])(obj)

    def serialize(self, serializable):
        if isinstance(serializable, ndb.Model):
            return json.dumps(to_dict_repr(serializable))
        elif isinstance(serializable, ndb.Query):
            return json.dumps([
                self.to_dict_repr(obj) for obj in serializable
            ])
        else:
            raise NonSerializableException()

    def update(self, data, model=None, partial=False):
        return self.save(data, model, type='partial_update', model=model)

    def validate(self):
        # TODO
        pass
