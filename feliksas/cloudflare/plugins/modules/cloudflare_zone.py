#!/usr/bin/env python3

import traceback
from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.basic import AnsibleModule

try:
    from cloudflare import Cloudflare
    from cloudflare.types.zones import zone_create_params
except ImportError:
    Cloudflare = None
    zone_create_params = None
    HAS_CLOUDFLARE = False
    CLOUDFLARE_IMPORT_ERROR = traceback.format_exc()
else:
    HAS_CLOUDFLARE = True
    CLOUDFLARE_IMPORT_ERROR = None

__metaclass__ = type

DOCUMENTATION = r'''
---
module: cloudflare_zone
short_description: Cloudflare Zone management module
version_added: "1.0.0"

description: Module for creating Cloudflare zones
requirements:
  - python-cloudflare >= 4.1.0
  
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
      account:
        description: The account the zone belongs to
        type: dict
        returned: success
        contains:
          id:
            description: (Optional) Cloudflare account ID
            type: str
            returned: success
            sample: 3973f6861c3ceb48ff96a33cec4d02e2
          name:
            description: (Optional) Cloudflare account name
            type: str
            returned: success
            sample: My Cloudflare account
      activated_on:
        description: The last time proof of ownership was detected and the zone was made active
        type: str
        returned: success
        sample: "2020-10-21T13:38:10.816183+00:00"
      created_on:
        description: When the zone was created
        type: str
        returned: success
        sample: "2020-10-21T13:38:10.816183+00:00"
      development_mode:
        description: The interval (in seconds) from when development mode expires (positive number) or last expired (negative number) for the domain. If development mode has never been enabled, this value is 0.
        type: float
        returned: success
        sample: 0.0
      meta:
        description: Metadata about the zone
        type: dict
        returned: success
        contains:
          cdn_only:
            description: (Optional) The zone is only configured for CDN
            type: bool
            returned: success
          custom_certificate_quota:
            description: (Optional) Number of Custom Certificates the zone can have
            type: int
          dns_only:
            description: (Optional) The zone is only configured for DNS
            type: bool
          foundation_dns:
            description: (Optional) The zone is setup with Foundation DNS
            type: bool
          page_rule_quota:
            description: (Optional) Number of Page Rules a zone can have
            type: int
          phishing_detected:
            description: (Optional) The zone has been flagged for phishing
            type: bool
      modified_on:
        description: When the zone was last modified
        type: str
        returned: success
        sample: "2020-10-21T13:38:10.816183+00:00"
      name:
        description: The domain name
        type: str
        returned: success
        sample: example.com
      name_servers:
        description: The name servers Cloudflare assigns to a zone
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
      original_dnshost:
        description: DNS host at the time of switching to Cloudflare
        type: str
        returned: success
      original_registrar:
        description: Registrar for the domain at the time of switching to Cloudflare
        type: str
        returned: success
        sample: "godaddy.com, llc (id: 146)"
      owner:
        description: The owner of the zone
        type: dict
        returned: success
        contains:
          id:
            description: (Optional) Cloudflare zone owner account ID
            type: str
            returned: success
            sample: 3973f6861c3ceb48ff96a33cec4d02e2
          name:
            description: (Optional) Cloudflare zone owner account name
            type: str
            returned: success
            sample: My Cloudflare account
          type:
            description: (Optional) Cloudflare zone owner account type
            type: str
            returned: success
            sample: user
      paused:
        description: (Optional) Indicates whether the zone is only using Cloudflare DNS services. A true value means the zone will not receive security or performance benefits.
        type: bool
        returned: success
      status:
        description: The zone status on Cloudflare.
        type: str
        returned: success
        sample: active
      type:
        description: (Optional) A full zone implies that DNS is hosted with Cloudflare. A partial zone is typically a partner-hosted zone or a CNAME setup.
        type: str
        returned: success
        sample: full
      vanity_name_servers:
        description: (Optional) An array of domains used for custom name servers. This is only available for Business and Enterprise plans.
        type: list
        returned: success
        elements: str
        sample:
          - dns1.example.com
          - dns2.example.com
      verification_key:
        description: (Optional) Verification key for partial zone setup.
        type: str
        returned: success
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


def run_module():
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

    if not HAS_CLOUDFLARE:
        module.fail_json(
            msg=missing_required_lib('cloudflare'),
            exception=CLOUDFLARE_IMPORT_ERROR
        )

    cf = Cloudflare()
    zones = None
    try:
        zones = cf.zones.list(name=module.params['name'])
    except Exception as e:
        module.fail_json(msg=f"Unable to fetch zone from Cloudflare: {str(e)}", **result)

    for zone in zones:
        if zone.name == module.params['name']:
            result['zone'] = zone.to_dict()
            break

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
                result['zone'] = new_zone.to_dict()
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
