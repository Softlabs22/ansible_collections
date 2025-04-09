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
module: cloudflare_rules_list_item
short_description: Cloudflare Rules List items management module
version_added: "1.7.0"

description: >
  Module for managing individual items (IPs, hostnames, ASNs) in Cloudflare account-wide lists.
requirements:
  - python-cloudflare >= 4.1.0

options:
    list_name:
        description: Name of the list to manage
        required: true
        type: str
    account_name:
        description: Cloudflare account name where the list is configured
        required: true
        type: str
    kind:
        description: Kind of the list to manage
        type: str
        required: false
        default: ip
        choices:
        - ip
        - asn
        - hostname
        - redirect
    item:
        description: Item to add or remove from the list
        type: dict
        required: true
    state:
        description: Desired item state
        choices: ['present', 'absent']
        default: present
        required: false
        type: str
author:
    - Andrey Ignatov (andrey.ignatov@agcsoft.com)
'''

EXAMPLES = r'''
- name: Create a new item
  softlabs.cloudflare.cloudflare_rules_list_item:
    account_name: "My Account"
    list_name: "my_list"
    item:
      ip: 8.8.8.8
      comment: "Google DNS"
      
- name: Delete an item
  softlabs.cloudflare.cloudflare_rules_list_item:
    account_name: "My Account"
    list_name: "my_list"
    item:
      ip: 8.8.8.8
    state: absent
'''

RETURN = r'''
item:
  description: Item contents
  returned: success
  type: dict
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
        items.extend([i for i in list_page])
        if list_page.result_info is not None:
            cursor = list_page.result_info.cursors.get('after', None)
        if cursor is None:
            break
    return items


def run_module():
    module_args = dict(
        list_name=dict(type='str', required=True),
        account_name=dict(type='str', required=True),
        kind=dict(type='str', required=False, default='ip', choices=['ip', 'asn', 'hostname', 'redirect']),
        item=dict(type='dict', required=True),
        state=dict(type='str', required=False, default='present', choices=['present', 'absent']),
    )

    result = dict(
        changed=False,
        item={},
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
    target_account = None
    list_id = None
    list_items = []
    existing_item_id = None
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
            if ll.name == module.params['list_name']:
                if ll.kind != module.params['kind']:
                    module.fail_json(msg=f"Wrong kind of list: '{ll.name}' is of kind '{ll.kind}', while '{module.params['kind']}' was specified", **result)
                list_items = get_list_items(
                    cf_client=cf,
                    account_id=target_account.id,
                    list_id=ll.id
                )
                list_id = ll.id
                break
    except Exception as e:
        module.fail_json(msg=f"Unable to fetch lists from Cloudflare: {str(e)}", **result)

    if list_id is None:
        module.fail_json(f"List '{module.params['list_name']}' does not exist", **result)
    else:
        for item in list_items:
            if module.params['kind'] == 'ip':
                if item.ip == module.params['item']['ip']:
                    result['item'] = item.to_dict()
                    existing_item_id = item.id
            elif module.params['kind'] == 'asn':
                if item.asn == module.params['item']['asn']:
                    result['item'] = item.to_dict()
                    existing_item_id = item.id
            elif module.params['kind'] == 'hostname':
                if item.hostname == module.params['item']['hostname']:
                    result['item'] = item.to_dict()
                    existing_item_id = item.id
            elif module.params['kind'] == 'redirect':
                if item.redirect.source_url == module.params['item']['redirect']['source_url']:
                    result['item'] = item.to_dict()
                    existing_item_id = item.id
        result['item'].pop('id', None)
        result['item'].pop('created_on', None)
        result['item'].pop('modified_on', None)

    if module.check_mode:
        module.exit_json(**result)

    if module.params['state'] == 'present':
        if existing_item_id is None:
            try:
                cf.rules.lists.items.create(
                    list_id=list_id,
                    account_id=target_account.id,
                    body=[{
                        **module.params['item']
                    }]
                )
                result['item'] = module.params['item']
                result['changed'] = True
            except Exception as e:
                module.fail_json(msg=f"Unable to create item: {str(e)}", **result)
        else:
            if result['item'] != module.params['item']:
                try:
                    cf.rules.lists.items.delete(
                        list_id=list_id,
                        account_id=target_account.id,
                        extra_body={
                            "items": [{
                                "id": existing_item_id
                            }]
                        }
                    )
                    cf.rules.lists.items.create(
                        list_id=list_id,
                        account_id=target_account.id,
                        body=[{
                            **module.params['item']
                        }]
                    )
                    result['item'] = module.params['item']
                    result['changed'] = True
                except Exception as e:
                    module.fail_json(msg=f"Unable to replace item: {str(e)}", **result)

    elif module.params['state'] == 'absent':
        if existing_item_id is not None:
            try:
                cf.rules.lists.items.delete(
                    list_id=list_id,
                    account_id=target_account.id,
                    extra_body={
                        "items": [{
                            "id": existing_item_id
                        }]
                    }
                )
                result['item'] = {}
                result['changed'] = True
            except Exception as e:
                module.fail_json(msg=f"Unable to delete item: {str(e)}", **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
