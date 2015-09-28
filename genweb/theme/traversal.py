from plone.resource.traversal import ResourceTraverser


class BootStrapTraverser(ResourceTraverser):
    """The bootstrap resources traverser.

    Allows traversal to /++bootstrap++<name> using ``plone.resource`` to fetch
    things stored either on the filesystem or in the ZODB.
    """

    name = 'bootstrap'
