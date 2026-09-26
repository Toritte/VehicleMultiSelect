# Technical walkthrough

## Startup and options
Each manager option includes a startup archive replacing the existing Wwise callback Lua resource (`core/wwise/lua/wwise_flow_callbacks`) plus empty companion files. The three wrappers share the same logic and differ in an embedded category token. The selected startup preserves return values and installs a chained update callback; v0.12 optionally delegates startup to an installed loader as described below.

After validating the game executable and game.dll hashes, the callback reads deployed archives in the game's data directory using Unicode Windows APIs. It examines only numeric 9ba626afa44a3aa3.patch_* filenames and recognizes the expected single-Wwise-resource archive layout and category tokens. It does not query or add engine resources and does not load arbitrary third-party Lua. Tokens are configuration markers, not security authentication.

The scan limits enumeration to 4,096 candidate files, skips files outside 192–131,072 bytes and caps total reads at 16 MiB. Stale deployed option archives can affect detection; remove old packages and redeploy when changing versions. No files are modified by the scan.

## Guarded data changes
For build 25480438, the settings pointer is at RVA 0x348e8f8 and the lookup table at 0x37cb600. The mod verifies the 724-byte selection-code signature at 0x146e30d, 11 groups, 149 unique records, 400-byte record stride, all expected classification flags and lookup ownership before writing.

Exosuit IDs: 27, 10, 91, 88. FRV IDs: 105, 26, 135. Tank IDs: 1, 50. Only the chosen category bits are cleared: at most nine one-byte changes in existing private writable data. Executable memory and protection settings are not changed. Classification flags may be used outside the selection UI; offline checks alone cannot establish the absence of gameplay side effects.

If a write or verification fails, rollback restores only records still owned by this operation. Foreign modifications or changed ownership prevent unsafe restoration. Failures are logged and application stops. The original update function is chained with its return values preserved; the wrapper removes itself only when it is still the active callback.

## Package metadata
manifest.json configures the manager. VehicleMultiSelect-manifest.json records file hashes, build identity and verification scope. It inventories every ZIP member except itself. No game dumps or research logs belong in the public source tree or installable package.

## Verification scope
The author reported successful standalone options operation and confirmed the artwork package. All seven option combinations are covered by offline tests. Windows file enumeration and reads were tested using a Unicode path. Package extraction was checked using the manager's SharpCompress version.

## Runtime compatibility
Boot is not replaced. Internal diagnostic labels retain the tested runtime names to preserve the verified bytecode. Other Wwise replacements require a compatible startup route.

## v0.12 optional loader startup
Each option also includes the declared mods/toritte/vehicle_multiselect resource. A winning Bingus loader discovers it; a winning Vehicle startup delegates to the recognized installed v16 payload, or starts standalone. Only one selected path initializes the original audio callbacks. Setup is guarded against repeated initialization. The v17 configuration confirmed by the author puts Bingus below Vehicle in HD2MM.

## v0.13 loader recognition
The supplied v16 and v17 payloads differ only in one ASCII digit in the diagnostic log label. Recognition normalizes exactly one two-digit loader-vNN label with API 1, then checks the complete resource SHA-256. It returns the unmodified installed bytecode. Unknown code changes, API changes, missing or duplicate labels remain rejected. This reduces metadata-only update breakage without treating arbitrary startup wrappers as loaders. Shared-resource warnings can remain because the archive identities are unchanged.
