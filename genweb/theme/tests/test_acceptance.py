import unittest

from plone.testing import layered
# from plone.app.testing import PLONE_ZSERVER

from genweb.theme.testing import GENWEBTHEME_ACCEPTANCE_TESTING

import robotsuite


def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([
        # layered(robotsuite.RobotTestSuite("test_accessibility.txt"),
        #         layer=PLONE_ZSERVER),
        layered(robotsuite.RobotTestSuite("test_acceptance.txt"),
                layer=GENWEBTHEME_ACCEPTANCE_TESTING),
    ])
    return suite
