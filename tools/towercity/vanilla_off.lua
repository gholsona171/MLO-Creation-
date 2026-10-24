-- vanilla_off.lua: Tower City replaces the Maze Bank Tower. IPL loaders (bob74_ipl and similar) still switch on that building's
-- executive interiors - the CEO office (ex_dt1_11_office_*) sits exactly on residence floors 98-99, its desks pushing up through the
-- floor, and the CEO garages (imp_dt1_11_*) belong to the same removed building. Whatever loads them, they are switched off here
-- and kept off (a loader can re-enable them later, so this re-checks every few seconds; it does nothing once they are off).
local IPLS = {
    'ex_dt1_11_office_01a', 'ex_dt1_11_office_01b', 'ex_dt1_11_office_01c',
    'ex_dt1_11_office_02a', 'ex_dt1_11_office_02b', 'ex_dt1_11_office_02c',
    'ex_dt1_11_office_03a', 'ex_dt1_11_office_03b', 'ex_dt1_11_office_03c',
    'imp_dt1_11_cargarage_a', 'imp_dt1_11_cargarage_b', 'imp_dt1_11_cargarage_c', 'imp_dt1_11_modgarage',
}

CreateThread(function()
    while true do
        for _, ipl in ipairs(IPLS) do
            if IsIplActive(ipl) then RemoveIpl(ipl) end
        end
        Wait(5000)
    end
end)
