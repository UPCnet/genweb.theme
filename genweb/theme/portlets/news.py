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
                       sort_limit=limit)[:limit]
        important = len(results)
        results2 = catalog(portal_type=('News Item', 'Link'),
                       review_state=state,
                       is_important=False,
                       sort_on=('Date'),
                       sort_order='reverse',
                       sort_limit=limit - important)[:limit - important]
        # for brain in results2:
        #     obj = brain.getObject()
        #     import ipdb; ipdb.set_trace()
        #     if obj.title == "a" or obj.title == "b":
        #         IImportant(obj).is_important = True
        #         import transaction; transaction.commit()
        return results + results2


class AddForm(base.AddForm):
        form_fields = form.Fields(INewsPortlet)
        label = _(u"Add Noticies portlet")
        description = _(u"Aquest portlet mostra noticies")

        def create(self, data):
            return Assignment(count=data.get('count', 5), showdata=data.get('showdata', True))
