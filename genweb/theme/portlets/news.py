from zope import schema
from zope.interface import implements
from zope.formlib import form
from plone.app.portlets.portlets import base
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFPlone import PloneMessageFactory as _
from Acquisition import aq_inner
from plone.memoize.instance import memoize
from plone.portlets.interfaces import IPortletDataProvider
from Products.CMFCore.utils import getToolByName
from genweb.core.adapters import IImportant

from zope.component import getMultiAdapter
from plone.app.layout.navigation.root import getNavigationRootObject

from plone.app.portlets.portlets.news import Renderer as news_renderer


class INewsPortlet(IPortletDataProvider):
    """A portlet which can render a list of news.
    """
    count = schema.Int(
        title=_(u"Numero de noticies a mostrar"),
        description=_(u"Maxim numero de noticies a mostrar (5 o 7)"),
        required=True,
        default=5,
        min=5,
        max=7)

    showdata = schema.Bool(
        title=_(u"Mostra data?"),
        description=_(u"Boolea que indica si s'ha de mostrar la data en les noticies"),
        required=True,
        default=True,
        )


class Assignment (base.Assignment):
    implements(INewsPortlet)

    def __init__(self, count=5, showdata=True):
        self.count = count
        self.showdata = showdata
    title = _(u"Noticies", default=u'Noticies')


class Renderer(news_renderer):
    render = ViewPageTemplateFile('templates/news.pt')

    def mostraData(self):
        return self.data.showdata

    def all_news_link(self):
        context = aq_inner(self.context)
        portal_state = getMultiAdapter((context, self.request),
            name=u'plone_portal_state')
        portal = portal_state.portal()
        if 'news' in getNavigationRootObject(context, portal).objectIds():
            return '%s/news' % portal_state.navigation_root_url()
        return None

    @memoize
    def _data(self):
        context = aq_inner(self.context)
        catalog = getToolByName(context, 'portal_catalog')
        limit = self.data.count
        state = ['published', 'intranet']
        results = catalog(portal_type=('News Item', 'Link'),
                       review_state=state,
                       is_important=True,
                       sort_on="getObjPositionInParent",
                       sort_limit=limit)
        important = len(results)
        if important < limit:
            results2 = catalog(portal_type=('News Item', 'Link'),
                       review_state=state,
                       is_important=False,
                       sort_on=('Date'),
                       sort_order='reverse',
                       sort_limit=limit - important)
            return results + results2
        else:
            return results


class AddForm(base.AddForm):
        form_fields = form.Fields(INewsPortlet)
        label = _(u"Add Noticies portlet")
        description = _(u"Aquest portlet mostra noticies")

        def create(self, data):
            return Assignment(count=data.get('count', 5), showdata=data.get('showdata', True))
