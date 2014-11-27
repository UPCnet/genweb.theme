from zope.interface import implements

from plone.app.portlets.portlets import base

from plone.portlets.interfaces import IPortletDataProvider

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFPlone import PloneMessageFactory as _

from genweb.core import utils

import feedparser


class IUPCNewsPortlet(IPortletDataProvider):
    """A portlet which can render a list of news from UPC.
    """


class Assignment (base.Assignment):
    implements(IUPCNewsPortlet)

    @property
    def title(self):
        return _(u"UPCNews")


class Renderer(base.Renderer):
    render = ViewPageTemplateFile('templates/upcnews.pt')

    def mes(self, mes):
        return self.utils.mes(mes)

    def dia_semana(self, dia):
        return self.utils.dia_semana(dia)

    def getRSS(self):

        idioma = utils.pref_lang()

        if idioma == 'zh':  # Force RSS en angles a web en chino
            idioma = 'en'

        url = 'http://www.upc.edu/saladepremsa/actualitat-upc/RSS?set_language=' + idioma

        items = []

        d = feedparser.parse(url)
        for item in d['items']:
            try:
                link = item.links[0]['href']
                itemdict = {
                    'title': item.title,
                    'url': link + '?set_language=' + idioma,
                    'summary': item.get('description', ''),
                }
            except AttributeError:
                continue
            items.append(itemdict)
        return items[:5]

    def getUrlRSSPremsa(self):
        idioma = idioma = utils.pref_lang()
        url_rss = 'http://www.upc.edu/saladepremsa/actualitat-upc/RSS?set_language=' + idioma
        return url_rss


class AddForm(base.NullAddForm):

        def create(self):
            return Assignment()
