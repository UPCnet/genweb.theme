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
from plone.app.layout.viewlets.common import ManagePortletsFallbackViewlet, ContentViewsViewlet
from plone.app.layout.viewlets.interfaces import IPortalTop, IPortalHeader, IBelowContent
from plone.app.layout.viewlets.interfaces import IPortalFooter
from plone.app.i18n.locales.browser.selector import LanguageSelector
from Products.CMFPlone.interfaces import IPloneSiteRoot

from genweb.core.utils import gw_config, havePermissionAtRoot, assignAltAcc
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

    def gw_config(self):
        return gw_config()

    def pref_lang(self):
        """Funcio que extreu idioma actiu
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


class gwHeader(LanguageSelector, viewletBase):
    grok.name('genweb.header')
    grok.template('header')
    grok.viewletmanager(IPortalHeader)
    grok.layer(IGenwebTheme)

    def languages(self):
        languages_info = super(LanguageSelectorViewlet, self).languages()
        results = []
        translation_group = queryAdapter(self.context, ITG)
        if translation_group is None:
            translation_group = NOTG
        for lang_info in languages_info:
            # Avoid to modify the original language dict
            data = lang_info.copy()
            data['translated'] = True
            query_extras = {
                'set_language': data['code'],
            }
            post_path = getPostPath(self.context, self.request)
            if post_path:
                query_extras['post_path'] = post_path
            data['url'] = addQuery(
                self.request,
                self.context.absolute_url().rstrip("/") + \
                    "/@@multilingual-selector/%s/%s" % (
                        translation_group,
                        lang_info['code']
                    ),
                **query_extras
            )
            results.append(data)
        return results


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
