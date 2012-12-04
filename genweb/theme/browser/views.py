from five import grok
from Acquisition import aq_inner
from zope.interface import Interface
from zope.component import getMultiAdapter, queryMultiAdapter, getUtility, queryUtility
from zope.contentprovider import interfaces

from Products.CMFPlone import utils
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFPlone.browser.navigation import CatalogNavigationTabs
from Products.CMFPlone.browser.navigation import get_id, get_view_url

from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletManagerRenderer

from genweb.core.interfaces import IGenwebLayer, IHomePage
from genweb.theme.browser.interfaces import IGenwebTheme
from genweb.core.utils import genweb_config, pref_lang, portal_url
from genweb.portlets.browser.manager import ISpanStorage


class GWConfig(grok.View):
    grok.context(Interface)

    def render(self):
        return genweb_config()


class homePage(grok.View):
    """ This is the special view for the homepage containing support for the
        portlet managers provided by the package genweb.portlets.
        It's restrained to IGenwebTheme layer to prevent it will interfere with
        the one defined in the Genweb legacy theme (v4).
    """
    grok.context(IPloneSiteRoot)
    grok.layer(IGenwebTheme)

    def update(self):
        self.portlet_container = self.getPortletContainer()

    def getPortletContainer(self):
        context = aq_inner(self.context)
        pc = getToolByName(context, 'portal_catalog')
        result = pc.searchResults(object_provides=IHomePage.__identifier__,
                                  Language=pref_lang())
        if result:
            # Return the object without forcing a getObject()
            return getattr(context, result[0].id, context)
        else:
            # If this happens, it's bad. Implemented as a fallback
            return context

    def renderProviderByName(self, provider_name):
        provider = queryMultiAdapter(
            (self.portlet_container, self.request, self),
            interfaces.IContentProvider, provider_name)

        provider.update()

        return provider.render()

    def getSpanValueForManager(self, manager):
        portletManager = getUtility(IPortletManager, manager)
        spanstorage = getMultiAdapter((self.portlet_container, portletManager), ISpanStorage)
        span = spanstorage.span
        if span:
            return span
        else:
            return '4'

    def have_portlets(self, manager_name, view=None):
        """Determine whether a column should be shown. The left column is called
        plone.leftcolumn; the right column is called plone.rightcolumn.
        """
        force_disable = self.request.get('disable_' + manager_name, None)
        if force_disable is not None:
            return not bool(force_disable)

        context = self.portlet_container
        if view is None:
            view = self

        manager = queryUtility(IPortletManager, name=manager_name)
        if manager is None:
            return False

        renderer = queryMultiAdapter((context, self.request, view, manager), IPortletManagerRenderer)
        if renderer is None:
            renderer = getMultiAdapter((context, self.request, self, manager), IPortletManagerRenderer)

        return renderer.visible


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
