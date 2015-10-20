from plone import api
from plone.memoize.instance import memoize
from plone.portlets.interfaces import IPortletDataProvider
from zope.formlib import form
from zope.interface import implements
from zope import schema
from zope.schema.interfaces import IContextSourceBinder
from zope.interface import directlyProvides

from Acquisition import aq_parent
from DateTime.DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.app.portlets.portlets import base

from plone.app.portlets import PloneMessageFactory as _

from genweb.core.utils import pref_lang

from zope.schema.vocabulary import SimpleVocabulary

from zope.i18nmessageid import MessageFactory
PLMF = MessageFactory('plonelocales')


def groupTags(self):

    portal = api.portal.get()
    path_portlet = "/".join(aq_parent(aq_parent(self)).getPhysicalPath())
    catalog = getToolByName(portal, 'portal_catalog')

    terms = []
    listterms = []
    state = ['published', 'intranet']
    """ todos los tags en esta carpeta
    """
    results = catalog(portal_types=('News Item', 'Event'),
                      path = {'query': path_portlet},
                              review_state=state,
                              Language=pref_lang()
                      )

    results = [a for a in results]
    for brain in results:
        if brain["Subject"] is not None:
            for b in brain["Subject"]:
                if b not in listterms:
                    listterms.append(b)
                    terms.append(SimpleVocabulary.createTerm(str(b)))

    return SimpleVocabulary(terms)
directlyProvides(groupTags, IContextSourceBinder)


def friendly_types(context):
    """ List user-selectable content types.

    We cannot use the method provided by the IPortalState utility view,
    because the vocabulary factory must be available in contexts where
    there is no HTTP request (e.g. when installing add-on product).

    This code is copied from
    https://github.com/plone/plone.app.layout/blob/master/plone/app/layout/globals/portal.py

    @return: Generator for (id, type_info title) tuples
    """
    termsTypes = []
    # site_properties = getToolByName(context, "portal_properties").site_properties
    # not_searched = site_properties.getProperty('types_not_searched', [])

    # portal_types = getToolByName(context, "portal_types")
    # types = portal_types.listContentTypes()

    # # Get list of content type ids which are not filtered out
    # prepared_types = [t for t in types if t not in not_searched]

    # # Return (id, title) pairs
    # types = [portal_types[id].title for id in prepared_types]
    # for ty in types:
    #     termsTypes.append(SimpleVocabulary.createTerm(ty))
    termsTypes.append(SimpleVocabulary.createTerm('News Item', 'News Item', "News Item"))
    termsTypes.append(SimpleVocabulary.createTerm('Event', 'Event', "Event"))
    return SimpleVocabulary(termsTypes)
directlyProvides(friendly_types, IContextSourceBinder)


class INewsCollectionPortlet(IPortletDataProvider):
    tags = schema.Set(title=_(u"Tags"),
                      description=_(u"categories"),
                      required=True,
                      value_type=schema.Choice(source=(groupTags))
                      )
    typetag = schema.Set(title=_(u"Type"),
                         description=_(u"Tipo"),
                         required=True,
                         value_type=schema.Choice(source=(friendly_types))
                         )


class Assignment (base.Assignment):
    implements(INewsCollectionPortlet)

    def __init__(self, tags, typetag):
        self.tags = tags
        self.typetag = typetag

    @property
    def title(self):
        return _(u"Categories")


class Renderer(base.Renderer):
    render = ViewPageTemplateFile('templates/newscollection.pt')

    def mostraTags(self):
        return self.data.tags

    def mostraTypeTags(self):
        return self.returnList(self.data.typetag)

    def _data(self):
        return self.data

    def returnList(self, elements):
        stringList = ''
        for i in elements:
            if len(stringList) > 0:
                stringList = stringList + ',' + i
            else:
                stringList = i
        return stringList


class AddForm(base.AddForm):
    form_fields = form.Fields(INewsCollectionPortlet)
    label = _(u"Add Tags portlet")
    description = _(u"This portlet lists tags by type and context.")

    def create(self, data):
        return Assignment(tags=data.get('tags'), typetag=data.get('typetag'))


class EditForm(base.EditForm):
    form_fields = form.Fields(INewsCollectionPortlet)
    label = _(u"Edit Tags Portlet")
    description = _(u"This portlet lists tags by type and context.")
