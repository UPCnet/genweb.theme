from five import grok
from Acquisition import aq_inner, aq_chain
from AccessControl.SecurityManagement import getSecurityManager

from zope.interface import Interface
from zope.component import getMultiAdapter

from Products.CMFPlone import utils
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.browser.navigation import CatalogNavigationTabs
from Products.CMFPlone.browser.navigation import get_id, get_view_url

from genweb.theme.browser.interfaces import IGenwebTheme

from zope.interface import implements
from zope.component import getUtility
from zope.publisher.interfaces import IPublishTraverse, NotFound


from Products.Five import BrowserView
from Products.CMFCore.interfaces import ISiteRoot

from Products.CMFPlone.interfaces.factory import IFactoryTool
from borg.localrole.interfaces import IFactoryTempFolder
from plone.app.layout.navigation.interfaces import INavigationRoot
from plone.registry.interfaces import IRegistry

from plone.multilingual.interfaces import ITranslationManager
from plone.multilingual.interfaces import ITranslatable
from plone.app.multilingual.browser.controlpanel import IMultiLanguagePolicies
from .selector import addQuery
from .selector import NOT_TRANSLATED_YET_TEMPLATE


class universalLink(BrowserView):
    """ Redirects the user to the negotiated translated page
        based on the user preferences in the user's browser.
    """

    implements(IPublishTraverse)

    def __init__(self, context, request):
        super(universalLink, self).__init__(context, request)
        self.tg = None
        self.lang = None

    def publishTraverse(self, request, name):

        if self.tg is None:  # ../@@universal-link/translationgroup
            self.tg = name
        elif self.lang is None:  # ../@@universal-link/translationgroup/lang
            self.lang = name
        else:
            raise NotFound(self, name, request)

        return self

    def getDestination(self):
        # Look for the element
        ptool = getToolByName(self.context, 'portal_catalog')
        if self.lang:
            query = {'TranslationGroup': self.tg, 'Language': self.lang}
        else:
            # The negotiated language
            ltool = getToolByName(self.context, 'portal_languages')
            if len(ltool.getRequestLanguages()) > 0:
                language = ltool.getRequestLanguages()[0]
                query = {'TranslationGroup': self.tg, 'Language': language}
        results = ptool.searchResults(query)
        url = None
        if len(results) > 0:
            url = results[0].getURL()
        return url

    def __call__(self):
        url = self.getDestination()
        if not url:
            root = getToolByName(self.context, 'portal_url')
            url = root.url()
        self.request.RESPONSE.redirect(url)


