# Ansible Collection - softlabs.cloudflare

This collection manages various resources within Cloudflare infrastructure.

Requires cloudflare-python and jsonpickle: `pip install cloudflare jsonpickle`

## Available modules

* cloudflare_account_info
* cloudflare_zone
* cloudflare_zone_info
* cloudflare_zone_setting
* cloudflare_ruleset
* cloudflare_ruleset_info
* cloudflare_ruleset_rule
* cloudflare_ruleset_rule_info
* cloudflare_page_rule
* cloudflare_rules_list
* cloudflare_rules_list_item
* cloudflare_managed_transforms

## cloudflare_ruleset_rule

Manages individual rules within Cloudflare rulesets. Supports both custom rulesets and phase entrypoints for managed WAF rules.

### Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| ref | yes | Unique reference name for the rule |
| ruleset_name | yes | Name of the ruleset, or `"entrypoint"` for phase entrypoints |
| phase | when using entrypoint | Phase for entrypoint rulesets (e.g., `http_request_firewall_managed`) |
| zone_name | yes* | Zone domain name (*mutually exclusive with account_id) |
| account_id | yes* | Account ID (*mutually exclusive with zone_name) |
| action | no | Action to perform (execute, skip, challenge, etc.) |
| action_parameters | no | Parameters for the action |
| expression | no | Filter expression for when the rule matches |
| enabled | no | Whether the rule is enabled (default: true) |
| position | no | Rule position (`index: N` or `after: "ref"`) |
| logging | no | Logging configuration |
| state | no | `present` or `absent` (default: present) |

### Examples

#### Enable Cloudflare Managed Ruleset via entrypoint

```yaml
- name: Enable Cloudflare Managed Ruleset
  softlabs.cloudflare.cloudflare_ruleset_rule:
    ref: cloudflare_managed_ruleset
    zone_name: example.com
    ruleset_name: entrypoint
    phase: http_request_firewall_managed
    action: execute
    action_parameters:
      id: "efb7b8c949ac4650a09736fc376e9aee"
    expression: "true"
    description: Enable Cloudflare Managed Ruleset
    position:
      index: 1
```

#### Enable OWASP Core Ruleset with custom filter

```yaml
- name: Enable Cloudflare OWASP Core Ruleset with custom filter
  softlabs.cloudflare.cloudflare_ruleset_rule:
    ref: cloudflare_owasp_core_ruleset
    zone_name: example.com
    ruleset_name: entrypoint
    phase: http_request_firewall_managed
    action: execute
    action_parameters:
      id: "4814384a9e5d4991b9815dcfc25d2f1f"
    expression: '(not http.request.uri.query contains "bypass")'
    description: Enable Cloudflare OWASP Core Ruleset with custom filter
    position:
      index: 2
```

#### Skip WAF for whitelisted IPs

```yaml
- name: Skip WAF for office IPs
  softlabs.cloudflare.cloudflare_ruleset_rule:
    ref: skip_whitelists_office
    zone_name: example.com
    ruleset_name: entrypoint
    phase: http_request_firewall_managed
    action: skip
    action_parameters:
      ruleset: "current"
    expression: '(ip.src in $office_ips)'
    description: "Skip WAF for office IPs"
    logging:
      enabled: true
    position:
      index: 1
```

### Supported phases

- `http_request_firewall_managed` - WAF Managed Rules
- `http_request_firewall_custom` - Custom WAF Rules
- `http_request_cache_settings` - Cache Rules
- `http_ratelimit` - Rate Limiting Rules
- `http_request_transform` - Transform Rules (request)
- `http_response_headers_transform` - Transform Rules (response headers)
- And more (see module documentation for full list)
