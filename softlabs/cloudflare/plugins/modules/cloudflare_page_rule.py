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
module: cloudflare_page_rule
short_description: Cloudflare page rules management module
version_added: "1.5.0"

description: Module for managing Cloudflare page rules
requirements:
  - python-cloudflare >= 4.1.0

options:
    zone_name:
        description: The name of the zone where to create the page rule
        required: true
        type: str
    target_url:
        description: URL expression to be targeted by the rule
        required: true
        type: str
    actions:
        description: A list of actions to be performed on match, element schema should match Cloudflare API specification
        required: true
        type: list
        elements: dict
    priority:
        description: >
          The priority of the rule, used to define which Page Rule is processed over another. Default is lowest (1).
          If changed from default value, should always be specified to preserve rule ordering, when O(state=present) 
        required: false
        type: int
        default: 1
    enabled:
        description: Whether the rule is enabled or not
        required: false
        type: bool
        default: true
    state:
        description: Desired rule state
        choices: ['present', 'absent']
        default: present
        required: false
        type: str
author:
    - Andrey Ignatov (andrey.ignatov@agcsoft.com)
'''

EXAMPLES = r'''
- name: Create a page rule
  softlabs.cloudflare.cloudflare_page_rule:
    zone_name: example.com
    target_url: "https://example.com/myroute/*"
    actions:
      - id: rocket_loader
        value: on

- name: Set particular priority for page rule
  softlabs.cloudflare.cloudflare_page_rule:
    zone_name: example.com
    target_url: "https://example.com/myroute/*"
    actions:
      - id: rocket_loader
        value: on
    priority: 2
    
- name: Disable a page rule
  softlabs.cloudflare.cloudflare_page_rule:
    zone_name: example.com
    target_url: "https://example.com/myroute/*"
    actions:
      - id: rocket_loader
        value: on
    priority: 2
    enabled: false
    
- name: Delete a page rule
  softlabs.cloudflare.cloudflare_page_rule:
    zone_name: example.com
    target_url: "https://example.com/myroute/*"
    actions:
      - id: rocket_loader
        value: on
    state: absent
'''

RETURN = r'''
old_rule:
  description: The previous state of the page rule
  returned: success
  type: dict
  contains:
    actions:
      description: A list of actions to be performed on match
      returned: success
      type: list
      elements: dict
      sample:
        - id: rocket_loader
          value: on
    created_on:
      description: The date and time the page rule was created
      returned: success
      type: str
      sample: "2025-04-02T09:16:57+00:00"
    id:
      description: The ID of the page rule
      returned: success
      type: str
      sample: "ed8eee725e4574b7b1c51eed88524347"
    modified_on:
      description: The date and time the page rule was modified
      returned: success
      type: str
      sample: "2025-04-02T09:16:57+00:00"
    priority:
      description: The priority of the page rule (position in rule list)
      returned: success
      type: int
      sample: 2
    status:
      description: Whether the page rule is enabled or disabled
      returned: success
      type: str
      sample:
       - active
       - disabled
    targets:
      description: Page rule target URL specification
      returned: success
      type: list
      elements: dict
      sample:
        - constraint:
            operator: matches
            value: "https://example.com/myroute/*"
          target: url
new_rule:
  description: The new state of the page rule. Schema is the same as for RV(old_rule)
  returned: success
  type: dict
'''


def compare_rule_actions(old_actions, new_actions):
    _old = {}
    _new = {}
    for action in old_actions:
        _old[action["id"]] = action.get("value", None)
    for action in new_actions:
        _new[action["id"]] = action.get("value", None)

    return _old == _new


def calculate_new_priority(old_prio, new_prio, rules_count):
    if rules_count == 1:
        return 1
    if new_prio > rules_count:
        if old_prio == rules_count:
            return old_prio
        return rules_count+1
    if new_prio > old_prio:
        return new_prio+1
    return new_prio


def run_module():
    module_args = dict(
        zone_name=dict(type='str', required=True),
        target_url=dict(type='str', required=True),
        actions=dict(type='list', elements='dict', required=True),
        priority=dict(type='int', required=False, default=1),
        enabled=dict(type='bool', required=False, default=True),
        state=dict(type='str', required=False, default='present', choices=['present', 'absent']),
    )

    result = dict(
        changed=False,
        old_rule={},
        new_rule={},
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

    cf = Cloudflare()

    zone_id = None
    rules = None
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

        if ord(module.params['target_url'][-1]) in range(ord('a'), ord('z') + 1):
            module.params['target_url'] = module.params['target_url'] + '/'

        rules = cf.page_rules.list(zone_id=zone_id)
        for rule in rules:
            if rule.targets[0].constraint.value == module.params['target_url']:
                result['old_rule'] = rule.to_dict()
                break
    except Exception as e:
        module.fail_json(msg=f"Could not fetch page rules from Cloudflare: {str(e)}", **result)

    result['new_rule'] = {
        'targets': [
            {
                "constraint": {
                    "operator": "matches",
                    "value": module.params['target_url']
                },
                "target": "url"
            }
        ],
        'actions': module.params['actions'],
        'priority': module.params['priority'],
        'status': "active" if module.params['enabled'] else "disabled"
    }

    if module.check_mode:
        module.exit_json(**result)

    if module.params['state'] == 'present':
        if len(result['old_rule'].keys()) == 0:
            try:
                result['new_rule'] = cf.page_rules.create(zone_id=zone_id, **result['new_rule']).to_dict()
                result['changed'] = True
            except Exception as e:
                module.fail_json(msg=f"Could not create page rule: {str(e)}", **result)
        else:
            result['new_rule']['priority'] = calculate_new_priority(
                result['old_rule']['priority'],
                result['new_rule']['priority'], len(rules)
            )
            if (not compare_rule_actions(result['old_rule']['actions'], result['new_rule']['actions'])) or \
                    (result['new_rule']['priority'] != result['old_rule']['priority']) or \
                    (result['new_rule']['status'] != result['old_rule']['status']):
                try:
                    result['new_rule'] = cf.page_rules.update(
                        zone_id=zone_id,
                        pagerule_id=result['old_rule']['id'],
                        **result['new_rule']).to_dict()
                    result['changed'] = True
                except Exception as e:
                    module.fail_json(msg=f"Could not edit page rule: {str(e)}", **result)
    elif module.params['state'] == 'absent':
        if len(result['old_rule'].keys()) > 0:
            try:
                cf.page_rules.delete(zone_id=zone_id, pagerule_id=result['old_rule']['id'])
                result['changed'] = True
            except Exception as e:
                module.fail_json(msg=f"Could not delete page rule: {str(e)}", **result)
        result['new_rule'] = {}

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
