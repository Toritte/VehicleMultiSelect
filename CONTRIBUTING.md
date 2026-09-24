# Build from source

Use Python 3.12 with the Lupa LuaJIT 2.1 module. The current package was built with Lupa 2.8. Install the development dependency with `python -m pip install -r requirements-dev.txt`.

From the repository root:
```sh
python -m unittest discover -s tests -v
python scripts/build.py --callback-resource /path/to/wwise_flow_callbacks.lua.main --out dist
```

The Windows scanner integration test uses the Windows API and requires Windows. The build requires a locally obtained original game Wwise callback resource with SHA-256 `05BBF52978028758B39F5B91A30A695D20069CEABD774D88755F0582A296BEC9`. It is intentionally not included in this source tree. The builder rejects a different fixture. LuaJIT compilation targets the game's non-GC64 bytecode format.

Output is Vehicle-MultiSelect-v0.12.zip. Add `--noimages` to build Vehicle-MultiSelect-v0.12-noimages.zip. Both use the same game resources. The builder needs no earlier release ZIP. Maintain source directly in this repository; no source ZIP is needed.

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

Preserve the author's artwork and descriptions. Do not recreate images as part of routine packaging. See THIRD_PARTY.md for existing attribution and redistribution status.

Release updates must synchronize runtime sources, packaging metadata and documentation with the author-edited release ZIP. Record changes in docs/RELEASE_NOTES.md.
