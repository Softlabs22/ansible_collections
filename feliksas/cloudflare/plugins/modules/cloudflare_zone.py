#!/usr/bin/env python3

from cloudflare import Cloudflare
from cloudflare.types.zones import Zone, zone_create_params
from ansible.module_utils.basic import AnsibleModule


__metaclass__ = type

DOCUMENTATION = r'''
---
module: cloudflare_zone
short_description: Cloudflare Zone management module
version_added: "1.0.0"

description: Module for creating Cloudflare zones

options:
    name:
        description: Root domain name of new zone
        required: true
        type: str
    state:
        description: Desired zone state
        choices: ['present', 'absent']
        default: present
        required: false
        type: str
    account_id:
        description: Cloudflare account ID to create new zone in
        required: true
        type: str
    type:
        description: Cloudflare zone type
        choices: ['full', 'partial', 'secondary']
        default: full
        required: false
        type: str
author:
    - Andrey Ignatov (feliksas@feliksas.lv)
'''

EXAMPLES = r'''
- name: Create zone "example.com"
  feliksas.cloudflare.cloudflare_zone:
    name: example.com
    account_id: 3973f6861c3ceb48ff96a33cec4d02e2

- name: Create secondary zone "example.com"
  feliksas.cloudflare.cloudflare_zone:
    name: example.com
    account_id: 3973f6861c3ceb48ff96a33cec4d02e2
    type: secondary

- name: Ensure that zone "example.com" does not exist
  feliksas.cloudflare.cloudflare_zone:
    name: example.com
    account_id: 3973f6861c3ceb48ff96a33cec4d02e2
    state: absent
'''

RETURN = r'''
zone:
    description: Cloudflare zone object
    type: dict
    returned: success
    contains:
      id:
        description: Cloudflare zone ID
        type: str
        returned: success
        sample: 2c42e8bcf86ab98eaa9ea5906f478948
      account:
        description: Cloudflare account information
        type: dict
        returned: success
        contains:
          id:
            description: Cloudflare account ID
            type: str
            returned: success
            sample: 3973f6861c3ceb48ff96a33cec4d02e2
          name:
            description: Cloudflare account name
            type: str
            returned: success
            sample: My Cloudflare account
      activated_on:
        description: Cloudflare zone activation date in ISO8601 format
        type: str
        returned: success
        sample: "2020-07-03T10:10:15.339911+00:00"
      created_on:
        description: Cloudflare zone creation date in ISO8601 format
        type: str
        returned: success
        sample: "2020-07-03T10:10:15.339911+00:00"
      modified_on:
        description: Cloudflare zone modification date in ISO8601 format
        type: str
        returned: success
        sample: "2020-07-03T10:10:15.339911+00:00"
      name:
        description: Cloudflare zone name
        type: str
        returned: success
        sample: example.com
      name_servers:
        description: Cloudflare zone allocated name servers
        type: list
        returned: success
        elements: str
        sample:
          - rosalyn.ns.cloudflare.com
          - thaddeus.ns.cloudflare.com
      original_name_servers:
        description: Cloudflare zone original name servers
        type: list
        returned: success
        elements: str
        sample:
          - ns1.digitalocean.com
          - ns2.digitalocean.com
      original_registrar:
        description: Cloudflare zone registrar
        type: str
        returned: success
        sample: "godaddy.com, llc (id: 146)"
      owner:
        description: Cloudflare zone owner account information
        type: dict
        returned: success
        contains:
          id:
            description: Cloudflare zone owner account ID
            type: str
            returned: success
            sample: 3973f6861c3ceb48ff96a33cec4d02e2
          name:
            description: Cloudflare zone owner account name
            type: str
            returned: success
            sample: My Cloudflare account
          type:
            description: Cloudflare zone owner account type
            type: str
            returned: success
            sample: user
      paused:
        description: Cloudflare zone pause flag
        type: bool
        returned: success
      status:
        description: Cloudflare zone status
        type: str
        returned: success
        sample: active
      type:
        description: Cloudflare zone type
        type: str
        returned: success
        sample: full
      plan:
        description: Cloudflare zone plan information
        type: dict
        returned: success
        contains:
          id:
            description: Cloudflare zone plan ID
            type: str
            returned: success
            sample: 0feeeeeeeeeeeeeeeeeeeeeeeeeeeeee
          name:
            description: Cloudflare zone plan name
            type: str
            returned: success
            sample: Free Website
'''


def populate_zone_dict(zone: Zone) -> dict:
    target_zone = {
        "id": zone.id,
        "account": {
            "id": zone.account.id,
            "name": zone.account.name,
        },
        "activated_on": zone.activated_on.isoformat() if zone.activated_on is not None else "",
        "created_on": zone.created_on.isoformat(),
        "modified_on": zone.modified_on.isoformat(),
        "name": zone.name,
        "name_servers": zone.name_servers,
        "original_name_servers": zone.original_name_servers if zone.original_name_servers is not None else [],
        "original_registrar": zone.original_registrar if zone.original_registrar is not None else "",
        "owner": {
            "id": zone.owner.id if zone.owner.id is not None else "",
            "name": zone.owner.name if zone.owner.name is not None else "",
            "type": zone.owner.type if zone.owner.type is not None else "",
        },
        "paused": zone.paused if zone.paused is not None else False,
        "status": zone.status if zone.status is not None else "",
        "type": zone.type if zone.type is not None else "",
        "plan": {
            "id": zone.plan.get("id", ""),
            "name": zone.plan.get("name", ""),
        }
    }
    return target_zone


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        name=dict(type='str', required=True),
        account_id=dict(type='str', required=True),
        state=dict(type='str', required=False, default='present', choices=['present', 'absent']),
        type=dict(type='str', required=False, default='full', choices=['full', 'partial', 'secondary']),
    )

    result = dict(
        changed=False,
        zone={},
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    cf = Cloudflare()
    zones = None
    try:
        zones = cf.zones.list(name=module.params['name'])
    except Exception as e:
        module.fail_json(msg=f"Unable to fetch zone from Cloudflare: {str(e)}", **result)

    for zone in zones:
        if zone.name == module.params['name']:
            target_zone = populate_zone_dict(zone)
            result['zone'] = target_zone

    if module.check_mode:
        module.exit_json(**result)

    if module.params['state'] == 'present':
        if len(result["zone"].keys()) == 0:
            new_zone = None
            if module.params.get('account_id', None) is None:
                module.fail_json(msg=f"'account_id' must be specified when 'create' is set to true", **result)
            try:
                new_zone = cf.zones.create(
                    name=module.params['name'],
                    account=zone_create_params.Account(
                        id=module.params['account_id'],
                    ),
                    type=module.params['type'],
                )
            except Exception as e:
                module.fail_json(msg=f"Could not create new zone: {str(e)}", **result)
            if new_zone is not None:
                result['zone'] = populate_zone_dict(new_zone)
            else:
                module.fail_json(msg=f"BUG: Cloudflare zone creation request did not return zone object", **result)
            result['changed'] = True
    elif module.params['state'] == 'absent':
        if len(result["zone"].keys()) > 0:
            try:
                cf.zones.delete(zone_id=result['zone']['id'])
                result['changed'] = True
            except Exception as e:
                module.fail_json(msg=f"Could not delete zone: {str(e)}", **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
