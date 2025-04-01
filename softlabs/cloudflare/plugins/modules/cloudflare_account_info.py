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
module: cloudflare_account_info
short_description: Cloudflare Account query module
version_added: "1.3.0"

description: Module for retrieving information about a Cloudflare account
requirements:
  - python-cloudflare >= 4.1.0
  
options:
    name:
        description: Account human-readable name
        required: true
        type: str
author:
    - Andrey Ignatov (andrey.ignatov@agcsoft.com)
'''

EXAMPLES = r'''
- name: Query account "My Account"
  softlabs.cloudflare.cloudflare_account_info:
    name: My Account
  register: result
'''

RETURN = r'''
account:
  description: Account information object
  returned: success
  type: dict
  contains:
    id:
      description: Account ID
      type: str
      returned: success
      example: 3973f6861c3ceb48ff96a33cec4d02e2
    name:
      description: Account human-readable name
      type: str
      returned: success
      sample: My Account
    created_on:
      description: Account creation date
      type: str
      returned: success
      sample: 2018-08-10T08:27:39.655883+00:00
    settings:
      description: Account settings
      type: dict
      returned: success
      contains:
        abuse_contact_email:
          description: Abuse contact email to notify for abuse reports.
          type: str
          returned: success
          sample: abuse@example.com
        default_nameservers:
          description: Default nameservers to be used for new zones added to this account.
          type: str
          returned: success
          sample: cloudflare.standard
        enforce_twofactor:
          description: Indicates whether membership in this account requires that Two-Factor Authentication is enabled
          type: bool
          returned: success
        use_account_custom_ns_by_default:
          description: Indicates whether new zones should use the account-level custom nameservers by default. Deprecated in favor of DNS Settings
          type: bool
          returned: success
    type:
      description: Account type
      type: str
      returned: success
      sample: standard
'''


def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
    )

    result = dict(
        account={},
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
    accounts = None
    try:
        accounts = cf.accounts.list(name=module.params['name'])
    except Exception as e:
        module.fail_json(msg=f"Unable to fetch accounts from Cloudflare: {str(e)}", **result)

    for account in accounts:
        if account.name == module.params['name']:
            result['account'] = account.to_dict()
            break

    if module.check_mode:
        module.exit_json(**result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
