import json
from google.appengine.ext import ndb


class NonSerializableException(Exception):
    pass


class ValidationError(Exception):
    pass


class ModelSerializer(object):
    include_fields = None
    exclude_fields = None
    translate_fields = {}
    model = None

    @ndb.transactional
    def _save(self, data, instance):
        validated_data = self.validate(data)
        instance.populate(**validated_data)
        instance.put()
        return instance

    def create(self, data, model=None):
        return self._save(data=data, instance=self.get_obj(model=model))

    def to_dict_repr(self, obj):
        dct = obj.to_dict(
            include=self.include_fields,
            exclude=self.exclude_fields
        )
        dct['id'] = obj.key.id()
        for key, value in self.translate_fields.iteritems():
            dct[value] = dct.pop(key)
        for key in dct:
            dct[key] = getattr(self, 'get_' + key, lambda _: dct[key])(obj)
        return dct

    def serialize(self, serializable):
        if isinstance(serializable, ndb.Model):
            return json.dumps(self.to_dict_repr(serializable))
        elif isinstance(serializable, ndb.Query):
            serializable = serializable.fetch()
            return json.dumps([
                self.to_dict_repr(obj) for obj in serializable
            ])
        raise NonSerializableException()  # TODO

    def update(self, data, id, model=None, partial=False):
        return self._save(data, instance=self.get_obj(id=id, model=model))

    def validate(self, data):
        # TODO
        return data

    def get_obj(self, id=None, model=None):
        model = model or self.model
        if not isinstance(model, ndb.model.MetaModel):
            # TODO
            raise ValidationError(
                "Expected an NDB model. Got {type} instead".format(
                    type=type(model).__name__
                )
            )
        try:
            id = int(id)
        except ValueError:
            pass
        obj = model() if id is None else model.get_by_id(id)
        if id is not None and obj is None:
            raise ValidationError(
                "Object with id {id} not found".format(id=id)
            )
        return obj