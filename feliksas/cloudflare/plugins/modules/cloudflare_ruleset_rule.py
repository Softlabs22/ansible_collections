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
module: cloudflare_ruleset_rule
short_description: Cloudflare Rulesets rule management module
version_added: "1.2.0"

description: Module for managing Cloudflare rules in a specified ruleset
options:
requirements:
  - python-cloudflare >= 4.1.0

options:
    ref:
        description: The reference name of the rule. Must be unique
        required: true
        type: str
    ruleset_name:
        description: The name of the ruleset containing the rule
        required: true
        type: str
    description:
        description: Description of the rule
        required: false
        type: str
    zone_name:
        description: Zone domain name. Specify when creating zone-scoped rules. Mutually exclusive with account_id.
        required: false
        type: str
    account_id:
        description: Cloudflare account. Specify when creating account-scoped rules. Mutually exclusive with zone_name.
        required: false
        type: str
    action:
        description: The action to perform when the rule matches
        required: false
        type: str
        choices:
          - challenge
          - compress_response
          - execute
          - js_challenge
          - log
          - managed_challenge
          - redirect
          - rewrite
          - route
          - score
          - serve_error
          - set_config
          - skip
          - set_cache_settings
          - log_custom_field
          - ddos_dynamic
          - force_connection_close
    action_parameters:
        description: The parameters configuring the rule's action
        required: false
        type: dict
    enabled:
        description: Whether the rule should be executed
        required: false
        type: bool
    exposed_credential_check:
        description: Configure checks for exposed credentials
        required: false
        type: dict
    expression:
        description: The expression defining which traffic will match the rule
        required: false
        type: str
    logging:
        description: An object configuring the rule's logging behavior
        required: false
        type: dict
    position:
        description: An object configuring where the rule will be placed
        required: false
        type: dict
    ratelimit:
        description: An object configuring the rule's ratelimit behavior
        required: false
        type: dict
    state:
        description: Desired rule state
        choices: ['present', 'absent']
        default: present
        required: false
        type: str
author:
    - Andrey Ignatov (feliksas@feliksas.lv)
'''

EXAMPLES = r'''

'''

RETURN = r'''

'''


def run_module():
    module_args = dict(
        ref=dict(type='str', required=True),
        ruleset_name=dict(type='str', required=True),
        account_id=dict(type='str', required=False),
        zone_name=dict(type='str', required=False),
        description=dict(type='str', required=False),
        action=dict(type='str', required=False, choices=[
            'challenge',
            'compress_response',
            'execute',
            'js_challenge',
            'log',
            'managed_challenge',
            'redirect',
            'rewrite',
            'route',
            'score',
            'serve_error',
            'set_config',
            'skip',
            'set_cache_settings',
            'log_custom_field',
            'ddos_dynamic',
            'force_connection_close',
        ]),
        action_parameters=dict(type='dict', required=False),
        enabled=dict(type='bool', required=False),
        exposed_credential_check=dict(type='dict', required=False),
        expression=dict(type='str', required=False),
        logging=dict(type='dict', required=False),
        position=dict(type='dict', required=False),
        ratelimit=dict(type='dict', required=False),
        state=dict(type='str', required=False, default='present', choices=['present', 'absent']),
    )

    result = dict(
        changed=False,
        rule={},
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
    ruleset = None
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
            if ruleset.name == module.params['ruleset_name']:
                ruleset = cf.rulesets.get(ruleset_id=ruleset.id, account_id=module.params.get('account_id', None), zone_id=zone_id)
                break
    except Exception as e:
        module.fail_json(msg=f"Could not fetch rulesets from Cloudflare: {str(e)}", **result)

    if ruleset is not None:
        for rule in ruleset.rules:
            if rule.ref == module.params['ref']:
                result['rule'] = rule.to_dict()
                break

    if module.params['state'] == 'present':
        if ruleset is None:
            module.fail_json(msg=f"Ruleset '{module.params['ruleset_name']}' does not exist", **result)
        else:
            if len(result['ruleset'].keys()) == 0:  # TODO: Create new rule
                pass
            else:  # TODO: Update existing rule
                pass
    elif module.params['state'] == 'absent':
        if ruleset is not None:  # Don't care if no such ruleset
            pass

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
