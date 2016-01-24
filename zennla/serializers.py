"""
Serializers have a two-fold purpose:
    - To provide a way of translating ndb models into primitive data-types
        and transforming them into a JSON string
    - To validate and translate primitive data into ndb model fields
        and create/update an object
"""
import json
from google.appengine.ext import ndb
from google.appengine.ext.db import BadValueError
from zennla.exceptions import NonSerializableException, ValidationError


class ModelSerializer(object):
    """
    ModelSerializer can be subclassed to create custom serializers
    for a model. The attributes that can be set are:
        - `model`: Set to a model class for which the serializers
                is being constructed.
        - `include_fields`: List of field names to be included in the
                serialized form of a model object.
        - `exclude_fields`: List of field names to be excluded
                during serialization. Takes precedence over `include_fields`
        - `translate_fields`: A dict mapping field names to the names used in
                serialized representation
    """
    include_fields = None
    exclude_fields = None
    translate_fields = {}
    model = None

    @ndb.transactional
    def _save(self, data, instance):
        """
        Populate and write an `instance` with `data` after validation
        Return the updated `instance`
        """
        validated_data = self.validate(data)
        instance.populate(**validated_data)
        instance.put()
        return instance

    def validate(self, data, model=None):
        """
        Take `data` as the dict containing the input data
        Return a dictionary with the validated data
        Raise a validation error if invalid data is found
        """
        validated_data = {}
        model = model or self.model
        properties = model._properties
        for prop_name, prop in properties.iteritems():
            field_value = data.get(
                self.translate_fields.get(prop_name), data.get(prop_name)
            )
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
                    validated_data[prop_name] = field_value \
                        if not prop._repeated else []
            else:
                try:
                    if prop._repeated:
                        if not isinstance(field_value, (list, tuple)):
                            raise ValidationError(
                                "`{field}` should be a list.".format(
                                    field=prop_name
                                )
                            )
                        else:
                            validated_data[prop_name] = [
                                prop._validate(elem) or elem
                                for elem in field_value
                            ]
                    else:
                        validated_data[prop_name] = prop._validate(
                            field_value
                        ) or field_value
                except BadValueError as e:
                    raise ValidationError(str(e))
        return validated_data

    def create(self, data, model=None):
        """
        Create a model instance with the given data
        Optionally take a `model` argument (default is self.model)
        """
        return self._save(data=data, instance=self.get_obj(model=model))

    def get_obj(self, id=None, model=None):
        """
        Return an instance at `id` of the given `model`
        (or of self.model if model isn't specified)
        Return a new instance if `id` isn't specified
        """
        model = model or self.model
        if not isinstance(model, ndb.model.MetaModel):
            raise ValidationError(
                "Expected an NDB model. Got {type} instead".format(
                    type=type(model).__name__
                )
            )
        try:
            id = int(id)
        except (TypeError, ValueError):
            pass
        obj = model() if id is None else model.get_by_id(id)
        if id is not None and obj is None:
            raise ValidationError(
                "Object with id {id} not found".format(id=id)
            )
        return obj

    def serialize(self, serializable):
        """
        Return a serialized representation of `serializable`
        `serializable` is either a queryset or a model object
        """
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

    def to_dict_repr(self, obj):
        """
        Model `Obj` -> dict representation
        Override this method to define custom dict representations
        """
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

    def update(self, data, id, model=None, partial=False):
        """
        Update the model object with at `id` with the given `data`
        Optionally take `model` as an argument (default is self.model)
        """
        return self._save(data, instance=self.get_obj(id=id, model=model))
