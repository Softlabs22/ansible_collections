#!/usr/bin/env python3

import traceback
from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.basic import AnsibleModule

try:
    from cloudflare import Cloudflare
except ImportError:
    Cloudflare = None
    HAS_CLOUDFLARE = False
    CLOUDFLARE_IMPORT_ERROR = traceback.format_exc()
else:
    HAS_CLOUDFLARE = True
    CLOUDFLARE_IMPORT_ERROR = None

__metaclass__ = type

DOCUMENTATION = r'''
---
module: cloudflare_ruleset_info
short_description: Cloudflare Ruleset query module
version_added: "1.2.0"

description: Module for getting information on Cloudflare rulesets
options:
requirements:
  - python-cloudflare >= 4.1.0

options:
    name:
        description: Name of the ruleset
        required: true
        type: str
    zone_name:
        description: Zone domain name. Specify when querying zone-scoped rulesets. Mutually exclusive with account_id.
        required: false
        type: str
    account_id:
        description: Cloudflare account. Specify when querying account-scoped rulesets. Mutually exclusive with zone_name.
        required: false
        type: str
    phase:
        description: The phase of the ruleset.
        required: true
        type: str
        choices:
          - ddos_l4
          - ddos_l7
          - http_config_settings
          - http_custom_errors
          - http_log_custom_fields
          - http_ratelimit
          - http_request_cache_settings
          - http_request_dynamic_redirect
          - http_request_firewall_custom
          - http_request_firewall_managed
          - http_request_late_transform
          - http_request_origin
          - http_request_redirect
          - http_request_sanitize
          - http_request_sbfm
          - http_request_transform
          - http_response_compression
          - http_response_firewall_managed
          - http_response_headers_transform
          - magic_transit
          - magic_transit_ids_managed
          - magic_transit_managed
          - magic_transit_ratelimit
author:
    - Andrey Ignatov (andrey.ignatov@agcsoft.com)
'''

EXAMPLES = r'''
- name: Query zone-scoped ruleset
  softlabs.cloudflare.cloudflare_ruleset_info:
    name: My ruleset
    zone_name: example.com
    phase: http_request_firewall_custom
    
- name: Query account-scoped ruleset
  softlabs.cloudflare.cloudflare_ruleset_info:
    name: My ruleset
    account_id: 3973f6861c3ceb48ff96a33cec4d02e2
    phase: http_request_firewall_custom
'''

RETURN = r'''
ruleset:
  description: Rule set object
  returned: success
  type: dict
  contains:
    description:
      description: Ruleset description
      type: str
      returned: success
      sample: My custom ruleset
    id:
      description: Ruleset ID
      type: str
      returned: success
      sample: b9ebca41fc574a2685631374d2172316
    kind:
      description: Ruleset kind
      type: str
      returned: success
      sample: zone
    last_updated:
      description: Ruleset last update timestamp
      type: str
      returned: success
      sample: "2025-03-28T12:44:44.946446+00:00"
    name:
      description: Ruleset name
      type: str
      returned: success
      sample: My ruleset
    phase:
      description: Ruleset phase
      type: str
      returned: success
      sample: http_ratelimit
    rules:
      description: List of rules
      type: list
      returned: success
      sample:
        - action: rewrite
          action_parameters:
            uri:
              origin: false
              path:
                expression: "normalize_url_path(raw.http.request.uri.path)"
          description: Normalization on the URL path, without propagating it to the origin
          enabled: true
          id: 78723a9e0c7c4c6dbec5684cb766231d
          last_updated: "2024-08-01T17:37:11.538019+00:00"
          ref: 272936dc447b41fe976255ff6b768ec0
          version: "6"
    version:
      description: Ruleset version
      type: str
      returned: success
      sample: "1"
'''


def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        account_id=dict(type='str', required=False),
        zone_name=dict(type='str', required=False),
        phase=dict(type='str', required=True, choices=[
            'ddos_l4',
            'ddos_l7',
            'http_config_settings',
            'http_custom_errors',
            'http_log_custom_fields',
            'http_ratelimit',
            'http_request_cache_settings',
            'http_request_dynamic_redirect',
            'http_request_firewall_custom',
            'http_request_firewall_managed',
            'http_request_late_transform',
            'http_request_origin',
            'http_request_redirect',
            'http_request_sanitize',
            'http_request_sbfm',
            'http_request_transform',
            'http_response_compression',
            'http_response_firewall_managed',
            'http_response_headers_transform',
            'magic_transit',
            'magic_transit_ids_managed',
            'magic_transit_managed',
            'magic_transit_ratelimit',
        ]),
    )

    result = dict(
        ruleset={},
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if not HAS_CLOUDFLARE:
        module.fail_json(
            msg=missing_required_lib('cloudflare'),
            exception=CLOUDFLARE_IMPORT_ERROR
        )

    if (module.params.get('account_id', None) is None and module.params.get('zone_name', None) is None)\
            or (module.params.get('account_id', None) is not None and module.params.get('zone_name', None) is not None):
        module.fail_json(msg="Either account_id or zone_name must be specified", **result)

    cf = Cloudflare()

    zone_id = None
    ruleset_id = None
    try:
        if module.params.get('zone_name', None) is not None:
            zones = cf.zones.list(name=module.params['zone_name'])
            zone = None
            for zone in zones:
                if zone.name == module.params['zone_name']:
                    zone = zone
                    break
            if zone is None:
                module.fail_json(msg=f"Zone '{module.params['zone_name']}' does not exist", **result)
            else:
                zone_id = zone.id

        rulesets = cf.rulesets.list(account_id=module.params['account_id'], zone_id=zone_id)
        for ruleset in rulesets:
            if ruleset.name == module.params['name'] and ruleset.phase == module.params['phase']:
                ruleset_id = ruleset.id
                break
    except Exception as e:
        module.fail_json(msg=f"Could not fetch rulesets from Cloudflare: {str(e)}", **result)

    if ruleset_id is not None:
        try:
            result['ruleset'] = cf.rulesets.get(
                account_id=module.params['account_id'],
                zone_id=zone_id,
                ruleset_id=ruleset_id
            ).to_dict()
        except Exception as e:
            module.fail_json(msg=f"Could not fetch ruleset from Cloudflare: {str(e)}", **result)

    if module.check_mode:
        module.exit_json(**result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
