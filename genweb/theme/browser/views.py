# -*- coding: utf-8 -*-
from five import grok
from plone import api
from Acquisition import aq_inner
from DateTime.DateTime import DateTime
from scss import Scss

from zope.interface import Interface
from zope.contentprovider import interfaces
from zope.annotation.interfaces import IAnnotations
from zope.component import getMultiAdapter, queryMultiAdapter, getUtility, queryUtility
from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile as ZopeViewPageTemplateFile

from plone.batching import Batch
from plone.registry.interfaces import IRegistry
from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletManagerRenderer
from plone.app.layout.globals.layout import LayoutPolicy
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.formwidget.recaptcha.view import RecaptchaView, IRecaptchaInfo
from plone.app.contenttypes.interfaces import IEvent
from plone.app.layout.navigation.interfaces import INavigationRoot

from Products.CMFPlone import utils
from Products.CMFPlone.utils import safe_unicode
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.PythonScripts.standard import url_quote_plus
from Products.statusmessages.interfaces import IStatusMessage
# from Products.ATContentTypes.interfaces.event import IATEvent
from Products.CMFPlone.browser.navtree import getNavigationRoot
from Products.CMFPlone.browser.navigation import CatalogNavigationTabs
from Products.CMFPlone.browser.navigation import get_id, get_view_url
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from recaptcha.client.captcha import displayhtml
from collective.recaptcha.view import RecaptchaView as CollectiveRecaptchaView

from genweb.core.interfaces import IHomePage
from genweb.core.utils import genweb_config, pref_lang
from genweb.core.interfaces import INewsFolder

from genweb.theme.browser.interfaces import IGenwebTheme, IHomePageView

from genweb.portlets.browser.manager import ISpanStorage

from Products.CMFCore.interfaces import IFolderish
from plone.memoize.view import memoize
from plone.memoize import ram

import pkg_resources
import json
import scss

grok.templatedir("views_templates")


