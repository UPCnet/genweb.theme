from zope.interface import Interface
from plone.theme.interfaces import IDefaultPloneLayer


class IThemeSpecificN3(IDefaultPloneLayer):
    """Marker interface that defines a Zope browser layer.
    """
