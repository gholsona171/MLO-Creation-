# Prints the photo set viewpoints as lines "name x y z tx ty tz fov" (world coords). JC rooms are given in the JC lot frame (u, v, z)
# from JusticeCenter/work/jc_frame.py (origin 335.87, -1640.11, heading 50); the merged spots are plain world coords.
import math
OX, OY, H = 335.87, -1640.11, math.radians(50.0)
def W(u, v): return (OX + u * math.cos(H) - v * math.sin(H), OY + u * math.sin(H) + v * math.cos(H))
JC = [  # name, cam u v z, target u v z, fov
    ('jc_01_exterior_plaza',      68, 6, 31.8,     30, 6, 40, 65),
    ('jc_02_exterior_aerial',     -95, -60, 95,    20, 5, 30, 55),
    ('jc_03_main_hall_galleria',  -6, 3, 30.6,     36, 8, 33, 70),
    ('jc_04_courtroom',           21, 39.5, 37.9,  28, 25, 37.3, 70),
    ('jc_05_auditorium',          27.5, 52, 31.0,  17, 43, 30.0, 70),
    ('jc_06_mayor_office',        48.5, 27.5, 73.8, 27, 19.5, 72.8, 70),
    ('jc_07_governor_office',     48.5, 27.5, 116.9, 16, 19.5, 116.0, 70),
    ('jc_08_police_lobby',        41, -29.5, 30.8, 34, -11, 30.0, 70),
    ('jc_09_police_desks',        32.2, -35.2, 30.5, 27.0, -35.2, 29.5, 70),
    ('jc_09b_detective_desks',    21.2, -35.8, 33.8, 14.5, -38.8, 32.7, 70),
    ('jc_10_restroom',            24.6, -32.5, 33.8, 32.3, -32.5, 32.5, 75),
    ('jc_11_stairwell',           36.0, 34.6, 30.5, 41.5, 33.8, 40.0, 75),
    ('jc_12_jail_cellblock',      -23.0, 45.0, 38.6, -23, 24, 35.4, 75),
]
SPOTS = [  # merged spots: roads + occlusion (cam xyz, target xyz)
    ('road_01_jc_davis_ave_south',     250.0, -1735.0, 55.0,  330.0, -1640.0, 30.0, 60),
    ('road_02_jc_street_east',         430.0, -1590.0, 33.0,  360.0, -1650.0, 30.0, 60),
    ('road_03_jc_street_north',        310.0, -1545.0, 33.0,  300.0, -1630.0, 30.0, 60),
    ('merge_04_bennys',               -150.0, -1370.0, 45.0, -210.0, -1310.0, 32.0, 60),
    ('merge_05_strawberry_carwash',     20.0, -1465.0, 45.0,   20.0, -1400.0, 29.0, 60),
    ('merge_06_davis_carwash',         120.0, -1765.0, 45.0,  172.0, -1718.0, 29.0, 60),
    ('merge_07_grove_street',           40.0, -1990.0, 50.0,  100.0, -1925.0, 21.0, 60),
    ('merge_08_hood_from_south',       260.0, -2160.0, 55.0,  340.0, -2040.0, 22.0, 60),
    ('merge_09_hood_from_east',        470.0, -2040.0, 35.0,  340.0, -2040.0, 25.0, 60),
    ('merge_10_medical_center',        290.0, -1480.0, 55.0,  344.0, -1399.0, 35.0, 60),
]
for n, u, v, z, tu, tv, tz, f in JC:
    x, y = W(u, v); tx, ty = W(tu, tv); print(f'{n} {x:.2f} {y:.2f} {z} {tx:.2f} {ty:.2f} {tz} {f}')
for n, x, y, z, tx, ty, tz, f in SPOTS: print(f'{n} {x} {y} {z} {tx} {ty} {tz} {f}')
