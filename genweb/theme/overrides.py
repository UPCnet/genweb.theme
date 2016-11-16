from Products.CMFPlone.browser.syndication.views import FeedView
from DateTime.DateTime import DateTime


class FeedViewCustom(FeedView):

    def localized_time(self, date):
        local_date = DateTime(date)
        return local_date.strftime('%Y-%m-%d %X')