class GWConfig(grok.View):
    grok.context(Interface)
    grok.layer(IGenwebTheme)

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
        if INavigationRoot.providedBy(self.context):
            pc = getToolByName(context, 'portal_catalog')
            # Add the use case of mixin types of IHomepages. The main ones of a
            # non PAM-enabled site and the possible inner ones.
            result = pc.searchResults(object_provides=IHomePage.__identifier__,
                                      portal_type='Document',
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

    def is_visible(self):
        """ This method lookup for the physical welcome page and checks if the
            user has the permission to view it. If it doesn't raises an
            unauthorized (login)
        """
        portal = api.portal.get()
        pc = api.portal.get_tool('portal_catalog')
        result = pc.unrestrictedSearchResults(object_provides=IHomePage.__identifier__,
                                              Language=pref_lang())
        if result:
            portal.restrictedTraverse(result[0].getPath())
            return True
        else:
            return False


class homePage(HomePageBase):
    """ This is the special view for the homepage containing support for the
        portlet managers provided by the package genweb.portlets.
        It's restrained to IGenwebTheme layer to prevent it will interfere with
        the one defined in the Genweb legacy theme (v3.5).
    """
    grok.name('homepage')
    grok.implements(IHomePageView)
    grok.context(INavigationRoot)
    grok.layer(IGenwebTheme)


class subHomePage(HomePageBase):
    """ This is the special view for the subhomepage containing support for the
        portlet managers provided by the package genweb.portlets.
        This is the PAM aware default LRF homepage view.
        It is also used in IFolderish (DX and AT) content for use in inner landing
        pages.
    """
    grok.name('homepage')
    grok.implements(IHomePageView)
    grok.context(IFolderish)
    grok.layer(IGenwebTheme)


def _render_cachekey(method, self, especific1, especific2):
    """Cache by the two specific colors"""
    return (especific1, especific2)


class TypeAheadSearch(grok.View):
    grok.name('gw_type_ahead_search')
    grok.context(Interface)
    grok.layer(IGenwebTheme)

    def render(self):
        # We set the parameters sent in livesearch using the old way.
        q = self.request['q']

        limit = 10
        path = None

        ploneUtils = getToolByName(self.context, 'plone_utils')
        portal_url = getToolByName(self.context, 'portal_url')()
        pretty_title_or_id = ploneUtils.pretty_title_or_id
        portalProperties = getToolByName(self.context, 'portal_properties')
        siteProperties = getattr(portalProperties, 'site_properties', None)
        useViewAction = []
        if siteProperties is not None:
            useViewAction = siteProperties.getProperty('typesUseViewActionInListings', [])

        # SIMPLE CONFIGURATION
        MAX_TITLE = 40
        MAX_DESCRIPTION = 80

        # generate a result set for the query
        catalog = self.context.portal_catalog

        friendly_types = ploneUtils.getUserFriendlyTypes()

        def quotestring(s):
            return '"%s"' % s

        def quote_bad_chars(s):
            bad_chars = ["(", ")"]
            for char in bad_chars:
                s = s.replace(char, quotestring(char))
            return s

        multispace = u'\u3000'.encode('utf-8')
        for char in ('?', '-', '+', '*', multispace):
            q = q.replace(char, ' ')
        r = q.split()
        r = " AND ".join(r)
        r = quote_bad_chars(r) + '*'
        searchterms = url_quote_plus(r)

        params = {'SearchableText': r,
                  'portal_type': friendly_types,
                  'sort_limit': limit + 1}

        if path is None:
            # useful for subsides
            params['path'] = getNavigationRoot(self.context)
        else:
            params['path'] = path

        params["Language"] = pref_lang()
        # search limit+1 results to know if limit is exceeded
        results = catalog(**params)

        REQUEST = self.context.REQUEST
        RESPONSE = REQUEST.RESPONSE
        RESPONSE.setHeader('Content-Type', 'application/json')

        label_show_all = _('label_show_all', default='Show all items')

        ts = getToolByName(self.context, 'translation_service')

        queryElements = []

        if results:
            # TODO: We have to build a JSON with the desired parameters.
            for result in results[:limit]:
                # Calculate icon replacing '.' per '-' as '.' in portal_types break CSS
                icon = result.portal_type.lower().replace(".", "-")
                itemUrl = result.getURL()
                if result.portal_type in useViewAction:
                    itemUrl += '/view'

                full_title = safe_unicode(pretty_title_or_id(result))
                if len(full_title) > MAX_TITLE:
                    display_title = ''.join((full_title[:MAX_TITLE], '...'))
                else:
                    display_title = full_title

                full_title = full_title.replace('"', '&quot;')

                display_description = safe_unicode(result.Description)
                if len(display_description) > MAX_DESCRIPTION:
                    display_description = ''.join(
                        (display_description[:MAX_DESCRIPTION], '...'))

                # We build the dictionary element with the desired parameters and we add it to the queryElements array.
                queryElement = {'class': '', 'title': display_title, 'description': display_description, 'itemUrl': itemUrl, 'icon': icon}
                queryElements.append(queryElement)

            if len(results) > limit:
                #We have to add here an element to the JSON in case there is too many elements.
                searchquery = '/@@search?SearchableText=%s&path=%s' \
                    % (searchterms, params['path'])
                too_many_results = {'class': 'with-separator', 'title': ts.translate(label_show_all, context=REQUEST), 'description': '', 'itemUrl': portal_url + searchquery, 'icon': ''}
                queryElements.append(too_many_results)

        return json.dumps(queryElements)


class dynamicCSS(grok.View):
    grok.name('dynamic.css')
    grok.context(Interface)
    grok.layer(IGenwebTheme)

    def update(self):
        self.especific1 = genweb_config().especific1
        self.especific2 = genweb_config().especific2

    def render(self):
        self.request.response.setHeader('Content-Type', 'text/css')
        self.request.response.addHeader('Cache-Control', 'must-revalidate, max-age=0, no-cache, no-store')
        if self.especific1 and self.especific2:
            return self.compile_scss(especific1=self.especific1, especific2=self.especific2)
        else:
            default = '@import "{}/genwebcustom.css";'.format(api.portal.get().absolute_url())
            return default

    @ram.cache(_render_cachekey)
    def compile_scss(self, **kwargs):
        genwebthemeegg = pkg_resources.get_distribution('genweb.theme')

        scssfile = open('{}/genweb/theme/scss/_dynamic.scss'.format(genwebthemeegg.location))

        settings = dict(especific1=self.especific1,
                        especific2=self.especific2,
                        portal_url=api.portal.get().absolute_url())

        variables_scss = """

        $genwebPrimary: {especific1};
        $genwebTitles: {especific2};

        @import "{portal_url}/genwebcustom.css";

        """.format(**settings)

        scss.config.LOAD_PATHS = [
            '{}/genweb/theme/bootstrap/scss/compass_twitter_bootstrap'.format(genwebthemeegg.location)
        ]

        css = Scss(scss_opts={
                   'compress': False,
                   'debug_info': False,
                   })

        dynamic_scss = ''.join([variables_scss, scssfile.read()])

        return css.compile(dynamic_scss)


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


class gwLayoutPolicy(LayoutPolicy):
    """ Customized plone-layout view """

    def bodyClass(self, template, view):
        """
        Returns the CSS class to be used on the body tag.

        Included body classes
        - template name: template-{}
        - portal type: portaltype-{}
        - navigation root: site-{}
        - section: section-{}
            - only the first section
        - section structure
            - a class for every container in the tree
        - hide icons: icons-on
        """
        context = self.context
        portal_state = getMultiAdapter(
            (context, self.request), name=u'plone_portal_state')
        normalizer = queryUtility(IIDNormalizer)

        # template class (required)
        name = ''
        if isinstance(template, ViewPageTemplateFile) or \
           isinstance(template, ZopeViewPageTemplateFile):
            # Browser view
            name = view.__name__
        else:
            if hasattr(template, 'getId'):
                name = template.getId()
        name = normalizer.normalize(name)
        body_class = 'template-%s' % name

        # portal type class (optional)
        portal_type = normalizer.normalize(context.portal_type)
        if portal_type:
            body_class += " portaltype-%s" % portal_type

        # section class (optional)
        navroot = portal_state.navigation_root()
        body_class += " site-%s" % navroot.getId()

        contentPath = context.getPhysicalPath()[
            len(navroot.getPhysicalPath()):]
        if contentPath:
            body_class += " section-%s" % contentPath[0]
            # skip first section since we already have that...
            if len(contentPath) > 1:
                registry = getUtility(IRegistry)
                try:
                    depth = registry[
                        'plone.app.layout.globals.bodyClass.depth']
                except KeyError:
                    depth = 4
                if depth > 1:
                    classes = ['subsection-%s' % contentPath[1]]
                    for section in contentPath[2:depth]:
                        classes.append('-'.join([classes[-1], section]))
                    body_class += " %s" % ' '.join(classes)

        # class for hiding icons (optional)
        if self.icons_visible():
            body_class += ' icons-on'
        else:
            body_class += ' icons-off'

        # class for user roles
        membership = getToolByName(context, "portal_membership")
        if membership.isAnonymousUser():
            body_class += ' userrole-anonymous'
        else:
            user = membership.getAuthenticatedMember()
            for role in user.getRolesInContext(self.context):
                body_class += ' userrole-' + role.lower()

        return body_class


class gwRecaptchaView(RecaptchaView, grok.View):
    """ Override of the original plone.formwidget.recaptcha view to match style
        and language options """
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


class gwCollectiveRecaptchaView(CollectiveRecaptchaView, grok.View):
    """ Override of the original collective.recaptcha view to match style
        and language options """
    grok.context(Interface)
    grok.name('captcha')
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


class gwSendEventView(grok.View):
    grok.context(IEvent)
    grok.name('send-event')
    grok.require('cmf.AddPortalContent')
    grok.layer(IGenwebTheme)

    def render(self):

        context = aq_inner(self.context)
        annotations = IAnnotations(context)
        event_title = context.Title()
        event_start = context.startDate
        event_day = DateTime.day(event_start)
        event_month = DateTime.month(event_start)
        event_year = DateTime.year(event_start)
        event_hour = DateTime.Time(event_start)
        event_link = context.absolute_url()
        mailhost = getToolByName(context, 'MailHost')
        urltool = getToolByName(context, 'portal_url')
        portal = urltool.getPortalObject()
        email_charset = portal.getProperty('email_charset')
        to_address = 'info@upc.edu'
        from_name = portal.getProperty('email_from_name')
        from_address = portal.getProperty('email_from_address')
        titulo_web = portal.getProperty('title')
        mtool = self.context.portal_membership
        userid = mtool.getAuthenticatedMember().id
        source = "%s <%s>" % (from_name, from_address)
        subject = "[Nou esdeveniment] %s" % (titulo_web)
        message = MESSAGE_TEMPLATE % dict(titolGW=titulo_web,
                                          titleEvent=event_title,
                                          dayEvent=event_day,
                                          monthEvent=event_month,
                                          yearEvent=event_year,
                                          hourEvent=event_hour,
                                          linkEvent=event_link,
                                          from_address=from_address,
                                          from_name=from_name,
                                          user_name=userid)

        mailhost.secureSend(message, to_address, source,
                            subject=subject, subtype='plain',
                            charset=email_charset, debug=False,
                            )

        if 'eventsent' not in annotations:
            annotations['eventsent'] = True

        # confirm = _(u"Mail sent.")
        confirm = _(u"Gràcies per la vostra col·laboració. Les dades de l\'activitat s\'han enviat correctament i seran publicades com més aviat millor.")
        IStatusMessage(self.request).addStatusMessage(confirm, type='info')
        self.request.response.redirect(self.context.absolute_url())


class newsCollectionView(grok.View):
    grok.context(IFolderish)
    grok.name('newscollection_view')
    grok.template("newscollectionview")
    grok.require('zope2.View')
    grok.layer(IGenwebTheme)

    def published_news_items(self):
        return self._data()

    @memoize
    def _data(self):
        context = aq_inner(self.context)
        catalog = getToolByName(context, 'portal_catalog')
        state = ['published', 'intranet']
        results = catalog(portal_type=('News Item'),
                       review_state=state,
                       is_important=True,
                       Language=pref_lang(),
                       sort_on="getObjPositionInParent")
        results = [a for a in results]
        results2 = catalog(portal_type=('News Item', 'Link'),
                   review_state=state,
                   is_important=False,
                   Language=pref_lang(),
                   sort_on=('Date'),
                   sort_order='reverse')
        results3 = []
        path_folder_news = self.all_news_link()
        for brain in results2:
            brain_url = brain.getURL()
            brain_type = brain.Type
            if brain_type == 'Link' and brain_url.startswith(path_folder_news) or brain_type == 'News Item':
                results3.append(brain)
        return results + results3

    def all_news_link(self):
        portal = api.portal.get()
        pc = api.portal.get_tool('portal_catalog')
        news_folder = pc.searchResults(object_provides=INewsFolder.__identifier__,
                                       Language=pref_lang())

        if news_folder:
            return '%s' % news_folder[0].getURL()
        else:
            return '%s/news_listing' % portal.absolute_url()


class ContactFeedback(grok.View):
    grok.name('contact_feedback')
    grok.context(INavigationRoot)
    grok.template("contact_feedback")
    grok.require('zope2.View')
    grok.layer(IGenwebTheme)


class FilteredContentsSearchView(grok.View):
    """ Filtered content search view for every folder. """
    grok.name('filtered_contents_search_view')
    grok.context(Interface)
    grok.require('genweb.member')
    grok.template('filtered_contents_search')
    grok.layer(IGenwebTheme)

    def update(self):
        self.query = self.request.form.get('q', '')
        if self.request.form.get('t', ''):
            self.tags = [v for v in self.request.form.get('t').split(',')]
        else:
            self.tags = []

    def get_batched_contenttags(self, query=None, batch=True, b_size=10, b_start=0):
        pc = getToolByName(self.context, "portal_catalog")
        path = self.context.getPhysicalPath()
        path = "/".join(path)
        r_results = pc.searchResults(path=path)
        batch = Batch(r_results, b_size, b_start)
        return batch

    def get_contenttags_by_query(self):
        pc = getToolByName(self.context, "portal_catalog")
        path = self.context.getPhysicalPath()
        path = "/".join(path)

        def quotestring(s):
            return '"%s"' % s

        def quote_bad_chars(s):
            bad_chars = ["(", ")"]
            for char in bad_chars:
                s = s.replace(char, quotestring(char))
            return s

        if not self.query and not self.tags:
            return self.getContent()

        if not self.query == '':
            multispace = u'\u3000'.encode('utf-8')
            for char in ('?', '-', '+', '*', multispace):
                self.query = self.query.replace(char, ' ')

            query = self.query.split()
            query = " AND ".join(query)
            query = quote_bad_chars(query) + '*'

            if self.tags:
                r_results = pc.searchResults(path=path,
                                             SearchableText=query,
                                             Subject={'query': self.tags, 'operator': 'and'})
            else:
                r_results = pc.searchResults(path=path,
                                             SearchableText=query)

            return r_results
        else:
            r_results = pc.searchResults(path=path,
                                         Subject={'query': self.tags, 'operator': 'and'})

            return r_results
            # return self.get_batched_contenttags(query=None, batch=True, b_size=10, b_start=0)

    def get_tags_by_query(self):
        pc = getToolByName(self.context, "portal_catalog")

        def quotestring(s):
            return '"%s"' % s

        def quote_bad_chars(s):
            bad_chars = ["(", ")"]
            for char in bad_chars:
                s = s.replace(char, quotestring(char))
            return s

        if not self.query == '':
            multispace = u'\u3000'.encode('utf-8')
            for char in ('?', '-', '+', '*', multispace):
                self.query = self.query.replace(char, ' ')

            query = self.query.split()
            query = " AND ".join(query)
            query = quote_bad_chars(query)
            path = self.context.absolute_url_path()

            r_results = pc.searchResults(path=path,
                                         Subject=query)

            return r_results
        else:
            return self.get_batched_contenttags(query=None, batch=True, b_size=10, b_start=0)

    def get_container_path(self):
        return self.context.absolute_url()

    def getContent(self):
        portal = api.portal.get()
        catalog = getToolByName(portal, 'portal_catalog')
        path = self.context.getPhysicalPath()
        path = "/".join(path)

        items = catalog.searchResults(path={'query': path, 'depth': 1},
                                      sort_on='getObjPositionInParent')

        return items


class SearchFilteredContentAjax(FilteredContentsSearchView):
    """ Ajax helper for filtered content search view for every folder. """
    grok.name('search_filtered_content')
    grok.context(Interface)
    grok.template('filtered_contents_search_ajax')
    grok.layer(IGenwebTheme)


class ImagesGalleryFolderView(grok.View):
    """ Filtered content search view for every folder. """
    grok.name('images_gallery_folder_view')
    grok.context(Interface)
    grok.require('genweb.member')
    grok.template('images_gallery_folder')
    grok.layer(IGenwebTheme)

    def get_images(self):
        pc = api.portal.get_tool(name='portal_catalog')
        path = '/'.join(self.context.getPhysicalPath())
        return pc.searchResults(portal_type='Image',
                                path={'query': path})


class FolderIndexView(grok.View):
    """ Render the title of items and its children
    """

    # number of levels to show, if greater than 3 should modify template
    MAX_LEVEL = 3

    grok.name(_(u'folder_index_view'))
    grok.template('folder_index_view')
    grok.context(IFolderish)
    grok.layer(IGenwebTheme)
    grok.require('zope2.View')

    def update(self):
        self.theme = 'Genweb'

    def genwebTheme(self):
        return self.theme == 'Genweb'

    def upcTheme(self):
        return self.theme == 'UPC'

    def items(self):
        return self._data()

    @memoize
    def _data(self):
        context = aq_inner(self.context)
        self.catalog = getToolByName(context, 'portal_catalog')
        folder_path = '/'.join(context.getPhysicalPath())
        results = self.find_items_in_path(folder_path, 1)

        return results

    def find_items_in_path(self, folder_path, level):
        # find items in folder sorted manually by user
        query_results = self.catalog(path={'query': folder_path, 'depth': 1}, sort_on='getObjPositionInParent')
        # list of objects (brain, results2) results2 only has value if item is a Folder
        results = []
        for item in query_results:
            results2 = []
            if level < FolderIndexView.MAX_LEVEL:
                if item.Type == 'Folder':  # find its children
                    folder_path_2 = folder_path + '/' + item.id
                    results2 = self.find_items_in_path(folder_path_2, level + 1)
            result = FolderIndexItem(item, results2, self)

            results.append(result)
        return results


class FolderIndexItem():
    """ Brain and its children
    """

    def __init__(self, brain, children, context):
        self.brain = brain
        self.children = children
        self.context = context

    def getChildren(self):
        return self.children

    def getClass(self):
        if self.isFolder():
            return 'span4'
        else:
            return 'span12'

    def hasImg(self):
        pathImg = self.brain.getPath() + '-img'
        if self.context.catalog.searchResults(path=pathImg):
            return True
        else:
            return False

    def getDescription(self):
        return self.brain.Description

    def getPath(self):
        return self.brain.getPath()

    def getPathImg(self):
        return self.brain.getPath() + '-img'

    def getTitle(self):
        return self.brain.Title

    def isFolder(self):
        return self.brain.Type == "Folder"

    def isVisible(self):
        # test if excluded from nav and has valid title
        return not self.brain.exclude_from_nav and len(self.brain.Title) > 0


class CustomCSS(grok.View):
    grok.name('genwebcustom.css')
    grok.context(Interface)
    grok.layer(IGenwebTheme)

    index = ViewPageTemplateFile('views_templates/genwebcustom.css.pt')

    def render(self):
        self.request.response.setHeader('Content-Type', 'text/css')
        return self.index()
