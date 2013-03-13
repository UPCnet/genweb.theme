# -*- coding: utf-8 -*-
import re
from five import grok
from cgi import escape
from Acquisition import aq_inner
from AccessControl import getSecurityManager
from zope.interface import Interface
from zope.component import getMultiAdapter
from zope.component.hooks import getSite

from plone.memoize.view import memoize_contextless

from Products.CMFCore import permissions
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.app.layout.viewlets.common import PersonalBarViewlet, GlobalSectionsViewlet, PathBarViewlet
from plone.app.layout.viewlets.common import SearchBoxViewlet, TitleViewlet, ManagePortletsFallbackViewlet
from plone.app.layout.viewlets.interfaces import IHtmlHead, IPortalTop, IPortalHeader, IBelowContent
from plone.app.layout.viewlets.interfaces import IPortalFooter, IAboveContentTitle
from Products.CMFPlone.interfaces import IPloneSiteRoot

from Products.ATContentTypes.interface.news import IATNewsItem
from genweb.core.adapters import IImportant

from genweb.core import HAS_CAS
from genweb.core.interfaces import IHomePage
from genweb.theme.browser.interfaces import IHomePageView
from genweb.core.utils import genweb_config, havePermissionAtRoot, pref_lang

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


class gwPersonalBarViewlet(PersonalBarViewlet, viewletBase):
    grok.name('genweb.personalbar')
    grok.viewletmanager(IPortalTop)
    grok.layer(IGenwebTheme)

    index = ViewPageTemplateFile('viewlets_templates/personal_bar.pt')

    def showRootFolderLink(self):
        return havePermissionAtRoot(self)

    def canManageSite(self):
        return getSecurityManager().checkPermission("plone.app.controlpanel.Overview", self.portal)

    def getPortraitMini(self):
        pm = getToolByName(self.portal(), 'portal_membership')
        return pm.getPersonalPortrait().absolute_url()

    def logout_link(self):
        if HAS_CAS:
            return '{}/cas_logout'.format(self.portal_url)
        else:
            return '{}/logout'.format(self.portal_url)


class gwHeader(viewletBase):
    grok.name('genweb.header')
    grok.template('header')
    grok.viewletmanager(IPortalHeader)
    grok.layer(IGenwebTheme)

    def get_image_class(self):
        if self.genweb_config().treu_menu_horitzontal:
            # Is a L2 type
            return 'l2-image'
        else:
            return 'l3-image'

    def show_login(self):
        isAnon = getMultiAdapter((self.context, self.request), name='plone_portal_state').anonymous()
        return not self.genweb_config().amaga_identificacio and isAnon

    def show_directory(self):
        return self.genweb_config().directori_upc


class gwImportantNews(viewletBase):
    grok.name('genweb.important')
    grok.context(IATNewsItem)
    grok.template('important')
    grok.viewletmanager(IAboveContentTitle)
    grok.layer(IGenwebTheme)

    def permisos_important(self):
        #TODO: Comprovar que l'usuari tingui permisos per a marcar com a important
        return not IImportant(self.context).is_important and getSecurityManager().checkPermission("plone.app.controlpanel.Overview", self.portal)

    def permisos_notimportant(self):
        #TODO: Comprovar que l'usuari tingui permisos per a marcar com a notimportant
        return IImportant(self.context).is_important and getSecurityManager().checkPermission("plone.app.controlpanel.Overview", self.portal)

    def update(self):
        form = self.request.form
        if 'genweb.theme.viewlet.marcar_important' in form:
            IImportant(self.context).is_important = True
        if 'genweb.theme.viewlet.marcar_notimportant' in form:
            IImportant(self.context).is_important = False


class gwGlobalSectionsViewlet(GlobalSectionsViewlet, viewletBase):
    grok.name('genweb.globalsections')
    grok.viewletmanager(IPortalTop)
    grok.layer(IGenwebTheme)

    index = ViewPageTemplateFile('viewlets_templates/sections.pt')

    def show_menu(self):
        return not self.genweb_config().treu_menu_horitzontal and self.portal_tabs


