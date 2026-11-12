"""The building's office desk (2026-11-11 rebuild, Antonio at postal 446: "the monitors are reversed, facing the aisle while the chairs sit
on the other side", "a stray third monitor sits half in a desk", "a monitor pokes up in a desk cluster").
v_corp_officedesk is a complete workstation (survey/vanilla/v_corp_officedesk.ydr.xml): its top is z 0.84 .. 0.90, x -1.25 .. 1.25,
y -0.54 .. 0.54; the model carries its own screens (the emissive face at y -0.02 .. 0.09 points -y), keyboard (y -0.49 .. -0.10), tower
and cables (hanging to y +0.62 behind it). Its user therefore sits on the model's -y side, and the only clear part of the top is the
end x -1.25 .. -0.75. The old desk set put the chair on the +y (cable) side, added monitors facing that chair (through the built-in
screens) and stood everything on a 0.76 top (0.14 m inside the desk).
workstation(): (u, v) is the TOP's centre and h the CHAIR's heading (its front -y faces the desk: the chair sits at +chair_y along the
heading's +y). The model turns to h + 180 so its keyboard and screens face the chair; it is moved 0.08 toward the chair so its hanging
cables end where the top's back edge is. Things on the desk go only on the clear end, at the model's x FREE_X."""
import math
DESK, TOP, FREE_X, CABLES = 'v_corp_officedesk', 0.90, -1.0, 0.08
def local(u, v, h, x, y):
    t = math.radians(h); return u + x * math.cos(t) - y * math.sin(t), v + x * math.sin(t) + y * math.cos(t)
def workstation(room, u, v, h, chair, z=0.0, chair_y=1.2, items=()):
    """-> [(room, model, u, v, z, heading)]: the desk, its chair, and items [(model, y, dz, dh)] on the clear end (y along the model's
    depth: - toward the user; dh: heading added to the model's (0 = the item's front toward the user)). z: the floor."""
    m = (h + 180.0) % 360.0; cu, cv = local(u, v, h, 0.0, CABLES)
    out = [(room, DESK, cu, cv, z, m), (room, chair, *local(u, v, h, 0.0, chair_y), z, h)]
    for model, y, dz, dh in items: out.append((room, model, *local(cu, cv, m, FREE_X, y), z + TOP + dz, (m + dh) % 360.0))
    return out
