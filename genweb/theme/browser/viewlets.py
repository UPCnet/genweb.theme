# -*- coding: utf-8 -*-
import re
import requests
from five import grok
from time import time
from cgi import escape
from Acquisition import aq_inner
from AccessControl import getSecurityManager
from zope.interface import Interface
from zope.component import getMultiAdapter
from zope.component.hooks import getSite
from zope.security import checkPermission

from plone.memoize import ram
from plone.memoize.view import memoize_contextless

# from Products.CMFCore import permissions
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile as ZopeViewPageTemplateFile
from Products.Five.browser.metaconfigure import ViewMixinForTemplates

from plone.app.layout.viewlets.common import PersonalBarViewlet, GlobalSectionsViewlet, PathBarViewlet
from plone.app.layout.viewlets.common import SearchBoxViewlet, TitleViewlet, ManagePortletsFallbackViewlet
from plone.app.layout.viewlets.interfaces import IHtmlHead, IPortalTop, IPortalHeader, IBelowContent
from plone.app.layout.viewlets.interfaces import IPortalFooter, IAboveContentTitle
from Products.CMFPlone.interfaces import IPloneSiteRoot

from Products.ATContentTypes.interface.news import IATNewsItem
from genweb.core.adapters import IImportant

from zope.annotation.interfaces import IAnnotations
from Products.ATContentTypes.interfaces.event import IATEvent

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

    def default_site_lang(self):
        lang = self.portal().portal_properties.site_properties.default_language
        if lang == 'ca':
            return 'Català'
        elif lang == 'es':
            return 'Español'
        elif lang == 'en':
            return 'Engish'
        else:
            return lang

    def showRootFolderLink(self):
        return havePermissionAtRoot()

    def canManageSite(self):
        return checkPermission("plone.app.controlpanel.Overview", self.portal())

    def getPortraitMini(self):
        pm = getToolByName(self.portal(), 'portal_membership')
        return pm.getPersonalPortrait().absolute_url()

    def logout_link(self):
        if HAS_CAS:
            return '{}/cas_logout'.format(self.portal_url)
        else:
            return '{}/logout'.format(self.portal_url)

    @ram.cache(lambda *args: time() // (60 * 60))
    def getNotificacionsGW(self):
        results = {}
        try:
            r = requests.get('http://www.upc.edu/ws/genweb/EinesGWv1.php', timeout=10)
            notificacions = r.json().get('items')
            have_new = [notificacio for notificacio in notificacions if notificacio.get('nou')]
            results['nou'] = have_new and ' nou' or ''
            results['elements'] = notificacions
            return results
        except:
            return {}

    def forgeResizerURLCall(self):

        resizer_string_header = "javascript:void((function(d){if(self!=top||d.getElementById('toolbar')&&d.getElementById('toolbar').getAttribute('data-resizer'))return%20false;d.write('<!DOCTYPE%20HTML><html%20style=\'opacity:0;\'><head><meta%20charset=\'utf-8\'/></head><body><a%20data-viewport=\'320x480\'%20data-icon=\'mobile\'>Mobile%20(e.g.%20Apple%20iPhone)</a><a%20data-viewport=\'600x800\'%20data-icon=\'small-tablet\'>Small%20Tablet</a><a%20data-viewport=\'768x1024\'%20data-icon=\'tablet\'>Tablet%20(e.g.%20Apple%20iPad%202-3rd,%20mini)</a><a%20data-viewport=\'1024x768\'%20data-icon=\'display\'%20data-version=\'17%E2%80%B3\'>17%E2%80%B3%20Display</a><a%20data-viewport=\'1280x800\'%20data-icon=\'notebook\'>Widescreen</a><script%20src=\'"
        resizer_js = '{}/++genweb++static/js/resizer.min.js'.format(self.portal_url)
        resizer_string_tail = "\'></script></body></html>')})(document));"

        return '{}{}{}'.format(resizer_string_header, resizer_js, resizer_string_tail)


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

    # def show_directory(self):
    #     return self.genweb_config().directori_upc

    def show_directory(self):
        show_general = self.genweb_config().directori_upc
        return show_general

    def show_directory_filtered(self):
        show_filtered = self.genweb_config().directori_filtrat
        return show_filtered

    def getURLDirectori(self, codi):
        if codi:
            return "http://directori.upc.edu/directori/dadesUE.jsp?id=%s" % codi
        else:
            return "http://directori.upc.edu"


class gwImportantNews(viewletBase):
    grok.name('genweb.important')
    grok.context(IATNewsItem)
    grok.template('important')
    grok.viewletmanager(IAboveContentTitle)
    grok.layer(IGenwebTheme)

    def permisos_important(self):
        #TODO: Comprovar que l'usuari tingui permisos per a marcar com a important
        return not IImportant(self.context).is_important and checkPermission("plone.app.controlpanel.Overview", self.portal())

    def permisos_notimportant(self):
        #TODO: Comprovar que l'usuari tingui permisos per a marcar com a notimportant
        return IImportant(self.context).is_important and checkPermission("plone.app.controlpanel.Overview", self.portal())

    def update(self):
        form = self.request.form
        if 'genweb.theme.viewlet.marcar_important' in form:
            IImportant(self.context).is_important = True
        if 'genweb.theme.viewlet.marcar_notimportant' in form:
            IImportant(self.context).is_important = False


class gwSendEvent(viewletBase):
    grok.name('genweb.sendevent')
    grok.context(IATEvent)
    grok.template('send_event')
    grok.viewletmanager(IAboveContentTitle)
    grok.layer(IGenwebTheme)

    def isEventSent(self):
        """
        """
        context = self.context
        annotations = IAnnotations(context)
        if 'eventsent' in annotations:
            return True
        else:
            return False

    def canManageSite(self):
        return checkPermission("plone.app.controlpanel.Overview", self.portal())

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
        return IHomePageView.providedBy(self.view) and IPloneSiteRoot.providedBy(self.context)


class gwFooter(viewletBase):
    grok.name('genweb.footer')
    grok.template('footer')
    grok.viewletmanager(IPortalFooter)
    grok.layer(IGenwebTheme)

    def get_go_to_top_link(self, template, view):

        name = ''
        if isinstance(template, ViewPageTemplateFile) or \
           isinstance(template, ZopeViewPageTemplateFile) or \
           isinstance(template, ViewMixinForTemplates):
            # Browser view
            name = view.__name__
        else:
            if hasattr(template, 'getId'):
                name = template.getId()

        context_state = getMultiAdapter(
            (aq_inner(self.context), self.request),
            name=u'plone_context_state')

        if name and name in context_state.current_base_url():
            # We are dealing with a view
            if '@@' in context_state.current_page_url():
                name = '@@{}'.format(name)

            return '{}/{}#portal-header'.format(self.context.absolute_url(), name)
        else:
            # We have a bare content
            return '{}#portal-header'.format(self.context.absolute_url())

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
        if IPloneSiteRoot.providedBy(self.context):
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
