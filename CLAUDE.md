# Ansible Collections Repo — Claude Context

GitLab: `softlabs/infra/ansible_collections` | Default branch: `master`

## Purpose

In-house Ansible Galaxy collections. Consumers install via `ansible-galaxy collection install` / `requirements.yml`.

## Collections (verified in-repo)

| Path | Namespace.name | Version (`galaxy.yml`) |
|------|----------------|------------------------|
| `softlabs/cloudflare/` | `softlabs.cloudflare` | **1.8.5** |

## Layout

```
ansible_collections/
├── softlabs/
│   └── cloudflare/          # Cloudflare DNS/WAF/transforms modules
│       ├── galaxy.yml
│       ├── plugins/modules/
│       └── README.md
├── .gitlab-ci.yml
└── README.md
```

## CI

- **Include:** `softlabs/pipelines/snippets` → `secret-scan.yml` + `review/claude-code-review.yml`
- **Stages:** `scan` → `review` → `validate`
- **`claude-code-review`** — auto on MR (`allow_failure: true`); reads this file first.

## Conventions

- New collection: `ansible-galaxy collection init <namespace>.<name>` at repo root.
- Bump `version` in `galaxy.yml` before `ansible-galaxy collection build` / `publish`.
- Do not invent collection APIs; match existing modules under `plugins/modules/`.
