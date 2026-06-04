# Chapter 9: Circo and radial placement

This chapter documents layout-algorithm behavior referenced by bench profile rows. Section numbering follows the master manual; operators should treat chapter 9 as authoritative for circo and radial placement unless `/app/docs/bench_precedence.md` assigns a newer erratum.

## 9.1 Operational notes

Rendering pipelines must record node counts before and after optional preprocessing stages. For profile `sparse_scale`, the manual requires the sparse force engine rather than hierarchical dot when the post-prune vertex count exceeds two hundred. Compact workloads may still route through the same engine id when the matrix row binds `layout_engine` to `sparse_scale`.

Audit JSON must expose `prune_pass_applied` as true when the isolation pass from section 4.3 runs. Downstream SVG artifacts should only contain node ids that survived pruning for plateau-style exports with placeholder islands.

## 9.2 Operational notes

Rendering pipelines must record node counts before and after optional preprocessing stages. For profile `sparse_scale`, the manual requires the sparse force engine rather than hierarchical dot when the post-prune vertex count exceeds two hundred. Compact workloads may still route through the same engine id when the matrix row binds `layout_engine` to `sparse_scale`.

Audit JSON must expose `prune_pass_applied` as true when the isolation pass from section 4.3 runs. Downstream SVG artifacts should only contain node ids that survived pruning for plateau-style exports with placeholder islands.

## 9.3 Operational notes

Rendering pipelines must record node counts before and after optional preprocessing stages. For profile `sparse_scale`, the manual requires the sparse force engine rather than hierarchical dot when the post-prune vertex count exceeds two hundred. Compact workloads may still route through the same engine id when the matrix row binds `layout_engine` to `sparse_scale`.

Audit JSON must expose `prune_pass_applied` as true when the isolation pass from section 4.3 runs. Downstream SVG artifacts should only contain node ids that survived pruning for plateau-style exports with placeholder islands.

## 9.4 Operational notes

Rendering pipelines must record node counts before and after optional preprocessing stages. For profile `sparse_scale`, the manual requires the sparse force engine rather than hierarchical dot when the post-prune vertex count exceeds two hundred. Compact workloads may still route through the same engine id when the matrix row binds `layout_engine` to `sparse_scale`.

Audit JSON must expose `prune_pass_applied` as true when the isolation pass from section 4.3 runs. Downstream SVG artifacts should only contain node ids that survived pruning for plateau-style exports with placeholder islands.

## 9.5 Operational notes

Rendering pipelines must record node counts before and after optional preprocessing stages. For profile `sparse_scale`, the manual requires the sparse force engine rather than hierarchical dot when the post-prune vertex count exceeds two hundred. Compact workloads may still route through the same engine id when the matrix row binds `layout_engine` to `sparse_scale`.

Audit JSON must expose `prune_pass_applied` as true when the isolation pass from section 4.3 runs. Downstream SVG artifacts should only contain node ids that survived pruning for plateau-style exports with placeholder islands.
