from Acquisition import aq_inner
from plone import api
from zope import schema
from zope.interface import implements
from zope.formlib import form

from plone.app.portlets.portlets import base
from plone.memoize.instance import memoize
from plone.portlets.interfaces import IPortletDataProvider

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFCore.utils import getToolByName

from genweb.core.interfaces import INewsFolder

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
        max=7
    )

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

    @property
    def title(self):
        return _(u"News")


class Renderer(news_renderer):
    render = ViewPageTemplateFile('templates/news.pt')

    def mostraData(self):
        return self.data.showdata

    def all_news_link(self):
        pc = api.portal.get_tool('portal_catalog')
        news_folder = pc.searchResults(object_provides=INewsFolder.__identifier__)

        if news_folder:
            return '%s' % news_folder[0].getURL()
        else:
            return ''

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
        results = [a for a in results]
        important = len(results)
        if important < limit:
            results2 = catalog(portal_type=('News Item', 'Link'),
                       review_state=state,
                       is_important=False,
                       sort_on=('Date'),
                       sort_order='reverse')
                       #, sort_limit=limit - important)
            results3 = []
            path_folder_news = self.all_news_link()
            for brain in results2:
                brain_url = brain.getURL()
                brain_type = brain.Type
                if brain_type == 'Link' and brain_url.startswith(path_folder_news) or brain_type == 'News Item':
                    results3.append(brain)
                if len(results3) == limit - important:
                    break
            return results + results3
        else:
            return results


class AddForm(base.AddForm):
        form_fields = form.Fields(INewsPortlet)
        label = _(u"Add Noticies portlet")
        description = _(u"Aquest portlet mostra noticies")

        def create(self, data):
            return Assignment(count=data.get('count', 5), showdata=data.get('showdata', True))


class EditForm(base.EditForm):
    form_fields = form.Fields(INewsPortlet)
    label = _(u"Edit News Portlet")
    description = _(u"This portlet displays recent News Items.")
