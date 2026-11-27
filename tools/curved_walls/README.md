# curved_walls

`geom.py`: a curved or freeform building over Tower City's `tc_kit` (run inside Blender; tc_kit is imported, never edited).

- The outer face is ONE closed counter-clockwise polyline built from named runs (`Outline`). Each wall, lining, glass pane, frame
  and portal is a piece between two run positions and two offsets, on mitred offset lines, so curved and angled walls meet with
  no gaps or overlaps.
- `run_walls(...)` builds a run's wall, its lining and its openings (ribbon / glass / door / backdoor / slider / bay / glassbay).
  The wall top and lining tops can follow a sloped or curved roof `f(x, y)`. A `band` puts a different material on the wall
  above a height (the fascia band). Portals cover an opening across runs of facets, up to 8 m of chord or 35 degrees of turn,
  so a curved ribbon window costs a few portals instead of one per facet.
- `ring_grid`: a sloped or curved ceiling or roof over a star-shaped polygon.
- `poly_rail`: a glass balustrade with one continuous shoe and top rail.
- `slab`, `clip_poly`, `offset_edges`.

A flat leaf (a door, a roll-up, a slider) must sit on ONE straight facet. Force a chord into the outline at the leaf's exact width
(see `blockboyz_truckclub/tools/club_plan.py`: `CHORDS`, `along()`).
