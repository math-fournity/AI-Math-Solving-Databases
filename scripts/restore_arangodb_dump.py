#!/usr/bin/env python3
"""Restore ArangoDB dumps (JSONL + manifest.json) into a running ArangoDB server.

Usage:
    python restore_arangodb_dump.py --host http://localhost:8529 \
        --user root --password <pass> [--databases xishujuzhen_math_glm52,p27sim] \
        [--suffix _restored] [--dry-run]

Reads manifest.json (collection -> doc count, files, sha256) and re-inserts every
document with its original _key. _rev is stripped (ArangoDB regenerates it).
--suffix restores into renamed databases (e.g. xishujuzhen_math_glm52_restored)
so a restore drill never touches existing databases.
"""
import argparse, gzip, hashlib, json, os, sys, time

def open_dump(path):
    return gzip.open(path, 'rt', encoding='utf-8') if path.endswith('.gz') else open(path, 'r', encoding='utf-8')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='http://localhost:8529')
    ap.add_argument('--user', default='root')
    ap.add_argument('--password', required=True)
    ap.add_argument('--databases', default=None, help='comma list; default = all in manifest')
    ap.add_argument('--collections', default=None, help='optional comma list to restore only these collections')
    ap.add_argument('--suffix', default='', help='append to database names (drill/side-by-side restore)')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    dumps = os.path.join(os.path.dirname(here), 'dumps')
    manifest = json.load(open(os.path.join(dumps, 'manifest.json'), encoding='utf-8'))

    from arango import ArangoClient
    client = ArangoClient(hosts=args.host)
    sysdb = client.db('_system', username=args.user, password=args.password)

    targets = args.databases.split(',') if args.databases else [k for k in manifest if isinstance(manifest[k], dict)]
    for dbn in targets:
        cols = manifest.get(dbn, {})
        if not cols:
            print(f"skip {dbn}: no manifest entries"); continue
        target_db = dbn + args.suffix
        print(f"== restoring {dbn} -> {target_db} ({len(cols)} collections) ==")
        if not args.dry_run:
            if not sysdb.has_database(target_db):
                sysdb.create_database(target_db)
        db = client.db(target_db, username=args.user, password=args.password)
        only = set(args.collections.split(',')) if args.collections else None
        for cn, meta in cols.items():
            if only is not None and cn not in only:
                continue
            if 'error' in meta:
                print(f"  {cn}: SKIP (source export had error)"); continue
            files = meta.get('files') or [meta]
            batch, total = [], 0
            t0 = time.time()
            if not args.dry_run and not db.has_collection(cn):
                db.create_collection(cn)
            col = db.collection(cn)
            for fmeta in files:
                fref = fmeta['file'] if isinstance(fmeta, dict) else fmeta
                path = os.path.join(dumps, fref)
                if not os.path.exists(path):
                    print(f"  {cn}: MISSING FILE {fref}, aborting collection"); break
                expect = fmeta.get('sha256') if isinstance(fmeta, dict) else meta.get('sha256')
                if expect and hashlib.sha256(open(path, 'rb').read()).hexdigest() != expect:
                    print(f"  {cn}: CHECKSUM MISMATCH in {fref}, aborting collection"); break
                with open_dump(path) as f:
                    for line in f:
                        line = line.strip()
                        if not line: continue
                        doc = json.loads(line)
                        doc.pop('_rev', None)
                        batch.append(doc)
                        if len(batch) >= 1000:
                            if not args.dry_run:
                                col.import_bulk(batch, on_duplicate='replace', sync=False)
                            total += len(batch); batch = []
                            if total % 100000 == 0:
                                print(f"  {cn}: {total} docs ({time.time()-t0:.0f}s)", flush=True)
            if batch:
                if not args.dry_run:
                    col.import_bulk(batch, on_duplicate='replace', sync=False)
                total += len(batch); batch = []
            ok = '' if args.dry_run else f" -> {col.count()} in db"
            print(f"  {cn}: {total} docs{ok} ({time.time()-t0:.0f}s)", flush=True)
    print("DONE")

if __name__ == '__main__':
    main()
