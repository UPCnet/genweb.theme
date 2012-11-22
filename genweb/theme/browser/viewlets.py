from five import grok
from Acquisition import aq_inner
from AccessControl import getSecurityManager
from zope.interface import Interface
from zope.component import getMultiAdapter
from zope.app.component.hooks import getSite

from plone.memoize.view import memoize_contextless

from Products.CMFCore import permissions
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.app.layout.viewlets.common import PersonalBarViewlet, GlobalSectionsViewlet, PathBarViewlet
from plone.app.layout.viewlets.common import SearchBoxViewlet, ManagePortletsFallbackViewlet
from plone.app.layout.viewlets.interfaces import IPortalTop, IPortalHeader, IBelowContent
from plone.app.layout.viewlets.interfaces import IPortalFooter
from Products.CMFPlone.interfaces import IPloneSiteRoot

from genweb.core.interfaces import IHomePage
from genweb.core.utils import genweb_config, havePermissionAtRoot, assignAltAcc, pref_lang

from genweb.theme.browser.interfaces import IGenwebTheme


grok.context(Interface)


class viewletBase(grok.Viewlet):
    grok.baseclass()

    @memoize_contextless
    def portal_url(self):
        return self.portal().absolute_url()

    @memoize_contextless
    def portal(self):
        return getSite()

    def genweb_config(self):
        return genweb_config()

    def pref_lang(self):
        """ Extracts the current language for the current user
        """
        lt = getToolByName(self.portal(), 'portal_languages')
        return lt.getPreferredLanguage()

    def assignAltAcc(self):
        return assignAltAcc(self)


class gwPersonalBarViewlet(PersonalBarViewlet, viewletBase):
    grok.name('genweb.personalbar')
    grok.viewletmanager(IPortalTop)
    grok.layer(IGenwebTheme)

    index = ViewPageTemplateFile('viewlets_templates/personal_bar.pt')

    def showRootFolderLink(self):
        return havePermissionAtRoot(self)

    def canManageSite(self):
        return getSecurityManager().checkPermission("plone.app.controlpanel.Overview", self.portal)


class gwHeader(viewletBase):
    grok.name('genweb.header')
    grok.template('header')
    grok.viewletmanager(IPortalHeader)
    grok.layer(IGenwebTheme)


class gwGlobalSectionsViewlet(GlobalSectionsViewlet, viewletBase):
    grok.name('genweb.globalsections')
    grok.viewletmanager(IPortalTop)
    grok.layer(IGenwebTheme)

    index = ViewPageTemplateFile('viewlets_templates/sections.pt')


class gwPathBarViewlet(PathBarViewlet, viewletBase):
    grok.name('genweb.pathbar')
    grok.viewletmanager(IPortalTop)
    grok.layer(IGenwebTheme)

    index = ViewPageTemplateFile('viewlets_templates/path_bar.pt')


class gwFooter(viewletBase):
    grok.name('genweb.footer')
    grok.template('footer')
    grok.viewletmanager(IPortalFooter)
    grok.layer(IGenwebTheme)


class gwSearchViewletManager(grok.ViewletManager):
    grok.context(Interface)
    grok.name('genweb.search_manager')


class gwSearchViewlet(SearchBoxViewlet, grok.Viewlet):
    grok.context(Interface)
    grok.viewletmanager(gwSearchViewletManager)
    grok.layer(IGenwebTheme)

    render = ViewPageTemplateFile('viewlets_templates/searchbox.pt')


class gwManagePortletsFallbackViewlet(ManagePortletsFallbackViewlet, grok.Viewlet):
    """ The override for the manage_portlets_fallback viewlet for IPloneSiteRoot
    """
    grok.context(IPloneSiteRoot)
    grok.name('plone.manage_portlets_fallback')
    grok.viewletmanager(IBelowContent)
    grok.layer(IGenwebTheme)

    render = ViewPageTemplateFile('viewlets_templates/manage_portlets_fallback.pt')

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

    def managePortletsURL(self):
        return "%s/%s" % (self.getPortletContainer().absolute_url(), '@@manage-homeportlets')

    def available(self):
        secman = getSecurityManager()
        if secman.checkPermission('Portlets: Manage portlets', self.context):
            return True
        else:
            return False
