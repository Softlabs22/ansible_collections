#!/usr/bin/env python3
from __future__ import annotations

import copy
import traceback
from typing import Dict
from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.basic import AnsibleModule

try:
    from cloudflare import Cloudflare
    from cloudflare.types import zones as zone_types
except ImportError:
    Cloudflare = None
    zone_types = None
    HAS_CLOUDFLARE = False
    CLOUDFLARE_IMPORT_ERROR = traceback.format_exc()
else:
    HAS_CLOUDFLARE = True
    CLOUDFLARE_IMPORT_ERROR = None

__metaclass__ = type

DOCUMENTATION = r'''
---
module: cloudflare_zone_setting
short_description: Cloudflare Zone settings management module
version_added: "1.1.0"

description: Module for managing Cloudflare zone settings

requirements:
  - python-cloudflare >= 4.1.0

options:
    zone_name:
        description: Root domain name of the zone to be configured
        required: true
        type: str
    setting_id:
        description: Setting name
        required: true
        choices:
          - advanced_ddos
          - aegis
          - always_online
          - always_use_https
          - automatic_https_rewrites
          - automatic_platform_optimization
          - brotli
          - browser_cache_ttl
          - browser_check
          - cache_level
          - challenge_ttl
          - ciphers
          - development_mode
          - early_hints
          - email_obfuscation
          - fonts
          - h2_prioritization
          - hotlink_protection
          - http2
          - http3
          - image_resizing
          - ip_geolocation
          - ipv6
          - min_tls_version
          - mirage
          - nel
          - opportunistic_encryption
          - opportunistic_onion
          - orange_to_orange
          - origin_error_page_pass_thru
          - origin_max_http_version
          - polish
          - prefetch_preload
          - proxy_read_timeout
          - pseudo_ipv4
          - response_buffering
          - rocket_loader
          - security_header
          - security_level
          - server_side_exclude
          - sort_query_string_for_cache
          - ssl
          - ssl_recommender
          - tls_1_3
          - tls_client_auth
          - true_client_ip_header
          - waf
          - webp
          - websockets
          - 0rtt
        type: str
    value:
        description: Value of the zone setting, should be string or dictionary, depending on the setting type.
        required: true
        type: raw
author:
    - Andrey Ignatov (feliksas@feliksas.lv)
'''

EXAMPLES = r'''
- name: Change simple setting
  feliksas.cloudflare.cloudflare_zone_setting:
    zone_name: example.com
    setting_id: 0rtt
    value: off
    
- name: Change setting with complex value
  feliksas.cloudflare.cloudflare_zone_setting:
    zone_name: example.com
    setting_id: security_header
    value:
      strict_transport_security:
        enabled: true
'''

RETURN = r'''
setting:
  description: Setting object
  returned: success
  type: dict
  contains:
    name:
      description: Setting ID
      type: string
      returned: success
      sample: 0rtt
    value:
      description: Setting value, can be dict or string
      returned: success
      type: raw
      sample:
        - "off"
        - strict_transport_security:
            enabled: true
            include_subdomains: false
            max_age: 0.0
            nosniff: false
            preload: false
'''


def build_new_value(old_value: Dict | str, new_value: Dict | str) -> Dict | str:
    def merge_dicts(target, source):
        if isinstance(target, dict):
            for key in source.keys():
                if key in target.keys():
                    target[key] = merge_dicts(target[key], source[key])
                else:
                    target[key] = source[key]
        else:
            target = source
        return target

    _old_value = copy.deepcopy(old_value)
    if isinstance(new_value, dict):
        return merge_dicts(_old_value, new_value)
    return new_value


def run_module():
    module_args = dict(
        zone_name=dict(type='str', required=True),
        setting_id=dict(type='str', required=True, choices=[
            'advanced_ddos',
            'aegis',
            'always_online',
            'always_use_https',
            'automatic_https_rewrites',
            'automatic_platform_optimization',
            'brotli',
            'browser_cache_ttl',
            'browser_check',
            'cache_level',
            'challenge_ttl',
            'ciphers',
            'development_mode',
            'early_hints',
            'email_obfuscation',
            'fonts',
            'h2_prioritization',
            'hotlink_protection',
            'http2',
            'http3',
            'image_resizing',
            'ip_geolocation',
            'ipv6',
            'min_tls_version',
            'mirage',
            'nel',
            'opportunistic_encryption',
            'opportunistic_onion',
            'orange_to_orange',
            'origin_error_page_pass_thru',
            'origin_max_http_version',
            'polish',
            'prefetch_preload',
            'proxy_read_timeout',
            'pseudo_ipv4',
            'response_buffering',
            'rocket_loader',
            'security_header',
            'security_level',
            'server_side_exclude',
            'sort_query_string_for_cache',
            'ssl',
            'ssl_recommender',
            'tls_1_3',
            'tls_client_auth',
            'true_client_ip_header',
            'waf',
            'webp',
            'websockets',
            '0rtt',
        ]),
        value=dict(type='raw', required=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(
        changed=False,
        setting={
            "name": module.params["setting_id"],
            "value": {},
        },
    )

    if not HAS_CLOUDFLARE:
        module.fail_json(
            msg=missing_required_lib('cloudflare'),
            exception=CLOUDFLARE_IMPORT_ERROR
        )

    cf = Cloudflare()

    zone = None
    try:
        zones = cf.zones.list(name=module.params['zone_name'])
        for zone in zones:
            if zone.name == module.params['zone_name']:
                zone = zone
                break
        if zone is None:
            module.fail_json(msg=f"Zone '{module.params['zone_name']}' does not exist", **result)
        setting = cf.zones.settings.get(setting_id=module.params['setting_id'], zone_id=zone.id)
        if not isinstance(setting.value, str):
            result['setting']['value'] = setting.value.to_dict()
        else:
            result['setting']['value'] = setting.value
    except Exception as e:
        module.fail_json(msg=f"Unable to fetch zone setting from Cloudflare: {str(e)}", **result)

    if module.check_mode:
        module.exit_json(**result)

    if not isinstance(module.params['value'], type(result['setting']['value'])):
        module.fail_json(
            msg=f"Wrong value type for '{module.params['setting_id']}': {type(result['setting']['value']).__name__} expected, {type(module.params['value']).__name__} given",
            **result)

    new_value = build_new_value(result['setting']['value'], module.params['value'])

    if new_value != result['setting']['value']:
        try:
            # noinspection PyArgumentList
            response = cf.zones.settings.edit(
                zone_id=zone.id,
                setting_id=module.params['setting_id'],
                value=module.params['value']
            )

            if not isinstance(response.value, str):
                updated_value = response.value.to_dict()
            else:
                updated_value = response.value

            if result['setting']['value'] != updated_value:
                result['changed'] = True
                result['setting']['value'] = updated_value
            else:
                module.fail_json("BUG: Requested to change value, but actual value did not change", **result)
        except Exception as e:
            module.fail_json(msg=f"Unable to modify zone setting: {str(e)}", **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
