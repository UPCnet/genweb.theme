from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from plone.app.portlets.portlets.navigation import Renderer as NavigationRenderer
from plone.app.portlets.portlets.rss import Renderer as RssRenderer
from plone.portlet.collection.collection import Renderer as CollectionRenderer


class gwNavigation(NavigationRenderer):
    """ The standard navigation portlet override 'old style'
        as it doesn't allow to do it jbot way...
    """
    _template = ViewPageTemplateFile('templates/navigation.pt')
    recurse = ViewPageTemplateFile('templates/navigation_recurse.pt')


class gwRSS(RssRenderer):
    """ The standard rss portlet override 'old style'
        as it doesn't allow to do it jbot way...
    """
    render_full = ZopeTwoPageTemplateFile('templates/rss.pt')


class gwCollection(CollectionRenderer):
    """ The standard rss portlet override 'old style'
        as it doesn't allow to do it jbot way...
    """
    _template = ViewPageTemplateFile('templates/collection.pt')
