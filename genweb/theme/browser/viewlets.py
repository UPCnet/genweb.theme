from five import grok
from Acquisition import aq_inner
from zope.interface import Interface
from zope.component import getMultiAdapter
from zope.app.component.hooks import getSite

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.app.layout.viewlets.common import PersonalBarViewlet
from plone.app.layout.viewlets.interfaces import IPortalTop
from Products.CMFPlone.interfaces import IPloneSiteRoot

from genweb.theme.browser.interfaces import IGenwebTheme


grok.context(Interface)


class viewletBase(grok.Viewlet):
    grok.baseclass()

    def portal_url(self):
        self.portal_object.absolute_url()

    def portal_object(self):
        return getSite()


class gwPersonalBarViewlet(PersonalBarViewlet, viewletBase):
    grok.name('genweb.personalbar')
    grok.viewletmanager(IPortalTop)
    grok.layer(IGenwebTheme)

    index = ViewPageTemplateFile('viewlets_templates/personal_bar.pt')
