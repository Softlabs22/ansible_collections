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
- name: Create rule
  feliksas.cloudflare.cloudflare_ruleset_rule:
    ref: my_rule
    zone_name: example.com
    ruleset_name: My ruleset
    description: My rule for cache settings
    action: set_cache_settings
    action_parameters:
      browser_ttl:
        mode: respect_origin
      cache: true
      edge_ttl:
        mode: bypass_by_default
    expression: '(http.host contains "example.com")'
    
- name: Modify rule
  feliksas.cloudflare.cloudflare_ruleset_rule:
    ref: my_rule
    zone_name: example.com
    ruleset_name: My ruleset
    description: My rule for cache settings
    action: set_cache_settings
    action_parameters:
      browser_ttl:
        mode: respect_origin
      cache: true
      edge_ttl:
        mode: bypass_by_default
    expression: '(http.host contains "subdomain.example.com")'    
    
- name: Disable rule
  feliksas.cloudflare.cloudflare_ruleset_rule:
    ref: my_rule
    zone_name: example.com
    ruleset_name: My ruleset
    description: My rule for cache settings
    action: set_cache_settings
    action_parameters:
      browser_ttl:
        mode: respect_origin
      cache: true
      edge_ttl:
        mode: bypass_by_default
    expression: '(http.host contains "example.com")'
    enabled: false

- name: Delete rule
  feliksas.cloudflare.cloudflare_ruleset_rule:
    ref: my_rule
    zone_name: example.com
    ruleset_name: My ruleset
    state: absent
'''

RETURN = r'''
rule:
  description: Rule contents object
  returned: success
  type: dict
  contains:
    action:
      description: The action to perform when the rule matches
      returned: success
      type: str
      sample: set_cache_settings
    action_parameters:
      description: The parameters object configuring the rule's action
      returned: success
      type: dict
      sample:
        browser_ttl:
          mode: respect_origin
        cache: true
        edge_ttl:
          mode: bypass_by_default
    enabled:
      description: Whether the rule should be executed
      returned: success
      type: bool
    exposed_credential_check:
      description: Exposed credentials checks configuration, if present
      returned: success
      type: dict
      contains:
        password_expression:
          description: Password matching expression
          returned: success
          type: str
          sample: "url_decode(http.request.body.form[\\\"password\\\"][0])"
        username_expression:
          description: Username matching expression
          returned: success
          type: str
          sample: "url_decode(http.request.body.form[\\\"username\\\"][0])"
    expression:
      description: The expression defining which traffic will match the rule
      returned: success
      type: str
      sample: '(http.host contains "example.com")'
    logging:
      description: An object configuring the rule's logging behavior, if present
      returned: success
      type: dict
      contains:
        enabled:
          description: Whether logging should be enabled
          returned: success
          type: bool
    ratelimit:
      description: Rate limiting parameters, if present
      returned: success
      type: dict
      contains:
        characteristics:
          description: Characteristics of the request on which the ratelimiter counter will be incremented
          returned: success
          type: str
          sample: "ip.src"
        period:
          description: Period in seconds over which the counter is being incremented
          returned: success
          type: int
          sample: 60
        counting_expression:
          description: Defines when the ratelimit counter should be incremented. It is optional and defaults to the same as the rule's expression
          returned: success
          type: str
        mitigation_timeout:
          description: Period of time in seconds after which the action will be disabled following its first execution
          returned: success
          type: int
          sample: 60
        requests_per_period:
          description: The threshold of requests per period after which the action will be executed for the first time
          returned: success
          type: int
          sample: 60
        score_per_period:
          description: The score threshold per period for which the action will be executed the first time
          returned: success
          type: int
          sample: 60
        score_response_header_name:
          description: The response header name provided by the origin which should contain the score to increment ratelimit counter on
          returned: success
          type: str
    id:
      description: The rule ID
      returned: success
      type: str
      sample: 0548abcd9e6443b08d0a280bc1001b46
    last_updated:
      description: The rule's last update time
      returned: success
      type: str
      sample: "2025-03-31T09:29:44.597883+00:00"
    ref:
      description: The reference of the rule (the rule ID by default)
      returned: success
      type: str
      sample: my_rule
    version:
      description: The version of the rule
      returned: success
      type: str
      sample: "4"
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
        for rs in rulesets:
            if rs.name == module.params['ruleset_name']:
                ruleset = cf.rulesets.get(ruleset_id=rs.id, account_id=module.params.get('account_id', None), zone_id=zone_id)
                break
    except Exception as e:
        module.fail_json(msg=f"Could not fetch rulesets from Cloudflare: {str(e)}", **result)

    if ruleset is not None and ruleset.rules is not None:
        for rule in ruleset.rules:
            if rule.ref == module.params['ref']:
                result['rule'] = rule.to_dict()
                break

    if module.check_mode:
        module.exit_json(**result)

    if module.params['state'] == 'present':
        if ruleset is None:
            module.fail_json(msg=f"Ruleset '{module.params['ruleset_name']}' does not exist", **result)
        else:
            new_rule_spec = {}
            for param in (
                    'ref',
                    'description',
                    'action',
                    'action_parameters',
                    'enabled',
                    'exposed_credential_check',
                    'expression',
                    'logging',
                    'position',
                    'ratelimit',
            ):
                if module.params[param] is not None:
                    new_rule_spec[param] = module.params[param]
            changed_ruleset = None
            if len(result['rule'].keys()) == 0:
                try:
                    changed_ruleset = cf.rulesets.rules.create(
                        ruleset_id=ruleset.id,
                        account_id=module.params['account_id'],
                        zone_id=zone_id,
                        **new_rule_spec
                    )
                except Exception as e:
                    module.fail_json(msg=f"Could not create new rule: {str(e)}", **result)
            else:
                old_rule_id = result['rule'].pop('id')
                result['rule'].pop('version')
                result['rule'].pop('last_updated')
                if result['rule'] != new_rule_spec:
                    try:
                        changed_ruleset = cf.rulesets.rules.edit(
                            ruleset_id=ruleset.id,
                            account_id=module.params['account_id'],
                            zone_id=zone_id,
                            rule_id=old_rule_id,
                            **new_rule_spec
                        )
                    except Exception as e:
                        module.fail_json(msg=f"Could not update rule: {str(e)}", **result)
            if changed_ruleset is not None:
                for rule in changed_ruleset.rules:
                    if rule.ref == module.params['ref']:
                        result['rule'] = rule.to_dict()
                        break
                result['changed'] = True

    elif module.params['state'] == 'absent':
        if ruleset is not None and len(result['rule'].keys()) > 0:  # Don't care if no such ruleset
            try:
                cf.rulesets.rules.delete(
                    account_id=module.params['account_id'],
                    zone_id=zone_id,
                    ruleset_id=ruleset.id,
                    rule_id=result['rule']['id']
                )
                result['changed'] = True
            except Exception as e:
                module.fail_json(msg=f"Could not delete rule: {str(e)}", **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