class selector_view(universalLink):

    def getDialogDestination(self):
        """Get the "not translated yet" dialog URL.
        """
        state = getMultiAdapter(
            (self.context, self.request),
            name='plone_context_state'
        )
        dialog_view = NOT_TRANSLATED_YET_TEMPLATE
        postpath = False
        # The dialog view shouldn't appear on the site root
        # because that is untraslatable by default.
        # And since we are mapping the root on itself,
        # we also do postpath insertion (@@search case)
        if ISiteRoot.providedBy(self.context):
            dialog_view = ''
            postpath = True
        try:
            url = state.canonical_object_url()
        # XXX: this copied over from LinguaPlone, not sure this is still needed
        except AttributeError:
            url = self.context.absolute_url()
        return self.wrapDestination(url + dialog_view, postpath=postpath)

    def getParentChain(self, context):
        # XXX: switch it over to parent pointers if needed
        return aq_chain(context)

    def getClosestDestination(self):
        """Get the "closest translated object" URL.
        """
        # We sould travel the parent chain using the catalog here,
        # but I think using the acquisition chain is faster
        # (or well, __parent__ pointers) because the catalog
        # would require a lot of queries, while technically,
        # having done traversal up to this point you should
        # have the objects in memory already
        context = aq_inner(self.context)
        checkPermission = getSecurityManager().checkPermission
        chain = self.getParentChain(context)
        for item in chain:
            if ISiteRoot.providedBy(item):
                # We do not care to get a permission error
                # if the whole of the portal cannot be viewed.
                # Having a permission issue on the root is fine;
                # not so much for everything else so that is checked there
                return self.wrapDestination(item.absolute_url())
            elif IFactoryTempFolder.providedBy(item) or \
                    IFactoryTool.providedBy(item):
                # TempFolder or portal_factory, can't have a translation
                continue
            try:
                canonical = ITranslationManager(item)
            except TypeError:
                if not ITranslatable.providedBy(item):
                    # In case there it's not translatable go to parent
                    # This solves the problem when a parent is not ITranslatable
                    continue
                else:
                    raise
            translation = canonical.get_translation(self.lang)
            if INavigationRoot.providedBy(translation) or \
                    bool(checkPermission('View', translation)):
                # Not a direct translation, therefore no postpath
                # (the view might not exist on a different context)
                return self.wrapDestination(translation.absolute_url(),
                                            postpath=False)
        # Site root's the fallback
        root = getToolByName(self.context, 'portal_url')
        return self.wrapDestination(root.url(), postpath=False)

    def wrapDestination(self, url, postpath=True):
        """Fix the translation url appending the query
        and the eventual append path.
        """
        if postpath:
            url += self.request.form.get('post_path', '')
        return addQuery(
            self.request,
            url,
            exclude=('post_path')
        )

    def __call__(self):
        url = self.getDestination()
        if url:
            # We have a direct translation, full wrapping
            url = self.wrapDestination(url)
        else:
            registry = getUtility(IRegistry)
            policies = registry.forInterface(IMultiLanguagePolicies)
            if policies.selector_lookup_translations_policy == 'closest':
                url = self.getClosestDestination()
            else:
                url = self.getDialogDestination()
            # No wrapping cause that's up to the policies
            # (they should already have done that)
        self.request.RESPONSE.redirect(url)


class not_translated_yet(BrowserView):
    """ View to inform user that the view requested is not translated yet,
        and shows the already translated related content.
    """
    grok.context(Interface)
    grok.name('genweb.not_translated_yet')
    grok.require('zope2.View')
    grok.layer(IGenwebTheme)

    def already_translated(self):
        return ITranslationManager(self.context).get_translations().items()

    def has_any_translation(self):
        return len(ITranslationManager(self.context).get_translations().items()) > 1


class gwCatalogNavigationTabs(CatalogNavigationTabs):
    """ Customized navigation tabs generator to include review_state attribute
        in results.
    """
    def topLevelTabs(self, actions=None, category='portal_tabs'):
        context = aq_inner(self.context)

        mtool = getToolByName(context, 'portal_membership')
        member = mtool.getAuthenticatedMember().id

        portal_properties = getToolByName(context, 'portal_properties')
        self.navtree_properties = getattr(portal_properties,
                                          'navtree_properties')
        self.site_properties = getattr(portal_properties,
                                       'site_properties')
        self.portal_catalog = getToolByName(context, 'portal_catalog')

        if actions is None:
            context_state = getMultiAdapter((context, self.request),
                                            name=u'plone_context_state')
            actions = context_state.actions(category)

        # Build result dict
        result = []
        # first the actions
        if actions is not None:
            for actionInfo in actions:
                data = actionInfo.copy()
                data['name'] = data['title']
                result.append(data)

        # check whether we only want actions
        if self.site_properties.getProperty('disable_folder_sections', False):
            return result

        query = self._getNavQuery()

        rawresult = self.portal_catalog.searchResults(query)

        def get_link_url(item):
            linkremote = item.getRemoteUrl and not member == item.Creator
            if linkremote:
                return (get_id(item), item.getRemoteUrl)
            else:
                return False

        # now add the content to results
        idsNotToList = self.navtree_properties.getProperty('idsNotToList', ())
        for item in rawresult:
            if not (item.getId in idsNotToList or item.exclude_from_nav):
                id, item_url = get_link_url(item) or get_view_url(item)
                data = {'name': utils.pretty_title_or_id(context, item),
                        'id': item.getId,
                        'url': item_url,
                        'description': item.Description,
                        'review_state': item.review_state}
                result.append(data)

        return result
