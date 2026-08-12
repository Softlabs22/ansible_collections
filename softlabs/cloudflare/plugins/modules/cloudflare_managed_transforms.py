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
module: cloudflare_managed_transforms
short_description: Cloudflare Managed Transforms management module
version_added: "1.8.3"

description: >
  Module for managing Cloudflare Managed Transforms settings for a zone.

requirements:
  - python-cloudflare >= 4.1.0

options:
    zone_name:
        description: Zone domain name. Specify when creating zone-scoped rulesets. Mutually exclusive with O(account_id).
        required: true
        type: str
    enabled_request_headers:
        description: |
          List of request headers rules to enable. Possible values are:
          C(add_bot_protection_headers),
          C(add_client_certificate_headers),
          C(add_visitor_location_headers),
          C(remove_visitor_ip_headers),
          C(add_true_client_ip_headers),
          C(add_waf_credential_check_status_header),
        required: false
        type: list
        elements: str
    enabled_response_headers:
        description: |
          List of response headers rules to enable. Possible values are:
          C(remove_x-powered-by_header),
          C(add_security_headers)
        required: false
        type: list
        elements: str

author:
    - Andrey Ignatov (andrey.ignatov@agcsoft.com)
'''

EXAMPLES = r'''
'''

RETURN = r'''

'''


def run_module():
    module_args = dict(
        zone_name=dict(type='str', required=True),
        enabled_request_headers=dict(type='list', required=False, default=[]),
        enabled_response_headers=dict(type='list', required=False, default=[]),
    )

    result = dict(
        changed=False,
        managed_transforms={},
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
    managed_transforms = None
    try:
        zones = cf.zones.list(name=module.params['zone_name'])
        for z in zones:
            if z.name == module.params['zone_name']:
                zone_id = z.id
                break
        if zone_id is None:
            module.fail_json(msg=f"Zone '{module.params['zone_name']}' does not exist", **result)

        managed_transforms = cf.managed_transforms.list(zone_id=zone_id)

    except Exception as e:
        module.fail_json(msg=f"Could not fetch managed rules from Cloudflare: {str(e)}", **result)

    available_request_headers = [x.id for x in managed_transforms.managed_request_headers]
    available_response_headers = [x.id for x in managed_transforms.managed_response_headers]

    for header in module.params['enabled_request_headers']:
        if header not in available_request_headers:
            module.fail_json(msg=f"Managed transform '{header}' is not available for this zone", **result)

    for header in module.params['enabled_response_headers']:
        if header not in available_response_headers:
            module.fail_json(msg=f"Managed rule '{header}' is not available for this zone", **result)

    for request_header in managed_transforms.managed_request_headers:
        should_enable = request_header.id in module.params['enabled_request_headers']

        if should_enable != request_header.enabled:
            if should_enable and any(x in module.params['enabled_request_headers'] for x in request_header.conflicts_with):
                module.fail_json(
                    msg=f"Managed transform {request_header.id} conflicts with "
                        f"{request_header.conflicts_with} and cannot be enabled",
                    **result,
                )

            request_header.enabled = should_enable
            result["changed"] = True

    for response_header in managed_transforms.managed_response_headers:
        should_enable = response_header.id in module.params['enabled_response_headers']

        if should_enable != response_header.enabled:
            if should_enable and any(x in module.params['enabled_response_headers'] for x in response_header.conflicts_with):
                module.fail_json(
                    msg=f"Managed transform {response_header.id} conflicts with "
                        f"{response_header.conflicts_with} and cannot be enabled",
                    **result,
                )

            request_header.enabled = should_enable
            result["changed"] = True

    result["managed_transforms"] = managed_transforms.to_dict()

    if module.check_mode:
        module.exit_json(**result)

    if result['changed']:
        try:
            resp = cf.managed_transforms.edit(
                zone_id=zone_id,
                managed_request_headers=managed_transforms.managed_request_headers,
                managed_response_headers=managed_transforms.managed_response_headers
            )
            result['managed_transforms'] = resp.to_dict()
        except Exception as e:
            module.fail_json(msg=f"Failed to edit managed transforms in Cloudflare: {str(e)}", **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
