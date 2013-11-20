# coding=utf-8

import unittest
import tornado_rest_swagger.models.plain_swagger


class SoundtrackModel(object):
    """
    The music track a player is playing now.
    """

    def __init__(self):
        self.on = True
        self.volume = 70
        self.position = 61
        self.duration = 183
        self.title = u'несе Галя воду'


class PlainModelReaderTestCase(unittest.TestCase):
    def test_read(self):
        reader = tornado_rest_swagger.models.plain_swagger.PlainModelReader()
        swagger_model = reader.read(SoundtrackModel)
        self.assertIsNotNone(swagger_model)
        self.assertEqual('SoundtrackModel', swagger_model['id'])
        self.assertEqual('The music track a player is playing now.', swagger_model['description'])
        self.assertDictContainsSubset({'type': 'integer'}, swagger_model['properties']['position'])
        self.assertDictContainsSubset({'type': 'boolean'}, swagger_model['properties']['on'])
        self.assertDictContainsSubset({'type': 'string'}, swagger_model['properties']['title'])

