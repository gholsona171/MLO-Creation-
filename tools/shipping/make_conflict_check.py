"""make_conflict_check.py: writes the buyer's conflict check (<resource>/tools/check_conflicts.ps1) for ANY MLO we ship.
Every shipped MLO carries one (Antonio, 2026-10-24). Call it from the build's assemble step, after the stream folder is final, so the
list is always this build's own files - never a hand-kept list.

  py -3 make_conflict_check.py --stream <res>/stream --res <resource folder name> --name "<Map name>"
       --area "<where it sits, street names + x y>" [--family <regex>] [--refs a,b,c] [--skip other_res,...] [--out <path>]

  --stream  the resource's stream folder; every file NOT starting with --ours (default: tc_) and not _manifest.ymf is listed
            (those are the Rockstar files we replace; our own files never clash by name)
  --family  regex of Rockstar file-name families for the area, to also flag same-area files with other names
            (e.g. '^(hei_|hi@|ma@)?(dt1_11|dt1_12)'); empty = off
  --refs    IPL / interior names a script might load there (e.g. ex_dt1_11_office,imp_dt1_11_cargarage)
  --skip    our other resources in the package (the main one is always skipped)
  --kind    map (default: the Rockstar files we replace, see --ours) | props (a script or prop pack that streams its OWN models:
            EVERY stream file is listed, because the clash is another resource streaming the same names, e.g. an older copy of
            the same script; template check_conflicts_props.ps1.in, --area is then the closing line the buyer reads)
Template: check_conflicts.ps1.in next to this file. Output is CRLF (a Windows PowerShell file). Prove it on a planted conflict
(a fake resource holding one listed file + one script naming a --refs entry) before shipping: both must be reported."""
import argparse, os, re
here = os.path.dirname(os.path.abspath(__file__))
a = argparse.ArgumentParser()
a.add_argument('--stream', required=True); a.add_argument('--res', required=True); a.add_argument('--name', required=True)
a.add_argument('--area', required=True); a.add_argument('--family', default=''); a.add_argument('--refs', default='')
a.add_argument('--skip', default=''); a.add_argument('--ours', default='tc_'); a.add_argument('--out')
a.add_argument('--kind', default='map', choices=['map', 'props']); a.add_argument('--template')
o = a.parse_args()
# A path Windows Python cannot see (e.g. Git Bash's /c/...) made os.walk return nothing and wrote a check with 0 files (2026-11-09).
assert os.path.isdir(o.stream), f'stream folder not found: {o.stream} (on Windows use C:\\... paths, not /c/...)'
if not o.template: o.template = os.path.join(here, 'check_conflicts_props.ps1.in' if o.kind == 'props' else 'check_conflicts.ps1.in')
# Every streamed game file anywhere under stream/ (subfolders too: bought resources keep ymap/, ybn/, ytyp/ ... folders, and the
# old top-level listdir wrote those FOLDER names into the check instead of the files, 2026-11-09 17mov). Data files loaded through
# data_file (.meta, .xml, .dat) are not matched by name, so they are left out, and so is the package's own _manifest*.ymf.
STREAMED = {'.ymap', '.ytyp', '.ybn', '.ydr', '.ydd', '.yft', '.ytd', '.ycd', '.ynd', '.ynv', '.ymt', '.ypt', '.awc'}
names = sorted({f for _, _, fs in os.walk(o.stream) for f in fs
                if os.path.splitext(f)[1].lower() in STREAMED and not f.lower().startswith('_manifest')
                and (o.kind == 'props' or not f.lower().startswith(o.ours.lower()))})
skip = '|'.join(re.escape(r) for r in [o.res] + [s for s in o.skip.split(',') if s])
refs = ','.join("'" + r.replace("'", "''") + "'" for r in o.refs.split(',') if r)
s = open(o.template, encoding='utf-8').read()
for k, v in {'@@FILES@@': '\n'.join(names), '@@NAME@@': o.name, '@@RES@@': o.res, '@@AREA@@': o.area,
             '@@FAMILY@@': o.family.replace("'", "''"), '@@REFS@@': refs, '@@SKIP@@': r'[\\/](' + skip + r')[\\/]'}.items():
    s = s.replace(k, v)
assert '@@' not in s, 'template placeholder left unfilled'
out = o.out or os.path.join(os.path.dirname(os.path.abspath(o.stream)), 'tools', 'check_conflicts.ps1')
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, 'w', encoding='utf-8', newline='\r\n') as f: f.write(s)
print(f'CONFLICT_CHECK {out}: {len(names)} ' + ('streamed files listed' if o.kind == 'props' else 'replaced Rockstar files listed'))
