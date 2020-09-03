## Script (Python) "require_login"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=Login

login = 'login'

portal = context.portal_url.getPortalObject()
# if cookie crumbler did a traverse instead of a redirect,
# this would be the way to get the value of came_from
#url = portal.getCurrentUrl()
#context.REQUEST.set('came_from', url)

if context.portal_membership.isAnonymousUser():
    return portal.restrictedTraverse(login)()
else:
    from AccessControl import getSecurityManager
    if getSecurityManager().checkPermission("zope2.View", context):
        came_from = context.REQUEST.get('came_from')
        if came_from:
            context.REQUEST.response.redirect(came_from)
        else:
            return portal.restrictedTraverse('insufficient_privileges')()
    else:
        return portal.restrictedTraverse('insufficient_privileges')()
