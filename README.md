# ansible_collections

## 1. What is it?

This repository is used to store custom in-house developed Ansible collections.

To start developing a new collection:
1.  Clone this repository
2.  In the root directory, run `ansible-galaxy collection init <your_namespace>.<collection_name>`

For details refer to [official documentation](https://docs.ansible.com/ansible/latest/dev_guide/developing_collections_creating.html).

## 2. Testing Ansible modules
Ansible module code can be quickly tested by running it as a module, while providing a JSON with arguments on stdin:
```shell
export PYTHONPATH=/path/to/ansible_collections:$PYTHONPATH
echo "{\"ANSIBLE_MODULE_ARGS\": {\"zone_name\": \"example.com\", \"enabled_request_headers\": [\"add_visitor_location_headers\"]}}" | python3 -m softlabs.cloudflare.plugins.modules.cloudflare_managed_transforms
```

## 3. Publishing a new version of the collection
1. Ensure that you have a Galaxy token configured at `~/.ansible/galaxy_token`
2. Change dir to collection root (where `galaxy.yml` resides)
3. Bump `version` in the collection's `galaxy.yml`
4. Build collection: `ansible-collection build`
5. Publish new version: `ansible-collection publish ./new_tarball.tar.gz`