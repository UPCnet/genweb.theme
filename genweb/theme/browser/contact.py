# -*- coding: utf-8 -*-
import re
from five import grok
from plone import api
from cgi import escape
from Acquisition import aq_inner

from zope.schema import TextLine, Text, ValidationError, Choice
from z3c.form import button
from plone.directives import form

from plone.formwidget.recaptcha.widget import ReCaptchaFieldWidget

from Products.CMFPlone.utils import safe_unicode
from Products.statusmessages.interfaces import IStatusMessage
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from plone.app.layout.navigation.interfaces import INavigationRoot

from genweb.theme.browser.interfaces import IGenwebTheme

from genweb.core import utils

from genweb.core.utils import pref_lang
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from genweb.controlpanel.interface import IGenwebControlPanelSettings
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.interfaces import IVocabularyFactory


grok.templatedir("views_templates")


MESSAGE_TEMPLATE = u"""\
Heu rebut aquest correu perquè en/na %(name)s (%(from_address)s) ha enviat \
comentaris sobre l'espai Genweb que administreu a \

%(genweb)s

El missatge és:

%(message)s
--
%(from_name)s
"""


class getEmailsContactNames(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        registry = getUtility(IRegistry)
        settings = registry.forInterface(IGenwebControlPanelSettings, check=False)
        items = []
        if settings.contact_emails_table is not None:
            for item in settings.contact_emails_table:
                items.append(SimpleVocabulary.createTerm(item['name'], item['name'], item['name']))
        return SimpleVocabulary(items)

grok.global_utility(getEmailsContactNames, name=u"availableContacts")


class NotAnEmailAddress(ValidationError):
    __doc__ = _(u"Invalid email address")

check_email = re.compile(r"[a-zA-Z0-9._%-]+@([a-zA-Z0-9-]+\.)*[a-zA-Z]{2,4}").match


def validate_email(value):
    if not check_email(value):
        raise NotAnEmailAddress(value)
    return True


def show_to_address():
    if True:
        return 'input'
    else:
        return 'hidden'


class IContactForm(form.Schema):
    """Define the fields of our form
    """

    form.mode(to_address=show_to_address())
    to_address = Choice(title=_('to_address',
                     default=u"Recipient"),
                     vocabulary=u"availableContacts")

    nombre = TextLine(title=_('genweb_sender_fullname', default=u"Name"),
                      required=True)

    from_address = TextLine(title=_('genweb_sender_from_address', default=u"E-Mail"),
                            required=True,
                            constraint=validate_email)

    asunto = TextLine(title=_('genweb_subject', default="Subject"),
                      required=True)

    mensaje = Text(title=_('genweb_message', default="Message"),
                   description=_("genweb_help_message", default="Please enter the message you want to send."),
                   required=True)

    form.widget(captcha=ReCaptchaFieldWidget)
    captcha = TextLine(title=_('genweb_type_the_code', default="Type the code"),
                       description=_('genweb_help_type_the_code', default="Type the code from the picture shown below"),
                       required=True)


class ContactForm(form.SchemaForm):
    grok.name('contact')
    grok.context(INavigationRoot)
    grok.template("contact")
    grok.require('zope2.View')
    grok.layer(IGenwebTheme)

    ignoreContext = True

    schema = IContactForm

    # This trick hides the editable border and tabs in Plone
    def update(self):
        self.request.set('disable_border', True)
        super(ContactForm, self).update()

    @button.buttonAndHandler(_(u"Send"))
    def action_send(self, action):
        """Send the email to the configured mail address in properties and redirect to the
        front page, showing a status message to say the message was received.
        """
        data, errors = self.extractData()
        if 'recaptcha_response_field' in self.request.keys():
            # Verify the user input against the captcha
            if self.context.restrictedTraverse('@@recaptcha').verify():
                pass
            else:
                return
        else:
            return

        if 'asunto' not in data or \
           'from_address' not in data or \
           'mensaje' not in data or \
           'nombre' not in data:
            return

        context = aq_inner(self.context)
        mailhost = getToolByName(context, 'MailHost')
        portal = api.portal.get()
        email_charset = portal.getProperty('email_charset')

        multi_contact_emails = self.getEmailsContact()
        import ipdb;ipdb.set_trace()
        if multi_contact_emails['contact_emails_show']:
            to_address = ''
        else:
            to_address = portal.getProperty('email_from_address')

        from_name = portal.getProperty('email_from_name')

        source = "%s <%s>" % (escape(safe_unicode(data['nombre'])), escape(safe_unicode(data['from_address'])))
        subject = "[Formulari Contacte] %s" % (escape(safe_unicode(data['asunto'])))
        message = MESSAGE_TEMPLATE % dict(name=data['nombre'],
                                          from_address=data['from_address'],
                                          genweb=portal.absolute_url(),
                                          message=data['mensaje'],
                                          from_name=from_name)

        mailhost.secureSend(escape(safe_unicode(message)), to_address, source,
                            subject=subject, subtype='plain',
                            charset=email_charset, debug=False,
                            )

        confirm = _(u"Mail sent.")
        IStatusMessage(self.request).addStatusMessage(confirm, type='info')

        self.request.response.redirect('contact_feedback')

        return ''

    def getURLDirectori(self, codi):
        return "http://directori.upc.edu/directori/dadesUE.jsp?id=%s" % codi

    def getURLMaps(self, codi):
        lang = utils.pref_lang()
        return "//maps.upc.edu/embed/?lang=%s&iu=%s" % (lang, codi)

    def getURLUPCmaps(self, codi):
        lang = self.context.Language()
        return "//maps.upc.edu/?iu=%s&lang=%s" % (codi, lang)

    def getContactPersonalized(self):
        isCustomized = utils.genweb_config().contacte_BBDD_or_page
        return isCustomized

    def getContactPage(self):
        """
        Funcio que retorna la pagina de contacte personalitzada
        """
        page = ""
        context = aq_inner(self.context)
        lang = self.context.Language()
        if lang == 'ca':
            customized_page = getattr(context, 'contactepersonalitzat', False)
        elif lang == 'es':
            customized_page = getattr(context, 'contactopersonalizado', False)
        elif lang == 'en':
            customized_page = getattr(context, 'customizedcontact', False)
        try:
            state = api.content.get_state(customized_page)
        except:
            state = ''
        if state == 'published':
            contact_body = context.contactepersonalitzat.text.raw
            page = contact_body
        else:
            return page

    def getEmailsContact(self):
        lang = pref_lang()

        registry = getUtility(IRegistry)
        settings = registry.forInterface(IGenwebControlPanelSettings, check=False)
        items = []
        if settings.contact_emails_table is not None:
            for item in settings.contact_emails_table:
                if lang in item['language']:
                    items.append(item)

        if len(items) > 0 and settings.contacte_multi_email:
            contact_emails_show = True
        else:
            contact_emails_show = False

        dades = {'contact_emails_table': items,
                 'contact_emails_show': contact_emails_show,
                 }
        return dades
