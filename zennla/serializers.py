import json
from google.appengine.ext import ndb
from google.appengine.ext.db import BadValueError
from zennla.exceptions import NonSerializableException, ValidationError


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
        raise NonSerializableException(
            "Object of type {type} is not serializable".format(
                type=type(serializable).__name__
            )
        )

    def update(self, data, id, model=None, partial=False):
        return self._save(data, instance=self.get_obj(id=id, model=model))

    def validate(self, data, model=None):
        validated_data = {}
        model = model or self.model
        properties = model._properties
        for prop_name, prop in properties.iteritems():
            field_value = data.get(prop_name)
            field_validation_method = getattr(
                self, 'validate_' + prop_name, None
            )
            if field_validation_method is not None:
                field_validation_method(field_value)
            if field_value is None:
                if prop._required:
                    raise ValidationError(
                        "Property {name} is required".format(name=prop_name)
                    )
                else:
                    validated_data[prop_name] = field_value
            else:
                try:
                    validated_data[prop_name] = prop._validate(field_value)
                except BadValueError as e:
                    raise ValidationError(str(e))
        return validated_data

    def get_obj(self, id=None, model=None):
        model = model or self.model
        if not isinstance(model, ndb.model.MetaModel):
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
