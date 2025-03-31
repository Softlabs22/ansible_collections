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
module: cloudflare_ruleset_rule_info
short_description: Cloudflare Rulesets rule query module
version_added: "1.2.0"

description: Module for getting information on Cloudflare rules
options:
requirements:
  - python-cloudflare >= 4.1.0

options:
    ref:
        description: The reference name of the rule. Mutually exclusive with description
        required: false
        type: str
    description:
        description: Description of the rule (acts as name in Cloudflare dashboard). Mutually exclusive with ref
        required: false
        type: str
    ruleset_name:
        description: The name of the ruleset containing the rule
        required: true
        type: str
    phase:
        description: The phase of the ruleset containing the rule
        required: false
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
    zone_name:
        description: Zone domain name. Specify when querying rules in zone-scoped rulesets. Mutually exclusive with account_id.
        required: false
        type: str
    account_id:
        description: Cloudflare account ID. Specify when querying rules in account-scoped rulesets. Mutually exclusive with zone_name.
        required: false
        type: str
author:
    - Andrey Ignatov (feliksas@feliksas.lv)
'''

EXAMPLES = r'''
- name: Query rule in zone-scoped ruleset by description
  cloudflare_ruleset_rule_info:
  feliksas.cloudflare.cloudflare_ruleset_rule_info:
    description: My rule for cache settings
    zone_name: example.com
    ruleset_name: My ruleset
    phase: http_request_cache_settings
    
- name: Query rule in zone-scoped ruleset by description
  cloudflare_ruleset_rule_info:
  feliksas.cloudflare.cloudflare_ruleset_rule_info:
    description: My rule for cache settings
    account_id: 3973f6861c3ceb48ff96a33cec4d02e2
    ruleset_name: My ruleset
    phase: http_request_cache_settings
    
- name: Query rule in zone-scoped ruleset by ref
  feliksas.cloudflare.cloudflare_ruleset_rule_info:
    ref: my_rule
    zone_name: example.com
    ruleset_name: My ruleset
    phase: http_request_cache_settings
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
        ref=dict(type='str', required=False),
        ruleset_name=dict(type='str', required=True),
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
        account_id=dict(type='str', required=False),
        zone_name=dict(type='str', required=False),
        description=dict(type='str', required=False),
    )

    result = dict(
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

    if (module.params.get('ref', None) is None and module.params.get('description', None) is None)\
            or (module.params.get('ref', None) is not None and module.params.get('description', None) is not None):
        module.fail_json(msg="Either ref or description must be specified", **result)

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
            if rs.name == module.params['ruleset_name'] and rs.phase == module.params['phase']:
                ruleset = cf.rulesets.get(ruleset_id=rs.id, account_id=module.params.get('account_id', None), zone_id=zone_id)
                break
        if ruleset is None:
            module.fail_json(msg=f"Ruleset \"{module.params['ruleset_name']}\" does not exist in phase {module.params['phase']}", **result)
    except Exception as e:
        module.fail_json(msg=f"Could not fetch rulesets from Cloudflare: {str(e)}", **result)

    if ruleset.rules is not None:
        for rule in ruleset.rules:
            if rule.ref == module.params['ref'] or rule.description == module.params['description']:
                result['rule'] = rule.to_dict()
                break

    if module.check_mode:
        module.exit_json(**result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
