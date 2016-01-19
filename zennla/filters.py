"""
FilterSets can be used as filtering backends for a viewset.
They perform querying against query parameters supplied in a request
"""

import operator
from google.appengine.ext.db import BadValueError
from zennla.exceptions import ImproperlyConfigured, ValidationError


class Filter(object):
    def __init__(self, field, lookup_type='eq'):
        self.field = field
        self.lookup_type = lookup_type

    def get_filter(self, value):
        try:
            if self.lookup_type == 'in':
                if not isinstance(value, (list, tuple)):
                    raise ImproperlyConfigured(
                        "IN comparison must be against a list or a tuple. "
                        "Found {type} instead".format(
                            type=type(value).__name__
                        )
                    )
                return self.field.IN(value)
            try:
                return getattr(operator, self.lookup_type)(
                    self.field, value
                )
            except AttributeError:
                raise ImproperlyConfigured(
                    "`lookup_type` must be one of: `in`, `eq`, `ne`, `gt`, "
                    "`ge`, `lt`, `le`. Found {lookup_field} instead.".format(
                        lookup_field=self.lookup_type
                    )
                )
        except BadValueError as e:
            raise ImproperlyConfigured(
                "Mismatch in the filter type and the model's field type "
                "({filter_type} used for {field_type})".format(
                    filter_type=type(self).__name__,
                    field_type=type(self.field).__name__
                )
            )


class NumberFilter(Filter):
    def get_filter(self, value):
        try:
            number_value = float(value)
        except ValueError:
            raise ValidationError(
                "Value passed for {filter_type} is not a number. "
                "Found {value_type} instead".format(
                    filter_type=type(self).__name__,
                    value_type=type(value).__name__
                )
            )
        return super(NumberFilter, self).get_filter(number_value)


class BooleanFilter(Filter):
    def get_filter(self, value):
        bool_value = value.lower() not in ('false', '0', 'no', 'f', 'n')
        return super(BooleanFilter, self).get_filter(bool_value)


class StringFilter(Filter):
    def get_filter(self, value):
        try:
            str_value = unicode(value)
        except ValueError:
            raise ValidationError(
                "Value passed for {filter_type} is not a string. "
                "Found {value_type} instead".format(
                    filter_type=type(self).__name__,
                    value_type=type(value).__name__
                )
            )
        return super(StringFilter, self).get_filter(str_value)


class FilterSet(object):
    class Meta:
        filters = []

    def get_filters(self, field_values):
        return (
            getattr(self, filter_name).get_filter(
                field_values.getall(filter_name)
                if getattr(
                    self, filter_name
                ).lookup_type == 'in' else field_values.get(filter_name)
            )
            for filter_name in self.Meta.filters
            if filter_name in field_values
        )

    def get_filtered_query(self, query, field_values):
        return query.filter(*self.get_filters(field_values))
