import unittest2 as unittest

from plone.testing.z2 import Browser

from genweb.theme.testing import GENWEBTHEME_INTEGRATION_TESTING
from genweb.theme.testing import GENWEBTHEME_FUNCTIONAL_TESTING


class BasicTest(unittest.TestCase):

    layer = GENWEBTHEME_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.app = self.layer['app']

    def test_sunburst_layers_available(self):
        self.failUnless('genwebtheme_custom' in self.portal.portal_skins)

    def test_sunburst_skin_installed(self):
        self.skins = self.portal.portal_skins
        theme = self.skins.getDefaultSkin()
        self.failUnless(theme == 'GenwebTheme', 'Default theme is %s' % theme)


class BootstrapTraversalTest(unittest.TestCase):

    layer = GENWEBTHEME_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.app = self.layer['app']
        self.browser = Browser(self.app)

    def testLESSResourceTraversal(self):
        portalURL = self.portal.absolute_url()
        self.browser.open('%s/++bootstrap++less/alerts.less' % portalURL)
        self.assertTrue(u"Alerts" in self.browser.contents)
