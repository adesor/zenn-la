"""
FilterSets can be used as filtering backends for a viewset.
They perform querying against query parameters supplied in a request
"""

import operator
from google.appengine.ext.db import BadValueError
from zennla.exceptions import ImproperlyConfigured, ValidationError


class FieldFilter(object):
    """
    The base class for all field type filters
    Extend to create custom Field Filters
    """
    def __init__(self, field, lookup_type='eq'):
        """
        FieldFilter has two base attributes:
            `field`: The ndb field for which the filter is applicable
            `lookup_type`: The type of comparison against the value supplied.
                It can have the following values:
                - `in`: field value in [list, of, values]
                - `eq`: field value == value
                - `ne`: field value != value
                - `gt`: field value > value
                - `ge`: field value >= value
                - `lt`: field value < value
                - `le`: field value <= value
        """
        self.field = field
        self.lookup_type = lookup_type

    def get_converted_value(self, value):
        """
        Convert the input value to another value
        Override this method to create filters that take non-string values
        """
        return value

    def get_filter(self, value):
        """
        Return a FilterNode object comparing the `field` with the `value`
        using the `lookup_type`. You are unlikely to want to override
        this method.
        """
        try:
            if self.lookup_type == 'in':
                if not isinstance(value, (list, tuple)):
                    raise ImproperlyConfigured(
                        "IN comparison must be against a list or a tuple. "
                        "Found {type} instead".format(
                            type=type(value).__name__
                        )
                    )
                converted_value = [
                    self.get_converted_value(elem) for elem in value
                ]
                return self.field.IN(converted_value)
            try:
                converted_value = self.get_converted_value(value)
                return getattr(operator, self.lookup_type)(
                    self.field, converted_value
                )
            except AttributeError:
                raise ImproperlyConfigured(
                    "`lookup_type` must be one of: `in`, `eq`, `ne`, `gt`, "
                    "`ge`, `lt`, `le`. Found {lookup_field} instead.".format(
                        lookup_field=self.lookup_type
                    )
                )
        except BadValueError:
            raise ImproperlyConfigured(
                "Mismatch in the filter type and the model's field type "
                "({filter_type} used for {field_type})".format(
                    filter_type=type(self).__name__,
                    field_type=type(self.field).__name__
                )
            )


class NumberFilter(FieldFilter):
    """
    Filter for numeric values
    """
    def get_converted_value(self, value):
        """
        Overridden to convert input value to its numeric equivalent
        """
        try:
            return float(value)
        except ValueError:
            raise ValidationError(
                "Value passed for {filter_type} is not a number. "
                "Found {value_type} instead".format(
                    filter_type=type(self).__name__,
                    value_type=type(value).__name__
                )
            )


class BooleanFilter(FieldFilter):
    """
    Filter for boolean values
    """
    def get_converted_value(self, value):
        """
        Overridden to convert input value to its boolean equivalent
        """
        return value.lower() not in ('false', '0', 'no', 'f', 'n')


class StringFilter(FieldFilter):
    """
    Filter for string values
    """
    def get_converted_value(self, value):
        """
        Overridden to convert input value to its string equivalent
        """
        try:
            return unicode(value)
        except ValueError:
            raise ValidationError(
                "Value passed for {filter_type} is not a string. "
                "Found {value_type} instead".format(
                    filter_type=type(self).__name__,
                    value_type=type(value).__name__
                )
            )


class FilterSet(object):
    """
    A FilterSet is associated with a ViewSet. The FilterSet filters the query
    based on any FilterSet associated with it.
    """
    class Meta:
        filters = []  # List any FieldFilters that need to be applied here

    def get_filters(self, field_values):
        """
        Return a generator for all the FilterFields listed in `Meta.filters`
        `field_values` is a mapping of field names and their values
        and is used to compare against the FilterFields
        """
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
        """
        Filter the `query` against the filters listed in `Meta.filters`
        """
        return query.filter(*self.get_filters(field_values))
