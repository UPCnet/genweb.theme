from plone import api
from zope.interface import implements

from genweb.core.interfaces import IHomePage
from genweb.core.utils import pref_lang

from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from Products.CMFPlone import PloneMessageFactory as _
from genweb.core import GenwebMessageFactory as GWMF


class IHomepagePortlet(IPortletDataProvider):
    """A portlet which can render a login form.
    """


class Assignment(base.Assignment):
    implements(IHomepagePortlet)

    title = GWMF(u'homepage_portlet', default=u'Homepage')


class Renderer(base.Renderer):

    render = ViewPageTemplateFile('templates/homepage.pt')

    def getHomepage(self):
        page = {}
        pc = api.portal.get_tool('portal_catalog')
        result = pc.searchResults(object_provides=IHomePage.__identifier__,
                                  Language=pref_lang())
        if not result:
            page['body'] = ''
        else:
            page['body'] = result[0].getObject().text.output

        return page


class AddForm(base.NullAddForm):

    def create(self):
        return Assignment()
