"""Inventory DMA datasets: dedupe by content, map usage to lectures/homework only."""
import os, re, json, hashlib, sqlite3, csv, collections
ROOTS = {'pl': '/Users/matthewzeidenberg/pl-nyu-cs479', 'lec': '/Users/matthewzeidenberg/dma-lecture-content'}
SKIP = {'rubric.json','package.json','package-lock.json','tsconfig.json','devcontainer.json','third-party-licenses.json',
        'manifest.json','image_map.json','edstem_inventory.json','edstem_inventory_003.json','challenges_meta.json',
        'challenges_meta_003.json','equivalent_solutions.json'}
EXT = ('csv','db','sqlite','json','tsv')
files = collections.defaultdict(lambda: {'paths': [], 'uses': set()})
def pl_use(p):
    q = p.split('/questions/')[1].split('/')[0]
    m = re.match(r'Lecture(\d+)_(.*)', q)
    if m: return ('lecture', int(m.group(1)))
    m = re.match(r'HW(\d+)([A-E]?)$', q)
    if m: return ('hw', int(m.group(1)))
    return None  # quizzes, exams, practice/sample finals: not listed
for key, root in ROOTS.items():
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in ('.git','tests','_build','node_modules','datasets','tools')]
        for f in fn:
            if f.lower().rsplit('.',1)[-1] not in EXT or f.startswith('info') or f in SKIP: continue
            if 'grading_context' in f or 'deterministic' in f: continue
            p = os.path.join(dp, f)
            if key == 'pl' and '/questions/' not in p: continue
            h = hashlib.md5(open(p,'rb').read()).hexdigest()
            e = files[(f, h)]; e['paths'].append(p)
            if key == 'pl':
                u = pl_use(p)
                if u: e['uses'].add(u)
# lecture notebooks that mention a file name
nbs = {}
for dp, dn, fn in os.walk(ROOTS['lec'] + '/notebooks'):
    for f in fn:
        m = re.match(r'lecture-(\d+)', f)
        if f.endswith('.ipynb') and m: nbs[int(m.group(1))] = open(os.path.join(dp, f)).read()
for (name, h), e in files.items():
    for n, txt in nbs.items():
        if name in txt: e['uses'].add(('lecture', n))
print(len(files), 'files found')
json.dump({f'{n}|{h}': {'paths': e['paths'], 'uses': sorted(e['uses'])} for (n,h),e in files.items()}, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'inventory.json'),'w'), indent=1)
