# Slot binding

Catalog labels in `/app/data/sku_catalog.json` include canonical slot keys used when seeding opening counts.

## Legacy routing

Older dashboards used shortened slot identifiers distinct from catalog keys. Bootstrap seeding may populate more than one Redis key per label during migration windows.

## Commit registry

`/app/config/script_registry.toml` names a primary commit body for live lanes and separate archive entries for cold-path tooling.
