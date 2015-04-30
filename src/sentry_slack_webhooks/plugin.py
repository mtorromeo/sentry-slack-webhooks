"""
sentry_slack_webhooks.plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import sentry_slack_webhooks

import re
import urllib
import urllib2
import logging
from cgi import escape

from django import forms
from django.utils.translation import ugettext_lazy as _
from urlparse import urlparse

from sentry.plugins.bases import notify
from sentry.utils import json



LEVEL_TO_COLOR = {
    'debug': 'cfd3da',
    'info': '2788ce',
    'warning': 'f18500',
    'error': 'f43f20',
    'fatal': 'd20f2a',
}


class SlackWebHooksOptionsForm(forms.Form):
    webhook = forms.CharField(
        label=_('WebHook URL'),
        widget=forms.TextInput(attrs={'class': 'span6'}),
        help_text=_('Ex. https://hooks.slack.com/services/FOO/BAR/BAZ.'))
    channel = forms.CharField(
        label=_('Channel'),
        widget=forms.TextInput(attrs={'class': 'span6'}),
        help_text=_('Ex. #general'))
    username = forms.CharField(
        label=_('Bot Name'),
        widget=forms.TextInput(attrs={'class': 'span6', 'placeholder': 'Sentry Bot'}),
        help_text=_('Optional user name for the bot that will post the messages.'))
    icon = forms.CharField(
        label=_('Bot Icon'),
        widget=forms.TextInput(attrs={'class': 'span6', 'placeholder': ':ghost:', 'value': 'https://slack.global.ssl.fastly.net/17635/img/services/sentry_48.png'}),
        help_text=_('Optional icon emoji or URL to a valid image for the bot.'))

    def clean_subdomain(self):
        value = self.cleaned_data.get('subdomain')
        if not re.match('^[a-z0-9_\-]+$', value, re.I):
            raise forms.ValidationError('Invalid subdomain')
        return value

    def clean_channel(self):
        value = self.cleaned_data.get('channel')
        if len(value) and value[0] not in ('@', '#'):
            value = '#' + value
        if not re.match('^[#@][a-z0-9_\-]+$', value, re.I):
            raise forms.ValidationError('Invalid channel')
        return value


class SlackWebHooksPlugin(notify.NotificationPlugin):
    author = 'Massimiliano Torromeo'
    author_url = 'https://github.com/mtorromeo/sentry-slack-webhooks'
    version = sentry_slack_webhooks.VERSION
    description = "Pushes events to the slack incoming webhooks."
    resource_links = [
        ('Bug Tracker', 'https://github.com/mtorromeo/sentry-slack-webhooks/issues'),
        ('Source', 'https://github.com/mtorromeo/sentry-slack-webhooks'),
    ]

    slug = 'slack-webhooks'
    title = _('Slack WebHooks')
    conf_title = title
    conf_key = 'slack-webhooks'
    project_conf_form = SlackWebHooksOptionsForm
    logger = logging.getLogger('sentry.plugins.slack-webhooks')

    def is_configured(self, project, **kwargs):
        return all((self.get_option(k, project) for k in ('webhook', 'channel')))

    def should_notify(self, group, event):
        # Always notify since this is not a per-user notification
        return True

    def color_for_group(self, group):
        return '#' + LEVEL_TO_COLOR.get(group.get_level_display(), 'error')

    def notify_users(self, group, event, fail_silently=False):
        webhook = self.get_option('webhook', event.project)
        channel = self.get_option('channel', event.project)
        username = self.get_option('username', event.project)
        icon = self.get_option('icon', event.project)

        project = event.project
        team = event.team

        title = '%s on <%s|%s %s>' % (
            'New event' if group.times_seen == 1 else 'Regression',
            group.get_absolute_url(),
            escape(team.name.encode('utf-8')),
            escape(project.name.encode('utf-8')),
        )

        message = group.message_short.encode('utf-8')
        culprit = group.title.encode('utf-8')

        # They can be the same if there is no culprit
        # So we set culprit to an empty string instead of duplicating the text
        if message == culprit:
            culprit = ''

        payload = {
            'parse': 'none',
            'text': title,
            'channel': channel,
            'attachments': [{
                'color': self.color_for_group(group),
                'fields': [{
                    'title': escape(message),
                    'value': escape(culprit),
                    'short': False,
                }]
            }]
        }

        if username:
            payload['username'] = username

        if icon:
            urlparts = urlparse(icon)
            if urlparts.scheme and urlparts.netloc:
                payload['icon_url'] = icon
            else:
                payload['icon_emoji'] = icon

        data = {'payload': json.dumps(payload)}

        data = urllib.urlencode(data)
        request = urllib2.Request(webhook, data)
        request.add_header('User-Agent', 'sentry-slack-webhooks/%s' % self.version)
        try:
            return urllib2.urlopen(request).read()
        except urllib2.URLError as e:
            self.logger.error('Could not connect to Slack: %s', e.read())
        except urllib2.HTTPError as e:
            self.logger.error('Error posting to Slack: %s', e.read())
