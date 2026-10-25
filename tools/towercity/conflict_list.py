"""conflict_list.py <stream dir> <template> <out>: writes the buyer's conflict check (tools/check_conflicts.ps1) with the
vanilla-named files of this build (everything in stream/ that is not ours: our files start with tc_; _manifest.ymf is a name every
map uses). The list is taken from the build, so the check always matches what ships. CRLF: it is a Windows PowerShell file."""
import os, sys
stream, tmpl, out = sys.argv[1:4]
names = sorted(n for n in os.listdir(stream) if not n.startswith('tc_') and n != '_manifest.ymf')
assert names and '@@FILES@@' in open(tmpl, encoding='utf-8').read()
with open(out, 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(open(tmpl, encoding='utf-8').read().replace('@@FILES@@', '\n'.join(names)))
print(f'CONFLICT_LIST {len(names)} files')
