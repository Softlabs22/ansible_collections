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
module: cloudflare_ruleset
short_description: Cloudflare Ruleset management module
version_added: "1.2.0"

description: >
  Module for managing Cloudflare rulesets for DDoS protection, WAF, Ratelimiting etc.
  Only ruleset creation and deletion is supported, for rule management - use module V(cloudflare_ruleset_rule)
options:
requirements:
  - python-cloudflare >= 4.1.0

options:
    name:
        description: Name of the ruleset
        required: true
        type: str
    description:
        description: Description of the ruleset
        required: false
        type: str
    zone_name:
        description: Zone domain name. Specify when creating zone-scoped rulesets. Mutually exclusive with O(account_id).
        required: false
        type: str
    account_id:
        description: Cloudflare account. Specify when creating account-scoped rulesets. Mutually exclusive with O(zone_name).
        required: false
        type: str
    kind:
        description: The kind of the ruleset.
        choices: ['managed', 'custom', 'root', 'zone']
        required: false
        type: str
    phase:
        description: The phase of the ruleset.
        required: false
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
    state:
        description: Desired ruleset state
        choices: ['present', 'absent']
        default: present
        required: false
        type: str
author:
    - Andrey Ignatov (andrey.ignatov@agcsoft.com)
'''

EXAMPLES = r'''
- name: Create account ruleset
  softlabs.cloudflare.cloudflare_ruleset:
    name: My ruleset
    account_id: 3973f6861c3ceb48ff96a33cec4d02e2
    kind: custom
    phase: http_request_firewall_custom

- name: Create zone ruleset
  softlabs.cloudflare.cloudflare_ruleset:
    name: My ruleset
    zone_name: example.com
    kind: custom
    phase: http_request_firewall_custom

- name: Delete ruleset
  softlabs.cloudflare.cloudflare_ruleset:
    name: My ruleset
    account_id: 3973f6861c3ceb48ff96a33cec4d02e2
    state: absent
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
        description=dict(type='str', required=False),
        phase=dict(type='str', required=False, choices=[
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
        kind=dict(type='str', choices=['managed', 'custom', 'root', 'zone'], required=False),
        state=dict(type='str', required=False, default='present', choices=['present', 'absent']),
    )

    result = dict(
        changed=False,
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

    if module.params['state'] == "present":
        if module.params.get('phase', None) is None or module.params.get('kind', None) is None:
            module.fail_json(msg="Both phase and kind must be specified when state is set to present", **result)

    cf = Cloudflare()

    zone_id = None
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

        rulesets = cf.rulesets.list(account_id=module.params.get('account_id', None), zone_id=zone_id)
        for ruleset in rulesets:
            if ruleset.name == module.params['name']:
                result['ruleset'] = ruleset.to_dict()
                break

    except Exception as e:
        module.fail_json(msg=f"Could not fetch rulesets from Cloudflare: {str(e)}", **result)

    if module.check_mode:
        module.exit_json(**result)

    if module.params['state'] == 'present':
        if len(result['ruleset'].keys()) == 0:
            try:
                new_ruleset = cf.rulesets.create(
                    kind=module.params['kind'],
                    name=module.params['name'],
                    phase=module.params['phase'],
                    account_id=module.params.get('account_id', None),
                    zone_id=zone_id,
                    description=module.params.get('description', None),
                )
                result['ruleset'] = new_ruleset.to_dict()
                result['changed'] = True
            except Exception as e:
                module.fail_json(msg=f"Could not create ruleset: {str(e)}", **result)
    elif module.params['state'] == 'absent':
        if len(result['ruleset'].keys()) > 0:
            try:
                cf.rulesets.delete(
                    account_id=module.params.get('account_id', None),
                    zone_id=zone_id,
                    ruleset_id=result['ruleset']['id']
                )
                result['changed'] = True
            except Exception as e:
                module.fail_json(msg=f"Could not delete ruleset: {str(e)}", **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
