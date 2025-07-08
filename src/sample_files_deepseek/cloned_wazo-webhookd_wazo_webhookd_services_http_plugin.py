# Copyright 2017-2025 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import cgi
import json
import logging
import socket
import urllib.parse
from typing import TYPE_CHECKING, NamedTuple

import requests
from celery import Task
from jinja2 import Environment

from wazo_webhookd.services.helpers import (
    RequestDetailsDict,
    requests_automatic_detail,
    requests_automatic_hook_retry,
)

if TYPE_CHECKING:
    from ...config import WebhookdConfigDict
    from ...database.models import Subscription
    from ...types import ServicePluginDependencyDict


logger = logging.getLogger(__name__)


class RequestTimeouts(NamedTuple):
    """Timeouts for requests in seconds."""

    connect: int
    read: int


REQUEST_TIMEOUTS = RequestTimeouts(connect=5, read=15)


class Service:
    def load(self, dependencies: ServicePluginDependencyDict):
        pass

    @classmethod
    def run(
        cls, task: Task, config: WebhookdConfigDict, subscription: Subscription, event
    ) -> RequestDetailsDict | None:
        options = subscription['config']
        headers = {}
        values = {
            'event_name': event['name'],
            'event': event['data'],
            'wazo_uuid': event['origin_uuid'],
        }

        url = Environment().from_string(options['url']).render(values)

        if subscription['owner_user_uuid'] and cls.url_is_localhost(url):
            # some services only listen on 127.0.0.1 and should not be accessible to users
            logger.warning(
                'Rejecting callback from user "%s" to url "%s": remote host is localhost!',
                subscription['owner_user_uuid'],
                url,
            )
            return None

        body = options.get('body')

        if body:
            content_type = options.get('content_type', 'text/plain')
            # NOTE(sileht): parse_header will drop any erroneous options
            ct_mimetype, ct_options = cgi.parse_header(content_type)
            ct_options.setdefault('charset', 'utf-8')
            data = Environment().from_string(body).render(values)
        else:
            ct_mimetype = 'application/json'
            ct_options = {'charset': 'utf-8'}
            data = json.dumps(event['data'])

        data = data.encode(ct_options['charset'])

        content_type_options = "; ".join(map("=".join, ct_options.items()))
        headers['Content-Type'] = f"{ct_mimetype}; {content_type_options}"

        verify = options.get('verify_certificate')
        if verify:
            verify = True if verify == 'true' else verify
            verify = False if verify == 'false' else verify

        with requests_automatic_hook_retry(task):
            session = requests.Session()
            with session.request(
                options['method'],
                url,
                data=data,
                verify=verify,
                headers=headers,
                timeout=REQUEST_TIMEOUTS,
            ) as r:
                r.raise_for_status()  # type: ignore
                return requests_automatic_detail(r)

    @staticmethod
    def url_is_localhost(url: str) -> bool:
        if not (remote_host := urllib.parse.urlparse(url).hostname):
            return False
        remote_address = socket.gethostbyname(remote_host)
        return remote_address == '127.0.0.1'
