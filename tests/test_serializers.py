import sys
sys.path.insert(1, 'google-cloud-sdk/platform/google_appengine')
sys.path.insert(1, 'google-cloud-sdk/platform/google_appengine/lib/yaml/lib')
import unittest
import json

from google.appengine.ext import ndb
from google.appengine.ext import testbed
from zennla.serializers import ModelSerializer


class TestModel(ndb.Model):
    number = ndb.IntegerProperty(default=42)
    text = ndb.StringProperty()


class TestSerializer(ModelSerializer):
    model = TestModel


class SerializerTestCase(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        ndb.get_context().clear_cache()

        self.sample_data = {
            'number': 1,
            'text': 'test_text'
        }
        self.test_serializer = TestSerializer()

    def tearDown(self):
        self.testbed.deactivate()

    def dict_to_filters(self, base_entity=None, mapping=None):
        base_entity = base_entity or TestModel
        mapping = mapping or self.sample_data
        filters = []
        for key, value in mapping.iteritems():
            if not isinstance(value, dict):
                filters.append(getattr(base_entity, key) == value)
            else:
                filters.extend(
                    self.dict_to_filters(
                        base_entity=getattr(base_entity, key),
                        mapping=value
                    )
                )
        return filters

    def test_validate_base_case(self):
        self.assertEqual(
            self.test_serializer._validate(self.sample_data), self.sample_data
        )

    def test__save(self):
        instance = TestModel()
        count_before__save = TestModel.query(*self.dict_to_filters()).count()
        self.test_serializer._save(self.sample_data, instance)
        count_after__save = TestModel.query(*self.dict_to_filters()).count()
        self.assertEqual(count_after__save, count_before__save + 1)

    def test_get_obj_new_instance(self):
        self.assertEqual(self.test_serializer.get_obj(), TestModel())

    def test_get_obj_existing_instance(self):
        key = TestModel(**self.sample_data).put()
        self.assertEqual(
            self.test_serializer.get_obj(id=key.id()),
            TestModel.get_by_id(key.id())
        )

    def test_create(self):
        count_before_create = TestModel.query(*(
            self.dict_to_filters()
        )).count()
        self.test_serializer.create(self.sample_data)
        count_after_create = TestModel.query(*(
            self.dict_to_filters()
        )).count()
        self.assertEqual(count_after_create, count_before_create + 1)

    def test_to_dict_repr(self):
        key = TestModel(**self.sample_data).put()
        obj = key.get()
        dict_repr = dict(self.sample_data)
        dict_repr.update({'id': key.id()})
        self.assertEqual(
            dict_repr, self.test_serializer.to_dict_repr(obj)
        )

    def test_serialize(self):
        key = TestModel(**self.sample_data).put()
        dict_repr = dict(self.sample_data)
        dict_repr.update({'id': key.id()})
        self.assertEqual(dict_repr, self.test_serializer.serialize(key.get()))
