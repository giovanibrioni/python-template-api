# Example report

```markdown
# Review

## Blockers
| Severity | Location | Finding |
| --- | --- | --- |
| high | alembic/versions/c3d_add_owner.py:28 | upgrade() calls op.drop_column("owner_email") with no expand/contract |
| high | app/items/service.py:22 | create reads by name then inserts, with no unique constraint |
| high | app/items/service.py:30 | writes the row and publishes an event with no outbox or compensation |
| high | app/items/service.py:18 | tenacity retries create, and the insert has no idempotency key |

## Warnings
| Severity | Location | Finding |
| --- | --- | --- |
| medium | app/items/repository.py:40 | new filter on owner_id has no index in the migration |
| medium | app/core/config.py:18 | redis_url is not listed in .env.example |

## Script summary
- lint: pass
- architecture: pass
- orphans: pass
- env: fail
- merge-risk: fail (2 warnings)

## Not in scope
- Events: no domain event contract
```
