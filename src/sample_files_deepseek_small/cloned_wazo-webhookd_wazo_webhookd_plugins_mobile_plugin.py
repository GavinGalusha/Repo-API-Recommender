# Copyright 2023-2024 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from typing import TYPE_CHECKING

from .http import NotificationResource

if TYPE_CHECKING:
    from ...types import PluginDependencyDict


class Plugin:
    def load(self, dependencies: PluginDependencyDict) -> None:
        api = dependencies['api']
        config = dependencies['config']
        auth_client = dependencies['auth_client']

        api.add_resource(
            NotificationResource,
            '/mobile/notifications',
            resource_class_args=[config, auth_client],
        )
