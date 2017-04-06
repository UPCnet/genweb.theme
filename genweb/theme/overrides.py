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
