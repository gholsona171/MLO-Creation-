# Incoming MLO pack check (field note 2026-11-19)

1. `clash.py <packs_dir> [<packs_dir>...]` - every pack's stream file names vs the server's name index
   (`cleveland_stream_index.json`: file name -> resources) and vs each other.
2. `../map_merge/mlo_scan.ps1 -Root <tree> -Out <tsv>` on the server tree and on the packs, then `overlap.py`:
   custom / `_milo_` ymap extents that overlap (vanilla road / LOD boxes are noise and are filtered).
3. Same name in two packs: md5 them. Identical = harmless; different copies of one vanilla occl / lodlights / road file
   is a merge job (`../map_merge/`).
4. Rig photo lineup (`photos/`): drop the clean packs in `[localtest]`, `refresh` + `ensure`, then
   `PL=<player id> lineup.sh <name> x y z dist height [rooms] [probe x y z]` = 4 ring shots + corner sheets of the
   biggest rooms. Read the gotchas in docs/09-field-notes.md 2026-11-19 (floats, interior 0 crash, focus, death UI).
