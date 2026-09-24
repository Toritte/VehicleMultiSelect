# Build from source

Use Python 3.12 with the Lupa LuaJIT 2.1 module. The current package was built with Lupa 2.8. Install the development dependency with `python -m pip install -r requirements-dev.txt`.

From the repository root:
```sh
python -m unittest discover -s tests -v
python scripts/build.py --boot-resource /path/to/boot.lua.main --out dist
```

The Windows scanner integration test uses the Windows API and requires Windows. The build requires a locally obtained original game boot resource with SHA-256 `85D7C6A9981E3288286C63BDB75E4256DCF859D6FC5F712CB72E9B329B1712E6`. It is intentionally not included in this source tree. The builder rejects a different fixture. LuaJIT compilation targets the game's non-GC64 bytecode format.

Output is the installable options ZIP and SHA256SUMS.txt under dist. The ZIP filename still identifies the verified preview lineage; changing documentation does not automatically publish or promote it to a final release. No additional source ZIP is needed: maintain the source directly in this repository.

## Repository layout
- src/: Lua runtime, guarded data changes and deployed-option detection.
- config/: supported game hashes and expected record flags.
- scripts/: archive writer and package builder.
- packaging/manifest.json: manager options and artwork references.
- assets/: author-provided original artwork, including the README banner.
- tests/: runtime simulations, resource-format checks and Windows file-reading integration.
- docs/: technical description and release notes.

## Validation
Gameplay edits require appropriate tests and game verification. Check all seven nonempty option combinations when changing selection logic. Keep private dumps, research logs, game binaries and extracted game resources out of public source uploads.

For packaging edits, compare game patch bytes with the user-verified package, verify every manifest image path and hash, and check extraction with SharpCompress 0.38.0 (used by HD2MM 1.2.1.0). Empty ZIP entries must use STORED compression. Python ZIP integrity checks alone previously missed a manager extraction problem.

Preserve the author's artwork and descriptions. Do not recreate images as part of routine packaging. See THIRD_PARTY.md and LICENSE-STATUS.md for existing attribution and redistribution status.
