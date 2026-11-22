"""Build the DMA dataset browser: site/data/*.gz plus site/catalog.js.

Usage is listed for lectures and assignments only. Quizzes, exams and
practice/sample finals are never mentioned.
"""
import base64, csv, glob, gzip, hashlib, io, json, os, re, shutil, sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, '..', '..', 'datasets')  # published by GitHub Pages
inv = json.load(open(os.path.join(HERE, 'inventory.json')))

LECTURES = {}
for f in glob.glob('/Users/matthewzeidenberg/dma-lecture-content/notebooks/lecture-*.ipynb'):
    m = re.match(r'lecture-(\d+)-(.*)\.ipynb', os.path.basename(f))
    title = m.group(2).replace('-', ' ')
    title = re.sub(r'\bsqlite\b', 'SQLite', title.capitalize())
    title = re.sub(r'\b(xml|json|numpy|mongodb|neo4j)\b',
                   lambda x: {'xml': 'XML', 'json': 'JSON', 'numpy': 'NumPy', 'mongodb': 'MongoDB', 'neo4j': 'Neo4j'}[x.group(1)], title)
    title = re.sub(r'\bpandas\b', 'pandas', title)
    LECTURES[int(m.group(1))] = title

def kind(name):
    ext = name.rsplit('.', 1)[-1].lower()
    return {'db': 'sqlite', 'sqlite': 'sqlite', 'csv': 'csv', 'tsv': 'csv', 'json': 'json'}[ext]

def group_key(name, h, paths):
    """Files with identical content are one dataset. CSVs also count as identical
    when they differ only by a byte-order mark, Windows line endings (Excel adds both)
    or a newline at the end of the file."""
    if kind(name) != 'csv':
        return h
    raw = open(paths[0], 'rb').read()
    raw = raw.removeprefix(b'\xef\xbb\xbf').replace(b'\r\n', b'\n').rstrip(b'\n') + b'\n'
    return 'csv:' + hashlib.sha1(raw).hexdigest()

# Merge entries with identical content under one dataset (aliases).
groups = {}
SKIP_BROKEN = {'athlete_events.db'}  # truncated file in the lecture repo; unused
for key, e in inv.items():
    name, h = key.split('|')
    if name in SKIP_BROKEN:
        continue
    d = groups.setdefault(group_key(name, h, e['paths']),
                          {'names': [], 'paths': [], 'uses': set(), 'hashes': {}})
    if name not in d['names']:
        d['names'].append(name)
    d['paths'] += e['paths']
    for p in e['paths']:
        d['hashes'][p] = h
    d['uses'] |= {tuple(u) for u in e['uses']}

# When the copies differ (BOM / line endings), publish the lecture notebook's copy
# and keep its hash in the dataset's id.
by_hash = {}
for d in groups.values():
    d['paths'].sort(key=lambda p: 'dma-lecture-content' not in p)
    by_hash[d['hashes'][d['paths'][0]]] = d

def describe_sqlite(path):
    con = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
    out = []
    for (t, sql) in con.execute("select name, sql from sqlite_master where type in ('table','view') and name not like 'sqlite_%' order by type, name"):
        broken = None
        try:
            cols = [{'name': r[1], 'type': r[2] or ''} for r in con.execute(f'pragma table_info("{t}")')]
            n = con.execute(f'select count(*) from "{t}"').fetchone()[0]
        except sqlite3.Error as ex:
            cols, n, broken = [], None, str(ex)
            print('  broken', path.rsplit('/', 1)[-1], t, ex)
        is_view = con.execute("select type from sqlite_master where name=?", (t,)).fetchone()[0] == 'view'
        out.append({'name': t, 'view': is_view, 'rows': n, 'columns': cols, **({'broken': broken} if broken else {})})
    con.close()
    return {'tables': out}

def describe_csv(path):
    with open(path, newline='', encoding='utf-8-sig', errors='replace') as f:
        rows = list(csv.reader(f))
    header = rows[0] if rows else []
    return {'columns': [{'name': c or '(index)'} for c in header], 'rows': max(len(rows) - 1, 0)}

def describe_json(path):
    data = json.load(open(path, encoding='utf-8'))
    if isinstance(data, list):
        keys = []
        for r in data[:200]:
            if isinstance(r, dict):
                keys += [k for k in r if k not in keys]
        return {'shape': 'list', 'rows': len(data), 'columns': [{'name': k} for k in keys]}
    return {'shape': 'object', 'keys': list(data)[:50]}

