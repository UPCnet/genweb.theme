from five import grok
from Acquisition import aq_inner
from AccessControl import getSecurityManager
from zope.interface import Interface
from zope.component import getMultiAdapter
from zope.app.component.hooks import getSite

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore import permissions

from plone.app.layout.viewlets.common import PersonalBarViewlet
from plone.app.layout.viewlets.interfaces import IPortalTop
from Products.CMFPlone.interfaces import IPloneSiteRoot

from genweb.core.utils import havePermissionAtRoot, assignAltAcc
from genweb.theme.browser.interfaces import IGenwebTheme


grok.context(Interface)


class viewletBase(grok.Viewlet):
    grok.baseclass()

    def portal_url(self):
        self.portal().absolute_url()

    def portal(self):
        return getSite()

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
