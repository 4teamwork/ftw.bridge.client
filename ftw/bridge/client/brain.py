from ftw.bridge.client.interfaces import IBrainRepresentation
from ftw.bridge.client.interfaces import IBrainSerializer
from ftw.bridge.client.utils import get_brain_url
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping
from Products.CMFCore.utils import getToolByName
from zope.component.hooks import getSite
from zope.interface import implements
import DateTime
import Missing


class BrainSerializer(object):
    implements(IBrainSerializer)

    def serialize_brains(self, results):
        data = []
        for brain in results:
            data.append(self._serialize_brain(brain))
        return data

    def deserialize_brains(self, data, total_length=None):
        if not isinstance(data, list):
            raise ValueError('data should be a list, got %s' % type(data))

        results = []
        for brain_data in data:
            brain_data = self._decode_data(brain_data)
            results.append(BrainRepresentation(brain_data))

        return BrainResultSet(results, total_length)

    def _serialize_brain(self, brain):
        data = {self._encode('_url'): self._encode(get_brain_url(brain))}

        for name in self._get_metadata_names(brain):
            value = getattr(brain, name, None)
            data[self._encode(name)] = self._encode(value)

        return data

    def _encode(self, value):
        if isinstance(value, str):
            return value.decode('utf-8')

        elif value is Missing.Value:
            return [':Missing.Value']

        elif isinstance(value, DateTime.DateTime):
            return [':DateTime', str(value)]

        elif isinstance(value, tuple):
            return self._encode(list(value))

        elif isinstance(value, PersistentMapping):
            return self._encode(dict(value))

        elif isinstance(value, dict):
            return dict((self._encode(key), self._encode(value))
                        for key, value in value.items())

        elif isinstance(value, PersistentList):
            return self._encode(list(value))

        elif isinstance(value, list):
            return map(self._encode, value)

        return value

    def _decode(self, value):
        if isinstance(value, unicode):
            return value.encode('utf-8')

        elif isinstance(value, list) and len(value) < 1:
            return value

        elif isinstance(value, list) and value[0] == ':Missing.Value':
            return Missing.Value

        elif isinstance(value, list) and value[0] == ':DateTime':
            try:
                return DateTime.DateTime(value[1])
            except DateTime.interfaces.SyntaxError:
                return None

        return value

    def _decode_data(self, data):
        new_data = {}
        for key, value in data.items():
            new_data[self._decode(key)] = self._decode(value)
        return new_data

    def _get_metadata_names(self, brain):
        catalog = getToolByName(getSite(), 'portal_catalog')
        return catalog._catalog.names


class BrainResultSet(list):

    def __init__(self, data, total_length):
        super(BrainResultSet, self).__init__(data)
        self._total_length = total_length

    def get_total_length(self):
        return self._total_length


class BrainRepresentation(object):
    implements(IBrainRepresentation)

    def __init__(self, data):
        self._data = data

    def __getattr__(self, name):
        if name in self._data:
            return self._data[name]
        else:
            raise AttributeError(name)

    def getURL(self):
        return self._url
