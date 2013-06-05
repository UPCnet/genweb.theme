from zope.configuration import xmlconfig

from plone.testing.z2 import ZSERVER_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting


class GenwebTheme(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import genweb.theme
        import genweb.core
        xmlconfig.file('configure.zcml',
                       genweb.theme,
                       context=configurationContext)

    def setUpPloneSite(self, portal):
        # Install into Plone site using portal_setup
        applyProfile(portal, 'genweb.theme:default')
        applyProfile(portal, 'genweb.controlpanel:default')


GENWEBTHEME_FIXTURE = GenwebTheme()
GENWEBTHEME_INTEGRATION_TESTING = IntegrationTesting(
    bases=(GENWEBTHEME_FIXTURE,),
    name="GenwebTheme:Integration")
GENWEBTHEME_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(GENWEBTHEME_FIXTURE,),
    name="GenwebTheme:Functional")
GENWEBTHEME_ROBOT_TESTING = FunctionalTesting(
    bases=(GENWEBTHEME_FIXTURE, ZSERVER_FIXTURE),
    name="GenwebTheme:Robot")
