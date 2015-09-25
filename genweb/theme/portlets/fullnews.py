from Acquisition import aq_inner
from plone import api
from zope import schema
from zope.interface import implements
from zope.formlib import form

from plone.app.portlets.portlets import base
from plone.memoize.instance import memoize
from plone.portlets.interfaces import IPortletDataProvider

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
# from Products.CMFPlone import PloneMessageFactory as _
from genweb.core import GenwebMessageFactory as _
from Products.CMFCore.utils import getToolByName

from genweb.core.interfaces import INewsFolder
from genweb.core.utils import pref_lang

from plone.app.portlets.portlets.news import Renderer as news_renderer


class IFullNewsPortlet(IPortletDataProvider):
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
    implements(IFullNewsPortlet)

    def __init__(self, count=5, showdata=True):
        self.count = count
        self.showdata = showdata

    @property
    def title(self):
        return _(u"Full News")


class Renderer(news_renderer):
    render = ViewPageTemplateFile('templates/fullnews.pt')

    def mostraData(self):
        return self.data.showdata

    def all_news_link(self):
        pc = api.portal.get_tool('portal_catalog')
        news_folder = pc.SearchResults(object_provides=INewsFolder.__identifier__,
                                       Language=pref_lang())

        if news_folder:
            return '%s' % news_folder[0].getURL()
        else:
            return ''

    def rss_news_link(self):
        pc = api.portal.get_tool('portal_catalog')
        news_folder = pc.SearchResults(object_provides=INewsFolder.__identifier__,
                                       Language=pref_lang())

        if news_folder:
            return '%s%s' % (news_folder[0].getURL(), '/aggregator/RSS')
        else:
            return ''

    def abrevia(self, obj):
        desc_new = obj.Description

        if len(desc_new) > 200:
            desc_text = desc_new[:200]
            desc_text = desc_text[:desc_text.rfind(' ') - len(desc_text)]
            desc_text = desc_text + '...'
        else:
            desc_text = desc_new
        return desc_text

    @memoize
    def _data(self):
        context = aq_inner(self.context)
        catalog = getToolByName(context, 'portal_catalog')
        limit = self.data.count
        state = ['published', 'intranet']
        results = catalog(portal_type=('News Item', 'Link'),
                       review_state=state,
                       is_important=True,
                       Language=pref_lang(),
                       sort_on="getObjPositionInParent",
                       sort_limit=limit)
        results = [a for a in results]
        important = len(results)
        if important < limit:
            results2 = catalog(portal_type=('News Item', 'Link'),
                       review_state=state,
                       is_important=False,
                       Language=pref_lang(),
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
        form_fields = form.Fields(IFullNewsPortlet)
        label = _(u"Add Noticies portlet")
        description = _(u"Aquest portlet mostra noticies")

        def create(self, data):
            return Assignment(count=data.get('count', 5), showdata=data.get('showdata', True))


class EditForm(base.EditForm):
    form_fields = form.Fields(IFullNewsPortlet)
    label = _(u"Edit News Portlet")
    description = _(u"This portlet displays recent News Items.")
