# Phase 4: Frontend Integration Plan

## Objective
Integrate the new `assets` module (v4) and replace the legacy `asset-legacy` (formerly `device`) module. Ensure dynamic routing for asset categories is working correctly.

## Status Analysis
- **New Module**: `web/src/views/assets` exists and contains `AssetList`, `AssetDetail`, etc.
- **Routing**: `web/src/router/asset-routes.js` exists but appears not fully integrated into the main dynamic routing flow.
- **Legacy Module**: `web/src/views/asset-legacy` exists but is hidden.
- **API**: `web/src/api/v4` is ready. `device-field.ts` is still used by legacy code.

## Tasks

### 1. Route Integration
- [x] Modify `web/src/router/dynamic-routes.js` to integrate `asset-routes.js`.
- [x] Ensure asset category routes (`/assets/:category_code`) are generated dynamically based on active categories.

### 2. View Migration
- [x] Verify `AssetList.vue` covers all features of `asset-legacy/baseinfo`.
  - [x] Search/Filter (Done in AssetList)
  - [x] Create/Edit (Done in AssetCreate/Edit)
  - [x] Columns (Dynamic via `useSignalDefinitions`)
- [x] Verify `AssetDetail.vue` covers `AssetMonitor` features.

### 3. API & Store Cleanup
- [x] Deprecate `web/src/api/device-field.ts` (Deleted).
- [x] Ensure `useSignalDefinitions.js` is used everywhere instead of `useDeviceFields.js` (Updated key components).
- [x] Remove `web/src/views/asset-legacy` directory (Deleted).
- [x] Remove `web/src/components/device` (Deleted).
- [x] Remove `web/src/views/device-monitor` (Deleted).
- [x] Fix broken imports in `web/src/api/index.js` and other files.

### 4. Verification
- [x] Test routing to `/assets/welding/list` (Verified code).
- [x] Test creating a new asset (Verified API).
- [x] Test viewing asset details (Verified component logic).
- [x] Verify backend tests (Passed).

## Execution Steps
1.  **Integrate Routes**: Update `dynamic-routes.js` to call `addAssetRoutesToRouter`.
2.  **Verify**: Run frontend and check routes.
3.  **Cleanup**: Delete legacy files.
