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
from plone.memoize import ram

from genweb.core.interfaces import IGenwebLayer, IHomePage
from Products.CMFCore.interfaces import ISiteRoot
from genweb.theme.browser.interfaces import IGenwebTheme, IHomePageView
from genweb.core.utils import genweb_config, pref_lang
from genweb.portlets.browser.manager import ISpanStorage

from scss import Scss
from genweb.theme.scss import dynamic_scss

from plone.formwidget.recaptcha.view import RecaptchaView, IRecaptchaInfo
from recaptcha.client.captcha import displayhtml


class GWConfig(grok.View):
    grok.context(Interface)

    def render(self):
        return genweb_config()


class HomePageBase(grok.View):
    """ Base methods for ease the extension of the genweb homePage view. Just
        define a new class inheriting from this one and redefine the basic
        grokkers like:

        class homePage(HomePageBase):
            grok.implements(IHomePageView)
            grok.context(IPloneSiteRoot)
            grok.require('genweb.authenticated')
            grok.layer(IUlearnTheme)

        Overriding the one in this module (homePage) with a more specific
        interface.
    """
    grok.baseclass()

    def update(self):
        self.portlet_container = self.getPortletContainer()

    def getPortletContainer(self):
        context = aq_inner(self.context)
        container = context

        # Portlet container will be in the context,
        # Except in the portal root, when we look for an alternative
        if ISiteRoot.providedBy(self.context):
            pc = getToolByName(context, 'portal_catalog')
            result = pc.searchResults(object_provides=IHomePage.__identifier__,
                                      Language=pref_lang())
            if result:
                # Return the object without forcing a getObject()
                container = getattr(context, result[0].id, context)

        return container

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


class homePage(HomePageBase):
    """ This is the special view for the homepage containing support for the
        portlet managers provided by the package genweb.portlets.
        It's restrained to IGenwebTheme layer to prevent it will interfere with
        the one defined in the Genweb legacy theme (v4).
    """
    grok.implements(IHomePageView)
    grok.context(IPloneSiteRoot)
    grok.layer(IGenwebTheme)


def _render_cachekey(method, self, especific1, especific2):
    """Cache by the two specific colors"""
    return (especific1, especific2)


class dynamicCSS(grok.View):
    grok.name('dynamic.css')
    grok.context(Interface)

    def update(self):
        self.especific1 = genweb_config().especific1
        self.especific2 = genweb_config().especific2

    def render(self):
        return self.compile_scss(self.especific1, self.especific2)

    @ram.cache(_render_cachekey)
    def compile_scss(self, especific1, especific2):
        css = Scss()
        return css.compile(dynamic_scss % (dict(especific1=especific1, especific2=especific2)))


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


class gwRecaptchaView(RecaptchaView, grok.View):
    grok.context(Interface)
    grok.name('recaptcha')
    grok.require('zope2.Public')
    grok.layer(IGenwebTheme)

    def render(self):
        pass

    def image_tag(self):
        lang = pref_lang()
        options = {"ca": """
                        <script type="text/javascript">
                            var RecaptchaOptions = {
                                    custom_translations : {
                                            instructions_visual : "Escriu les dues paraules:",
                                            instructions_audio : "Transcriu el que sentis:",
                                            play_again : "Torna a escoltar l'\u00e0udio",
                                            cant_hear_this : "Descarrega la pista en MP3",
                                            visual_challenge : "Modalitat visual",
                                            audio_challenge : "Modalitat auditiva",
                                            refresh_btn : "Demana dues noves paraules",
                                            help_btn : "Ajuda",
                                            incorrect_try_again : "Incorrecte. Torna-ho a provar.",
                                    },
                                    lang : '%s',
                                    theme : 'clean'
                                };
                        </script>
                        """ % lang,
                    "es": """
                        <script type="text/javascript">
                            var RecaptchaOptions = {
                                    lang : '%s',
                                    theme : 'clean'
                            };
                        </script>
                        """ % lang,
                    "en": """
                        <script type="text/javascript">
                            var RecaptchaOptions = {
                                    lang : '%s',
                                    theme : 'clean'
                            };
                        </script>
                        """ % lang
        }

        if not self.settings.public_key:
            raise ValueError('No recaptcha public key configured. Go to path/to/site/@@recaptcha-settings to configure.')
        use_ssl = self.request['SERVER_URL'].startswith('https://')
        error = IRecaptchaInfo(self.request).error
        return options.get(lang, '') + displayhtml(self.settings.public_key, use_ssl=use_ssl, error=error)
