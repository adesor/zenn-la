# Zenn-La
A REST microframework for Google App Engine (webapp2 and ndb)

## Installation:
Install using `pip`
```
$ pip install zennla
```

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
    query = Pokemon.query()
    serializer_class = PokemonSerializer
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
The `ModelSerializer` by default performs a validation for field type on the input data. However, in addition to that, you can add your own field validations.
The field validations should be methods in your `ModelSerializer` named as `validate_<field_name>`. The method should raise a `ValidationError` if the input field value is not valid, or return silently.

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

- Overriding `get_query()`: You can override `get_query()` to perform any filtering of the result set before serialization.

- Overriding `get_serializer_class()`: You can override `get_serializer_class()` to choose a serializer class dynamically.

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
Routers provide routing mechanism for resources. It contains a `route()` function which returns a `routes.PathPrefixRoute` (see: https://webapp-improved.appspot.com/guide/routing.html#path-prefix-routes) mapping a request handler `viewset` with a `base_url`.

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
