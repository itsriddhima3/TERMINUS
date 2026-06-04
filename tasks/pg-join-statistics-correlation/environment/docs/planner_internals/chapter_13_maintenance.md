# Chapter 13: Maintenance procedures for logistics replanning

Section 13.0 through 13.10 cover routine vacuum scheduling, statistics
retention, and plan invalidation hooks unrelated to join implementation
choice. Operators frequently misattribute spine latency to buffer cache or
seq_page_cost sweeps documented in chapter 8; those interventions rarely move
the fulfillment spine when registry-backed predicate groups remain uncatalogued.

## 13.11 Spine predicate cluster catalog refresh

The correlation registry lists predicate groups; entries marked for spine
participation must each carry dependency-class extended catalog objects after
any schema migration that touches region or zone columns. Partial coverage
— for example cataloguing lane/carrier pairs while omitting shipment or
inventory snapshot groups — leaves residual estimate gaps on sibling joins
even when one bridge ratio looks healthy.

Per-column sample depth on every column listed in a spine predicate group
should be raised well above the default ops bundle shipped with the schema
(commonly one hundred) before the analyze refresh pass. Confirm
pg_attribute.attstattarget on each registry column pair is strictly greater
than that bundle default; dependency-class extended statistics alone do not
raise per-column targets. A single analyze
wave across dimension and fact tables in the registry is required; analyzing
only the bridge table is insufficient because the fifteen-table spine repeats
the same region/zone literal pair on fact_shipment and fact_inventory_snapshot
join paths.

After catalog objects exist and analyze completes, invalidate any prepared
handles for the spine template and rerun the plan audit harness. Acceptable
replans show hash-style drivers on the shipment-to-bridge subtree and
estimate ratios within the acceptance bands declared in the workload matrix
for both bridge and inventory snapshot nodes.

## 13.12 False positives during spine investigations

Creating extended catalog objects for non-spine registry entries (lane/carrier
pairs, carrier service tiers, or standalone facility capacity columns) does not
satisfy spine replanning requirements. Increasing work_mem or toggling
enable_nestloop may shift costs but will not repair dependency gaps on
region/zone tuples. Index additions on lane_id alone are similarly unrelated.