class gwPathBarViewlet(PathBarViewlet, viewletBase):
    grok.name('genweb.pathbar')
    grok.viewletmanager(IPortalTop)
    grok.layer(IGenwebTheme)

    index = ViewPageTemplateFile('viewlets_templates/path_bar.pt')

    def paginaPrincipal(self):
        #TODO: Comprovar que no sigui la Pàgina Principal
        return IHomePageView.providedBy(self.view)


class gwFooter(viewletBase):
    grok.name('genweb.footer')
    grok.template('footer')
    grok.viewletmanager(IPortalFooter)
    grok.layer(IGenwebTheme)

    def getLinksPeu(self):
        """ links fixats per accessibilitat/rss/about """
        idioma = self.pref_lang()
        footer_links = {
            "ca": {
                "rss": "rss-ca",
                "about": "sobre-aquest-web",
                "accessibility": "accessibilitat"
            },
            "es": {
                "rss": "rss-es",
                "about": "sobre-esta-web",
                "accessibility": "accesibilidad"
            },
            "en": {
                "rss": "rss-en",
                "about": "about-this-web",
                "accessibility": "accessibility"
            },
            "zh": {
                "rss": "rss-en",
                "about": "about-this-web",
                "accessibility": "accessibility"
            },
        }

        return footer_links[idioma]


class gwSearchViewletManager(grok.ViewletManager):
    grok.context(Interface)
    grok.name('genweb.search_manager')


class gwSearchViewlet(SearchBoxViewlet, viewletBase):
    grok.context(Interface)
    grok.viewletmanager(gwSearchViewletManager)
    grok.layer(IGenwebTheme)

    render = ViewPageTemplateFile('viewlets_templates/searchbox.pt')


class gwManagePortletsFallbackViewlet(ManagePortletsFallbackViewlet, viewletBase):
    """ The override for the manage_portlets_fallback viewlet for IPloneSiteRoot
    """
    grok.context(IPloneSiteRoot)
    grok.name('plone.manage_portlets_fallback')
    grok.viewletmanager(IBelowContent)
    grok.layer(IGenwebTheme)

    render = ViewPageTemplateFile('viewlets_templates/manage_portlets_fallback.pt')

    def getPortletContainerPath(self):
        context = aq_inner(self.context)

        container_url = context.absolute_url()

        # Portlet container will be in the context,
        # Except in the portal root, when we look for an alternative
        if ISiteRoot.providedBy(self.context):
            pc = getToolByName(context, 'portal_catalog')
            result = pc.searchResults(object_provides=IHomePage.__identifier__,
                                      Language=pref_lang())
            if result:
                # Return the object without forcing a getObject()
                container_url = result[0].getURL()

        return container_url

    def managePortletsURL(self):
        return "%s/%s" % (self.getPortletContainerPath(), '@@manage-homeportlets')

    def available(self):
        secman = getSecurityManager()
        if secman.checkPermission('Portlets: Manage portlets', self.context):
            return True
        else:
            return False


class TitleViewlet(TitleViewlet, viewletBase):
    grok.context(Interface)
    grok.name('plone.htmlhead.title')
    grok.viewletmanager(IHtmlHead)
    grok.layer(IGenwebTheme)

    def update(self):
        portal_state = getMultiAdapter((self.context, self.request),
                                        name=u'plone_portal_state')
        context_state = getMultiAdapter((self.context, self.request),
                                         name=u'plone_context_state')
        page_title = escape(safe_unicode(context_state.object_title()))
        portal_title = escape(safe_unicode(portal_state.navigation_root_title()))

        genweb_title = getattr(self.genweb_config(), 'html_title_%s' % self.pref_lang(), 'Genweb UPC')
        if not genweb_title:
            genweb_title = 'Genweb UPC'
        genweb_title = escape(safe_unicode(re.sub(r'(<.*?>)', r'', genweb_title)))

        marca_UPC = escape(safe_unicode(u"UPC. Universitat Politècnica de Catalunya · BarcelonaTech"))

        if page_title == portal_title:
            self.site_title = u"%s &mdash; %s" % (genweb_title, marca_UPC)
        else:
            self.site_title = u"%s &mdash; %s &mdash; %s" % (page_title, genweb_title, marca_UPC)
