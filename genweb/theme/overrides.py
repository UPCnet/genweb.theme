from Products.CMFPlone.browser.syndication.views import FeedView
from DateTime.DateTime import DateTime
from Products.PloneFormGen.content.saveDataAdapter import FormSaveDataAdapter
from BTrees.IOBTree import IOBTree
try:
    from BTrees.LOBTree import LOBTree
    SavedDataBTree = LOBTree
except ImportError:
    SavedDataBTree = IOBTree
import time


class FeedViewCustom(FeedView):

    def __call__(self):
        return_value = super(FeedView, self).__call__()
        self.request.response.setHeader('Content-Type', 'application/xml')
        return return_value

    def localized_time(self, date):
        local_date = DateTime(date)
        return local_date.strftime('%Y-%m-%d %X')


class FormSaveDataAdapterCustom(FormSaveDataAdapter):

    def _addDataRow(self, value):

        self._migrateStorage()

        if isinstance(self._inputStorage, IOBTree):
            # 32-bit IOBTree; use a key which is more likely to conflict
            # but which won't overflow the key's bits

            id = self._inputItems
            self._inputItems += 1
        else:
            # 64-bit LOBTree
            id = int(time.time() * 1000)
            while id in self._inputStorage:  # avoid collisions during testing
                id += 1
        self._inputStorage[id] = self.decodeCharacters(value)
        self._length.change(1)

    def decodeCharacters(self, txt):
        txt[3] = txt[3].decode('string_escape')
        return txt
