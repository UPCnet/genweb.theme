# -*- coding: utf-8 -*-
import requests
import socket
from five import grok
from plone import api
from time import time
from Acquisition import aq_inner
from AccessControl import getSecurityManager
from zope.interface import Interface
from zope.component import getMultiAdapter
from zope.security import checkPermission

from plone.memoize import ram
from plone.memoize.view import memoize_contextless

# from Products.CMFCore import permissions
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile as ZopeViewPageTemplateFile
from Products.Five.browser.metaconfigure import ViewMixinForTemplates
from Products.CMFPlone.interfaces import IPloneSiteRoot

from plone.app.layout.viewlets.common import PersonalBarViewlet, GlobalSectionsViewlet, PathBarViewlet
from plone.app.layout.viewlets.common import SearchBoxViewlet, ManagePortletsFallbackViewlet
from plone.app.layout.viewlets.interfaces import IPortalTop, IPortalHeader, IBelowContent
from plone.app.layout.viewlets.interfaces import IPortalFooter
from plone.app.layout.navigation.interfaces import INavigationRoot

from genweb.core import HAS_CAS
from genweb.core import HAS_PAM
from genweb.core.interfaces import IHomePage
from genweb.theme.browser.interfaces import IHomePageView
from genweb.core.utils import genweb_config
from genweb.core.utils import havePermissionAtRoot
from genweb.core.utils import pref_lang
from genweb.theme.browser.interfaces import IGenwebTheme
from genweb.core.browser.viewlets import gwCSSViewletManager
from genweb.core.browser.viewlets import baseResourcesViewlet

grok.context(Interface)


class gwCSSViewlet(baseResourcesViewlet):
    """ This is the CSS viewlet for Genweb """
    grok.context(Interface)
    grok.viewletmanager(gwCSSViewletManager)
    grok.layer(IGenwebTheme)

    resource_type = 'css'
    current_egg_name = 'genweb.theme'


class viewletBase(grok.Viewlet):
    grok.baseclass()

    @memoize_contextless
    def root_url(self):
        return self.portal().absolute_url()

    @memoize_contextless
    def portal(self):
        return api.portal.get()

    def genweb_config(self):
        return genweb_config()

    def pref_lang(self):
        """ Extracts the current language for the current user """
        lt = getToolByName(self.portal(), 'portal_languages')
        return lt.getPreferredLanguage()


