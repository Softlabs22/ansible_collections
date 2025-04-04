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

try:
    import jsonpickle
except ImportError:
    jsonpickle = None
    HAS_JSONPICKLE = False
    JSONPICKLE_IMPORT_ERROR = traceback.format_exc()
else:
    HAS_JSONPICKLE = True
    JSONPICKLE_IMPORT_ERROR = None

__metaclass__ = type

DOCUMENTATION = r'''
module: cloudflare_rules_list
short_description: Cloudflare Rules Lists management module
version_added: "1.6.0"

description: >
  Module for managing Cloudflare account-wide lists, that can be used in various rules to match a set of IPs, ASNs or hostnames.
requirements:
  - python-cloudflare >= 4.1.0
  - jsonpickle >= 3.2.2

options:
    name:
        description: Name of the list
        required: true
        type: str
    account_name:
        description: Cloudflare account name where to create the list
        required: true
        type: str
    kind:
        description: Kind of the list to create
        type: str
        required: false
        default: ip
        choices:
        - ip
        - asn
        - hostname
        - redirect
    description:
        description: An informative summary of the list
        type: str
        required: false
    items:
        description: One or more items to add to the list
        type: list
        required: false
        elements: dict
    state:
        description: Desired list state
        choices: ['present', 'absent']
        default: present
        required: false
        type: str
author:
    - Andrey Ignatov (andrey.ignatov@agcsoft.com)
'''

EXAMPLES = r'''
- name: Create an IP list
  softlabs.cloudflare.cloudflare_rules_list:
    account_name: "My Account"
    name: blocked_ips
    description: "Blocked IPs list"
    kind: ip
    items:
      - ip: 127.0.0.1
        comment: localhost
      - ip: 8.8.8.8
        comment: Google DNS
    
- name: Delete a list
  softlabs.cloudflare.cloudflare_rules_list:
    account_name: "My Account"
    name: blocked_ips
    state: absent
'''

RETURN = r'''
rules_list:
  description: List contents
  returned: success
  type: list
  elements: dict
  sample:
    - ip: 127.0.0.1
      comment: localhost
      id: 06d263ad763242db8bafb8654cd2c453
      created_on: "2025-04-03T13:00:43Z"
      modified_on: "2025-04-03T13:00:43Z"
'''


def get_list_items(cf_client: Cloudflare, account_id: str, list_id: str):
    items = []
    cursor = None
    while True:
        list_page = cf_client.rules.lists.items.list(
            list_id=list_id,
            account_id=account_id,
            cursor=cursor,
        )
        items.extend([i.to_dict() for i in list_page])
        if list_page.result_info is not None:
            cursor = list_page.result_info.cursors.get('after', None)
        if cursor is None:
            break
    return items

def compare_lists(kind, old, new):
    if kind in ('ip', 'asn', 'hostname'):
        return set([i[kind] for i in old]) == set([j[kind] for j in new])
    elif kind == 'redirect':
        return set([jsonpickle.dumps(i['redirect']) for i in old]) == set([jsonpickle.dumps(j['redirect']) for j in new])


def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        account_name=dict(type='str', required=True),
        kind=dict(type='str', required=False, default='ip', choices=['ip', 'asn', 'hostname', 'redirect']),
        description=dict(type='str', required=False),
        items=dict(type='list', elements='dict', required=False),
        state=dict(type='str', required=False, default='present', choices=['present', 'absent']),
    )

    result = dict(
        changed=False,
        rules_list={},
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

    if not HAS_JSONPICKLE:
        module.fail_json(
            msg=missing_required_lib('jsonpickle'),
            exception=JSONPICKLE_IMPORT_ERROR
        )

    cf = Cloudflare()

    accounts = None
    target_account = None
    existing_list_id = None
    try:
        accounts = cf.accounts.list(name=module.params['account_name'])
    except Exception as e:
        module.fail_json(msg=f"Unable to fetch accounts from Cloudflare: {str(e)}", **result)

    for account in accounts:
        if account.name == module.params['account_name']:
            target_account = account
            break

    if target_account is None:
        module.fail_json(f"Account '{module.params['account_name']}' does not exist", **result)

    try:
        lists = cf.rules.lists.list(account_id=target_account.id)
        for ll in lists:
            if ll.name == module.params['name']:
                result['rules_list'] = get_list_items(
                    cf_client=cf,
                    account_id=target_account.id,
                    list_id=ll.id
                )
                existing_list_id = ll.id
                break
    except Exception as e:
        module.fail_json(msg=f"Unable to fetch lists from Cloudflare: {str(e)}", **result)

    if module.check_mode:
        module.exit_json(**result)

    if module.params['state'] == 'present':
        if module.params['items'] is None:
            module.fail_json(msg="items parameter is required when state is set to 'present'", **result)
        if len(result['rules_list']) > 0:
            if not compare_lists(module.params['kind'], result['rules_list'], module.params['items']):
                try:
                    cf.rules.lists.items.update(
                        account_id=target_account.id,
                        list_id=existing_list_id,
                        body=module.params['items']
                    )
                    result['rules_list'] = module.params['items']
                    result['changed'] = True
                except Exception as e:
                    module.fail_json(msg=f"Unable to update list: {str(e)}", **result)
        else:
            try:
                new_list = cf.rules.lists.create(
                    account_id=target_account.id,
                    kind=module.params['kind'],
                    name=module.params['name'],
                    description=module.params['description'],
                )
                cf.rules.lists.items.create(
                    account_id=target_account.id,
                    list_id=new_list.id,
                    body=module.params['items']
                )
                result['rules_list'] = module.params['items']
                result['changed'] = True
            except Exception as e:
                module.fail_json(msg=f"Unable to create list: {str(e)}", **result)
    elif module.params['state'] == 'absent':
        if len(result['rules_list']) > 0:
            try:
                cf.rules.lists.delete(
                    account_id=target_account.id,
                    list_id=existing_list_id
                )
                result['rules_list'] = []
                result['changed'] = True
            except Exception as e:
                module.fail_json(msg=f"Unable to delete list: {str(e)}", **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
