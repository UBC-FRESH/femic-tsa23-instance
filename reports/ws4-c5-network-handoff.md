# TSA 23 c5 road-network handoff

Date: 2026-10-29

This is the single index for the planned TSA 23 road network and its WS4
evidence.  It records what was built, what was tested, what was rejected, and
what remains open.  The detailed sources remain in the linked reports and the
fresh-road example.

## Network

- Source work: `fresh-road/examples/tsa23_c5_network/`
- Pattern: 600 m square lattice with one 45-degree diagonal per cell, matching
  the c5 `RDTYPE='N'` geometry.
- Potential-grid filter: AOI raster mask, existing-road proximity, lakes/FWA
  rivers/protected areas, dangling edges, tiny components.
- Existing roads: paved public DRA + active/pending FTEN resource roads.
- Mills: three operating 100 Mile House mills (`95`, `694`, `733`).  Williams
  Lake mills are 25–36 km outside TSA 23 and are not destinations here.
- Existing build cost: 0.
- Potential classes: four identical-geometry variants; all share the c5 `N`
  construction cost because c5 has only one new-road construction coefficient.
- Final network: one mill-connected component, 102,128 / 102,128 blocks linked
  to their nearest node, 0 unrouted.
- Route config: `config/ws4/route_c5.yaml`.
- Route tables: `runtime/ws4/roads_c5/` (generated; ignored by git).
- Map layers: `fresh-road/examples/tsa23_c5_network/ws4_map/` (large GeoJSON
  ignored); the old 4 km grid and DRA-only orphan layers were removed.

The DRA-only orphan components are **not** part of this network.  The 36
DRA-only no-route blocks were source-graph fragments, not isolated THLB blocks;
the c5 network routes all of them.

## WS4 evidence

| Run | Result | Record |
|---|---|---|
| Report-only c5 routing, 102,128 blocks | 99,541 linked/routed, 0 no-linkage, median 52.6 km to nearest mill | `fresh-road/examples/tsa23_c5_network/ws4_report/` |
| 5-year simulation, 2,000-block schedule | 0 unrouted route rows; 44.66 km average haul; build 28.98 M, haul 21.67 M, maintenance 11.73 M, total 62.38 M CAD | `fresh-road/examples/tsa23_c5_network/ws4_sim/` |
| c5 accounting on existing `risk_opt_final` schedule | 714 blocks, 0 unrouted; build 11.23 M, haul 60.89 M, maintenance 4.56 M, total 76.68 M CAD; product accounts identical to base | `reports/ws4-route-c5-risk-final.md` |
| Road-aware optimizer scenario, 10 M build bound | 100 iterations, 2,031 blocks, 0 unrouted, build 27.41 M; target not met; benchmark only | `reports/ws4-road-aware-opt.md` |

The product accounts in the no-road and routed runs are identical; only
`route.*` accounts are added.  The route build account is charged when a
potential segment is first used.

## Rejected approaches

- `initial_roads: existing` on the full 465k-segment network: 10 blocks took
  100 s; not viable for optimizer iterations.
- Reduced network from only previously used potential roads: 7,587 unrouted
  route rows under a changed schedule; rejected.
- DRA-only baseline: 36 blocks / 189,557 ledger volume unrouted; retained only
  as evidence of DRA source gaps, not as the access baseline.
- The old 4 km potential grid: replaced by the c5 600 m lattice.

## Open decisions

1. A real road budget or objective if road costs should influence planning.
2. A four-class construction-cost ladder; c5 provides only one `N` coefficient.
3. Product eligibility / mill demand for the three mills.
4. Public cliff/rock masking; lakes, FWA rivers, and protected areas are applied.
5. Publishing the runtime route tables through DataLad or a release bundle.

No WS4 objective, constraint, growth, solver, or compiled dataset was changed
in the network/route work.  The road-aware scenario is a separate target file.
