from Products.CMFPlone.browser.syndication.views import FeedView
from DateTime.DateTime import DateTime


class FeedViewCustom(FeedView):

    def __call__(self):
        return_value = super(FeedView, self).__call__()
        self.request.response.setHeader('Content-Type', 'application/xml')
        return return_value

    def localized_time(self, date):
        local_date = DateTime(date)
        return local_date.strftime('%Y-%m-%d %X')