def use_label(u):
    t, n = u
    if t == 'lecture':
        return {'kind': 'lecture', 'n': n, 'label': f'Lecture {n}', 'title': LECTURES.get(n, '')}
    return {'kind': 'assignment', 'n': n, 'label': f'Assignment {n}', 'title': ''}

# Two different files share the names movies2.db and students_and_courses.csv: label them.
name_count = {}
for d in by_hash.values():
    for n in d['names']:
        name_count[n] = name_count.get(n, 0) + 1

if os.path.isdir(SITE):
    shutil.rmtree(SITE)
os.makedirs(os.path.join(SITE, 'data'))
shutil.copy(os.path.join(HERE, 'sql-wasm.wasm'), os.path.join(SITE, 'sql-wasm.wasm'))

# Notes shown under a dataset's name, by its displayed name.
NOTES = {
    'movies.db': "Starts empty: Lecture 22's INSERT examples fill in the movie table. "
                 "The filled-in version is movies2.db.",
    'movies2.db': "The movie table after Lecture 22's INSERT examples (17 movies).",
    'movies2_with_genre.db': "Not the same as movies2.db: this one has a separate genre table. "
                             "Two Lecture 22 PrairieLearn exercises use it under the name movies2.db.",
}

def lecture_names(d):
    return {os.path.basename(p) for p in d['paths'] if 'dma-lecture-content' in p}

catalog, total_gz = [], 0
for h, d in sorted(by_hash.items(), key=lambda kv: kv[1]['names'][0].lower()):
    # Title each dataset with a name no other dataset uses if it has one (so two
    # different files never show the same title), then the lecture notebook's
    # filename; its other names are listed as aliases.
    lec = lecture_names(d)
    names = sorted(d['names'], key=lambda n: (name_count[n] > 1, n not in lec,
                                               n != os.path.basename(d['paths'][0]), n))
    primary = names[0]
    src = d['paths'][0]
    k = kind(primary)
    note = NOTES.get(primary, '')
    if not note and name_count[primary] > 1:
        note = ('Lecture notebook version' if 'dma-lecture-content' in src else 'PrairieLearn exercise version')
    slug = re.sub(r'[^A-Za-z0-9]+', '-', primary.rsplit('.', 1)[0]).strip('-').lower() + '-' + h[:6]
    gzname = f'data/{slug}.{primary.rsplit(".", 1)[1].lower()}.gz.b64.txt'
    raw = open(src, 'rb').read()
    gz = gzip.compress(raw, 9)
    open(os.path.join(SITE, gzname), 'w').write(base64.b64encode(gz).decode())
    total_gz += len(gz)
    info = {'sqlite': describe_sqlite, 'csv': describe_csv, 'json': describe_json}[k](src)
    uses = sorted(d['uses'], key=lambda u: (u[0] != 'lecture', u[1]))
    catalog.append({
        'id': slug, 'name': primary, 'aliases': names[1:], 'note': note, 'kind': k,
        'bytes': len(raw), 'gzBytes': len(gz), 'file': gzname,
        'uses': [use_label(u) for u in uses], 'info': info,
    })

# Inline the catalog into the page (a separate script file doesn't load in the artifact viewer).
cat_js = 'window.CATALOG = ' + json.dumps(catalog, separators=(',', ':')).replace('</', '<\\/') + ';'
page = open(os.path.join(HERE, 'index.html')).read()
assert '<script src="catalog.js"></script>' in page
page = page.replace('<script src="catalog.js"></script>', '<script>' + cat_js + '</script>')
# GitHub Pages serves the file as-is, so give it a full HTML document.
page = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        + page.replace('<meta charset="utf-8">\n', '', 1) + '\n</html>\n')
open(os.path.join(SITE, 'index.html'), 'w').write(page)

print(len(catalog), 'datasets;', round(total_gz / 1e6, 1), 'MB compressed')
for c in catalog:
    print(f"{c['kind']:6} {c['name']:38} {c['note']:30} {c['bytes']//1024:>6} KB -> {c['gzBytes']//1024:>5} KB  {[u['label'] for u in c['uses']]}")