class gwPersonalBarViewlet(PersonalBarViewlet, viewletBase):
    grok.name('genweb.personalbar')
    grok.viewletmanager(IPortalTop)
    grok.layer(IGenwebTheme)

    index = ViewPageTemplateFile('viewlets_templates/personal_bar.pt')

    def get_current_url(self):
        return self.context.absolute_url()

    def default_site_lang(self):
        pl = api.portal.get_tool(name='portal_languages')
        return pl.getDefaultLanguage()
        # return pl.getAvailableLanguages()[default_lang]['native']

    def get_available_langs(self):
        pl = api.portal.get_tool(name='portal_languages')
        langs_info = []
        for lang in pl.getSupportedLanguages():
            langs_info.append(dict(native=pl.getAvailableLanguages()[lang]['native'],
                                   code=lang))
        return langs_info

    def showRootFolderLink(self):
        return havePermissionAtRoot()

    def show_tools(self):
        portal = self.portal()
        user_global_roles = api.user.get_roles()
        user_local_roles_at_root = api.user.get_roles(obj=portal)

        # If user is Editor, WebMaster, Manager or Site Administrator globally,
        # inconditionally return True and stop bothering
        if 'Editor' in user_global_roles or 'Manager' in user_global_roles or 'Site Administrator' in user_global_roles or 'WebMaster' in user_global_roles:
            roles = dict(show=True, show_root_sharing=True, show_advanced=True, show_en=True, show_ca=True, show_es=True, show_shared=True)
            return roles

        if getattr(portal, 'ca', False):
            user_roles_at_ca_root = api.user.get_roles(obj=portal['ca'])
        else:
            user_roles_at_ca_root = []
        if getattr(portal, 'es', False):
            user_roles_at_es_root = api.user.get_roles(obj=portal['es'])
        else:
            user_roles_at_es_root = []
        if getattr(portal, 'en', False):
            user_roles_at_en_root = api.user.get_roles(obj=portal['en'])
        else:
            user_roles_at_en_root = []

        menus_to_show = dict(show=False, show_root_sharing=False, show_advanced=False, show_en=False, show_ca=False, show_es=False, show_shared=False)

        if 'Editor' in user_local_roles_at_root:
            menus_to_show['show'] = True
            menus_to_show['show_en'] = True
            menus_to_show['show_es'] = True
            menus_to_show['show_ca'] = True
            menus_to_show['show_shared'] = True
            menus_to_show['show_root_sharing'] = True
            menus_to_show['show_advanced'] = True

        if 'Editor' in user_roles_at_ca_root or 'Contributor' in user_roles_at_ca_root:
            menus_to_show['show'] = True
            menus_to_show['show_ca'] = True
            if 'ca' in self.context.Language():
                menus_to_show['show_shared'] = True

        if 'Editor' in user_roles_at_es_root or 'Contributor' in user_roles_at_es_root:
            menus_to_show['show'] = True
            menus_to_show['show_es'] = True
            if 'es' in self.context.Language():
                menus_to_show['show_shared'] = True

        if 'Editor' in user_roles_at_en_root or 'Contributor' in user_roles_at_en_root:
            menus_to_show['show'] = True
            menus_to_show['show_en'] = True
            if 'en' in self.context.Language():
                menus_to_show['show_shared'] = True

        return menus_to_show

    def canManageSite(self):
        return checkPermission("plone.app.controlpanel.Overview", self.portal())

    def getPortraitMini(self):
        pm = getToolByName(self.portal(), 'portal_membership')
        return pm.getPersonalPortrait().absolute_url()

    def logout_link(self):
        if HAS_CAS:
            return '{}/cas_logout'.format(self.root_url())
        else:
            return '{}/logout'.format(self.root_url())

    @ram.cache(lambda *args: time() // (60 * 60))
    def getNotificacionsGW(self):
        results = {}
        try:
            r = requests.get('https://www.upc.edu/content/index.php/ws/EinesGWv2', timeout=10)
            lang = self.pref_lang()
            if lang == 'ca':
                notificacions = r.json().get('ca')
            elif lang == 'es':
                notificacions = r.json().get('es')
            elif lang == 'en':
                notificacions = r.json().get('en')

            have_new = [notificacio for notificacio in notificacions if notificacio.get('nou')]
            results['nou'] = have_new and ' nou' or ''
            results['elements'] = notificacions
            return results
        except:
            return {}

    def forgeResizerURLCall(self):
        part1 = """<a class="button" data-text="Advanced bookmarklet" href="javascript:void((function(d){if(self!=top||d.getElementById('toolbar')&&d.getElementById('toolbar').getAttribute('data-resizer'))return false;d.write('<!DOCTYPE HTML><html style=&quot;opacity:0;&quot;><head><meta charset=&quot;utf-8&quot;/></head><body><a data-viewport=&quot;240x240&quot; data-icon=&quot;handy&quot;>Mobile</a><a data-viewport=&quot;320x480&quot; data-icon=&quot;mobile&quot;>Mobile (e.g. Apple iPhone)</a><a data-viewport=&quot;320x568&quot; data-icon=&quot;mobile&quot; data-version=&quot;5&quot;>Apple iPhone 5</a><a data-viewport=&quot;600x800&quot; data-icon=&quot;small-tablet&quot;>Small Tablet</a><a data-viewport=&quot;768x1024&quot; data-icon=&quot;tablet&quot;>Tablet (e.g. Apple iPad 2-3rd, mini)</a><a data-viewport=&quot;1024x768&quot; data-icon=&quot;display&quot; data-version=&quot;17″&quot;>17″ Display</a><a data-viewport=&quot;1280x800&quot; data-icon=&quot;notebook&quot;>Widescreen</a><a data-viewport=&quot;2560x1600&quot; data-icon=&quot;display&quot; data-version=&quot;30″&quot;>30″ Apple Cinema Display</a><script src=&quot;"""

        lang = self.pref_lang()
        if lang == 'ca':
            part2 = """/++genweb++static/js/resizer.min.js&quot;></script></body></html>')})(document));"><span class="pull-left">Vistes</span><i class="fontello-icon-mobile pull-left"></i><i class="fontello-icon-tablet pull-left"></i></a>"""
        if lang == 'es':
            part2 = """/++genweb++static/js/resizer.min.js&quot;></script></body></html>')})(document));"><span class="pull-left">Vistas</span><i class="fontello-icon-mobile pull-left"></i><i class="fontello-icon-tablet pull-left"></i></a>"""
        if lang == 'en':
            part2 = """/++genweb++static/js/resizer.min.js&quot;></script></body></html>')})(document));"><span class="pull-left">Views</span><i class="fontello-icon-mobile pull-left"></i><i class="fontello-icon-tablet pull-left"></i></a>"""

        return part1 + self.root_url() + part2


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

    def get_title(self):
        title = getattr(self.genweb_config(), 'html_title_{}'.format(self.pref_lang()))
        if title:
            return title
        else:
            return u''

    def is_logo_enabled(self):
        return self.genweb_config().right_logo_enabled

    def get_right_logo_alt(self):
        right_logo_alt = self.genweb_config().right_logo_alt
        return right_logo_alt if right_logo_alt else ""

    def is_pam_installed(self):
        return HAS_PAM

    def getCustomLink(self):
        """ Custom links """
        lang = self.pref_lang()
        custom_links = {
            "ca": {
                "cl_title": self.genweb_config().cl_title_ca,
                "url": self.genweb_config().cl_url_ca,
                "image": self.genweb_config().cl_img_ca,
                "oinw": self.genweb_config().cl_open_new_window_ca,
                "enable": self.genweb_config().cl_enable_ca,
            },
            "es": {
                "cl_title": self.genweb_config().cl_title_es,
                "url": self.genweb_config().cl_url_es,
                "image": self.genweb_config().cl_img_es,
                "oinw": self.genweb_config().cl_open_new_window_es,
                "enable": self.genweb_config().cl_enable_es,
            },
            "en": {
                "cl_title": self.genweb_config().cl_title_en,
                "url": self.genweb_config().cl_url_en,
                "image": self.genweb_config().cl_img_en,
                "oinw": self.genweb_config().cl_open_new_window_en,
                "enable": self.genweb_config().cl_enable_en,
            },
        }
        return custom_links[lang]

    def getHomeLink(self):
        lang = self.pref_lang()
        if lang == "ca":
            home_link = 'https://www.upc.edu/ca'
        elif lang == "es":
            home_link = 'https://www.upc.edu/es'
        elif lang == "en":
            home_link = 'https://www.upc.edu/en'
        else:
            home_link = 'https://www.upc.edu/ca'
        return home_link


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
        footer_links = {"ca": {"rss": "rss-ca",
                               "about": "sobre-aquest-web",
                               "accessibility": "accessibilitat",
                               "disclaimer": "https://www.upc.edu/ca/avis-legal"
                               },
                        "es": {"rss": "rss-es",
                               "about": "sobre-esta-web",
                               "accessibility": "accesibilidad",
                               "disclaimer": "https://www.upc.edu/es/aviso-legal"
                               },
                        "en": {"rss": "rss-en",
                               "about": "about-this-web",
                               "accessibility": "accessibility",
                               "disclaimer": "https://www.upc.edu/en/disclaimer"
                               },
                        "zh": {"rss": "rss-en",
                               "about": "about-this-web",
                               "accessibility": "accessibility",
                               "disclaimer": "https://www.upc.edu/en/disclaimer"
                               },
                        }
        return footer_links[idioma]

    def idioma_cookies(self):
        lang = self.pref_lang()

        if lang == 'ca':
            return 'https://www.upc.edu/ca/avis-legal/politica-de-cookies'
        if lang == 'es':
            return 'https://www.upc.edu/es/aviso-legal/politica-de-cookies'
        if lang == 'en':
            return 'https://www.upc.edu/en/disclaimer/cookies-policy'
        if lang == 'zh':
            return 'https://www.upc.edu/en/disclaimer/cookies-policy'
        if lang == '':
            return 'https://www.upc.edu/ca/avis-legal/politica-de-cookies'

    def checkIsAdmin(self):
        # Check if user has admin role to show the bottom information box
        # (only for managers)
        if api.user.is_anonymous():
            # is anon
            canViewContent = False
        else:
            # Is a validated user...
            username = api.user.get_current().getProperty('id')
            # get username
            roles = api.user.get_roles(username=username)
            # And check roles
            if 'Manager' in roles:
                canViewContent = True
            else:
                canViewContent = False
        return canViewContent

    def serverInfo(self):
        data = {}
        data['Hostname'] = socket.gethostname()
        data['IP'] = socket.gethostbyname(socket.gethostname())
        data['Port'] = self.request.environ['SERVER_PORT']
        data['Plone'] = api.env.plone_version()
        data['Zope'] = api.env.zope_version()

        in_debug_mode = api.env.debug_mode()
        if in_debug_mode:
            data['Debug'] = "-  Zope is in debug mode"
        else:
            data['Debug'] = ""

        return data

    def getHomeLink(self):
        lang = self.pref_lang()
        if lang == "ca":
            home_link = 'https://www.upc.edu/ca'
        elif lang == "es":
            home_link = 'https://www.upc.edu/es'
        elif lang == "en":
            home_link = 'https://www.upc.edu/en'
        else:
            home_link = 'https://www.upc.edu/ca'

        return home_link


class gwSearchViewletManager(grok.ViewletManager):
    grok.context(Interface)
    grok.name('genweb.search_manager')
    grok.layer(IGenwebTheme)


class gwSearchViewlet(SearchBoxViewlet, viewletBase):
    grok.context(Interface)
    grok.viewletmanager(gwSearchViewletManager)
    grok.layer(IGenwebTheme)

    render = ViewPageTemplateFile('viewlets_templates/searchbox.pt')


class gwManagePortletsFallbackViewletMixin(object):
    """ The override for the manage_portlets_fallback viewlet for IPloneSiteRoot """

    render = ViewPageTemplateFile('viewlets_templates/manage_portlets_fallback.pt')

    def getPortletContainerPath(self):
        context = aq_inner(self.context)

        container_url = context.absolute_url()

        # Portlet container will be in the context,
        # Except in the portal root, when we look for an alternative
        if INavigationRoot.providedBy(self.context):
            pc = getToolByName(context, 'portal_catalog')
            # Add the use case of mixin types of IHomepages. The main ones of a
            # non PAM-enabled site and the possible inner ones.
            result = pc.searchResults(object_provides=IHomePage.__identifier__,
                                      portal_type='Document',
                                      Language=pref_lang())

            if result:
                # Return the object without forcing a getObject()
                container_url = result[0].getURL()

        return container_url

    def managePortletsURL(self):
        return "%s/%s" % (self.getPortletContainerPath(), '@@manage-homeportlets')

    def available(self):
        secman = getSecurityManager()

        if secman.checkPermission('Genweb: Manage home portlets', self.context):
            return True
        else:
            return False


class gwManagePortletsFallbackViewletForPloneSiteRoot(gwManagePortletsFallbackViewletMixin, ManagePortletsFallbackViewlet, viewletBase):
    """ The override for the manage_portlets_fallback viewlet for IPloneSiteRoot """
    grok.context(INavigationRoot)
    grok.name('plone.manage_portlets_fallback')
    grok.viewletmanager(IBelowContent)
    grok.layer(IGenwebTheme)


class gwManagePortletsFallbackViewletForIHomePage(gwManagePortletsFallbackViewletMixin, ManagePortletsFallbackViewlet, viewletBase):
    """ The override for the manage_portlets_fallback viewlet for IHomePage """
    grok.context(IHomePage)
    grok.name('plone.manage_portlets_fallback')
    grok.viewletmanager(IBelowContent)
    grok.layer(IGenwebTheme)
