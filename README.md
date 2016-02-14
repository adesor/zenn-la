# Zenn-La
A REST microframework for Google App Engine (webapp2 and ndb)

##Contents
* [Installation](#installation)
* [Example Usage](#example-usage)
* [Custom Serializers](#custom-serializers)
* [Validations](#validations)
* [ViewSets](#viewsets)
* [Routers](#routers)
* [Filtering](#filtering)

## Installation:
Install using `pip`
```
$ pip install zennla
```
For help with adding third party Python packages in Google App Engine, read [here](https://cloud.google.com/appengine/docs/python/tools/libraries27?hl=en)

## Example Usage:
Suppose you have a model named `Pokemon`:
```python
from google.appengine.ext import ndb

class Pokemon(ndb.Model):
    name = ndb.StringProperty()
    type = ndb.StringProperty()
    number = ndb.IntegerProperty()
```

Define a serializer for this model:
```python
from zennla.serializers import ModelSerializer

class PokemonSerializer(ModelSerializer):
    model = Pokemon
```

Define a viewset for this model:
```python
from zennla.viewsets import ModelViewSet

class PokemonViewSet(ModelViewSet):
    serializer_class = PokemonSerializer
    model = Pokemon  # Optional - uses serializer_class's `model` instance by default
```

Add a route to your resource linking a base URL to the viewset:
```python
import webapp2
from zennla.routers import route

app = webapp2.WSGIApplication([
    route('/pokemon', PokemonViewSet)
])
```

...and you have a working API for the `Pokemon` model! It supports GET and POST on `pokemon/` and GET, PUT, DELETE on `pokemon/<id>/` by default.

You can create a `Pokemon` object as:
```
{{base_url}}/pokemon/ [POST]
Body:
{
    "name": "Bulbasaur",
    "type": "Grass",
    "number": 1
}

Response (201):
{
    "name": "Bulbasaur",
    "type": "Grass",
    "number": 1,
    "id": 4785074604081152
}
```

You can fetch your `Pokemon` resource as:
```
{{base_url}}/pokemon/ [GET]

Response (200):
[
    {
        "name": "Bulbasaur",
        "type": "Grass",
        "number": 1,
        "id": 4785074604081152
    }
]
```

Or retrieve a specific `Pokemon` as:
```
{{base_url}}/pokemon/4785074604081152/ [GET]

Response (200):
{
    "name": "Bulbasaur",
    "type": "Grass",
    "number": 1,
    "id": 4785074604081152
}
```

Or update a `Pokemon` as:
```
{{base_url}}/pokemon/4785074604081152/ [PUT]
{
    "name": "Bulbasaur",
    "type": "Grass/Poison",
    "number": 1
}

Response (200):
{
    "name": "Bulbasaur",
    "type": "Grass/Poison",
    "number": 1,
    "id": 4785074604081152
}
```



## Custom Serializers
You can set the following attributes in the `ModelSerializer` subclass
- `include_fields`: List of field names to be included in the serialized form of a model object.
- `exclude_fields`: List of field names to be excluded in the serialized form of a model object. Takes precedence over `include_fields`
- `translate_fields`: A dict mapping field names to the names used in serialized representation

You can override `to_dict_repr` method to define your own dictionary representation of a model object.

You can also add a method named as `get_<field_name>` to define a custom representation for that field.

You can add pre and post save hooks (methods that run just before and after an object is written to the datastore respectively) by defining `pre_save(self, instance, data, validated_data)` and `post_save(self, instance, data, validated_data)` respectively.

### Example:
```python
class PokemonSerializer(ModelSerializer):
    model = Pokemon
    include_fields = ["name", "number"]  # Only include these fields
    translate_fields = {
        "number": "code"  # Translate `number` to `code` in serialized representation
    }

    def get_name(obj):
        return "Pokemon " + obj.name
```

```
{{base_url}}/pokemon/ [GET]
[
    {
        "name": "Pokemon Bulbasaur",
        "code": 1
    }
]
```


## Validations
The `ModelSerializer` by default performs a validation for field type on the input data. In addition to that, you can add your own field validations. You can also perform object level validations.
The field validations should be methods in your `ModelSerializer` named as `validate_<field_name>`. The method should raise a `ValidationError` if the input field value is not valid, or return silently.
You can define any object level validations by defining the `validate(self, data, model)` method.

The validation flow is:
- basic validations
- field validations
- object level validation

### Example:
```python
from zennla.exceptions import ValidationError

class PokemonSerializer(ModelSerializer):
    model = Pokemon

    def validate_name(self, field_value):
        """
        Only accept lower-case names
        """
        if field_value != field_value.lower():
            raise ValidationError("Name must be lower case!")
```

```
{{base_url}}/pokemon/ [POST]
{
    "name": "Mewtwo",
    "type": "Psychic"
    "number": 150
}

Response (400):
{
    "detail": "Name must be lower case!"
}
```



## Viewsets
Viewsets are request handler classes which provide CRUD operations.
To define custom viewsets, you can override `get()`, `put()`, `post()` and `delete()` or any other method corresponding to the allowed methods.

### Customizing
- You can also add pre and post method handler hooks to perform any actions. These should be defined as `pre_<handler_method>` or `post_<handler_method>`.

- You can add filtering to the viewsets by listing the FilterSets in the `filter_backends` attribute (Discussed in detail [here](#filtering)).

- You can support a number of media types by listing the renderers in the `renderers` attribute (Discussed in detail [here](#renderers))

- Overriding `get_query()`: You can override `get_query()` to perform any filtering of the result set before serialization.

- Overriding `get_serializer_class()`: You can override `get_serializer_class()` to choose a serializer class dynamically.

- Overridding `get_model()`: You can override `get_model()` to choose a model dynamically. Defaults to the model defined by the `model` attribute or, if not defined, the `model` attribute of the `serializer_class`.

### Example

```python
class PokemonViewSet(ModelViewSet):
    serializer_class = PokemonSerializer

    def pre_get(self, *args, **kwargs):
        # perform_some_action
        return

    def get_query():
        """
        Only query on Grass type Pokemon
        """
        return Pokemon.query(Pokemon.type == 'grass')
```



## Routers
Routers provide routing mechanism for resources. It contains a `route()` function which returns a `routes.PathPrefixRoute` (read [here](https://webapp-improved.appspot.com/guide/routing.html#path-prefix-routes)) mapping a request handler `viewset` with a `base_url`.

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



## Filtering
You can create filters by extending the `FilterSet` class. The `FilterSet` class lists all the filters that need to be applied to a query and contains a method `get_filtered_query()` which filters the query using the listed filters. The FilterSet must have an attribute whose name becomes a query parameter and value is equal to one of the `FieldFilter`s. The `FieldFilter`s defined by default are:

- `NumberFilter`: Use this to make a filter that takes numeric values
- `BooleanFilter`: Use this to make a filter that takes boolean values
- `StringFilter`: Use this to make a filter that takes string values

A `FilterField` needs to be specified an ndb model field on which it should be applied. It also has a `lookup_type` attribute which can be used to define the type of lookup. The valid values are:
- `'eq'`: Check for equality (default)
- `'in'`: Compare against a list of values
- `'ne'`: Check for inequality
- `'le'`: Check for less than or equals (<=)
- `'ge'`: Check for greater than or equals (>=)
- `'lt'`: Check for less than (<)
- `'gt'`: Check for greater than (>)

You can create your own FilterFields by overriding `get_converted_value()` which takes in a raw value (string) and converts it into the format required before any comparisons are done.

### Example
```python
from zennla import filters

class PokemonFilter(filters.FilterSet):
    name = filters.StringFilter(Pokemon.name)
    type = filters.StringFilter(Pokemon.type, lookup_type='in')
    num_ge = filters.NumberFilter(Pokemon.number, lookup_type='ge')

class PokemonViewSet(ModelViewSet):
    serializer_class = PokemonSerializer
    filter_backends = [PokemonFilter]  # Add the filterset to our viewset

```

```
{{base_url}}/pokemon/?name='Mewtwo'&type='Grass'&type='Psychic'&type='Electric'&num_ge=75 [GET]
{
    "name": "Mewtwo",
    "type": "Psychic"
    "number": 150
}

Response (200):
[
    {
        "name": "Mewtwo",
        "type": "Psychic"
        "number": 150
    }
]
```



## Renderers
Renderers are used to serialize a response into specific media types. They give a generic way of being able to handle various media types on the response, such as JSON encoded data or HTML output.

By default Zenn-La provides a `JSONRenderer` and an `XMLRenderer`. You can define custom renderers by subclassing `BaseRenderer` and setting the `media_type` and `format` attributes, and overriding the `render()` method.

The renderer is chosen corresponding to the `Accept` header set on the request (read [here](https://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html)). If no satisfying renderer is found associated with the viewset, a `406 - Not Acceptable` response is returned. If no `Accept` header is set, the first renderer in the `renderers` list of the view set is used. By default, `ModelViewSet` uses `JSONRenderer`.
