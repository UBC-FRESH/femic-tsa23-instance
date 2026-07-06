# TSA23 Source/Corpus Discovery Plan

## Scope

This note documents what source data will be required for TSA23 instance building,
what is currently available in FEMIC metadata/public-data, and the planned discovery
workflow. This is a planning document — no data has been materialized yet.

## Required Source Layers (Tentative)

Based on patterns from TSA29 and TFL6 instances, TSA23 will need:

1. **VRI (Vegetation Resource Inventory)** — Polygon/stand-level vegetation data
   - Expected source: BC Data Catalogue / provincial VRI
   - Format: File geodatabase or shapefiles
   - Status: Available in public-data via datalad (unverified for TSA23 extent)

2. **SiteProd** — Site productivity rasters and band maps
   - Expected source: BC Data Catalogue
   - Format: GeoTIFF + JSON bandmap
   - Status: Canonical artifacts expected to exist; need verification

3. **TSA Boundaries** — TSA23 boundary shapefile/geodatabase
   - Expected source: BC Data Catalogue (WHSE_FOREST_VEGETATION or similar)
   - Format: GDB/shapefile
   - Status: Not yet identified in public-data

4. **THLB/THNS Definitions** — Timber Harvestable Land Base boundaries
   - Expected source: Provincial inventory or TSA-specific definition
   - Status: Unknown; requires TSR document review

5. **BCDC Layers for Silviculture Planning**
   - Site Prod BC, Silviculture Activities History, etc.
   - Expected source: BC Data Catalogue API
   - Status: Not yet resolved/classified

## TSR Sources

TSA23-specific TSR documents must be discovered via FEMIC TSR indexing:

1. **Fetch TSA23 TSR registry**:
   ```powershell
   femic tsr fetch --tsa 23
   ```
   Expected: PDF documents with TSA23 timber supply policies, silviculture directives,
   area definitions, and harvest planning frameworks.

2. **Extract candidate facts**:
   ```powershell
   femic tsr extract --tsa 23
   ```
   Expected: Candidate silviculture prescriptions, retention areas, management type
   designations, and THLB/THNS boundary descriptions.

3. **Initialize reviewed overlay**:
   ```powershell
   femic tsr overlay-init --instance-root external/femic-tsa23-instance --tsa 23
   ```

## Blockers

- **TSR Fetch not attempted**: No TSA23 TSR documents have been fetched or indexed yet.
  This is the first action for P109 (source discovery phase).
- **Public-data extent unknown**: The femic-public-data submodule contains many layers
  but TSA23-specific extents have not been identified. A targeted search through BCDC
  and datalad indexes will be needed in P109.
- **Boundary files uncertain**: TSA boundary shapefiles may require a separate BCDC
  query or request from provincial data portals.

## Follow-on Tasks (P109+)

1. `femic tsr fetch --tsa 23` — Download and index TSA23 TSR documents
2. Identify and materialize VRI polygons covering TSA23 extent
3. Verify SiteProd artifacts exist for TSA23 area
4. Query BCDC for TSA23 boundary layer
5. Materialize all source layers via datalad or direct download
6. Run `femic tsr extract --tsa 23` to populate candidate facts
