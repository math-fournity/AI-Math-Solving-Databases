#!/usr/bin/env python3
"""remap_paths.py — 把已恢复数据库中的中性化历史路径重映射到你本机的真实布局。

背景：数据导出时已把原始机器的路径中性化为通用前缀（见 dumps/manifest.json 的
_substitutions）。恢复后，DB 文档里的 solver_dir / trajectory_dir / local_path 等
字段仍是中性路径——它们是"溯源记录"，系统运行时读 .env，不读这些字段。
但如果你希望历史记录里的路径指向你本机的真实目录（便于跳转/对账），运行本脚本。

用法：
    python remap_paths.py --host http://localhost:8529 --user root --password <pass> \
        [--databases xishujuzhen_math_glm52] \
        [--map /Volumes/data=/mnt/bigdisk] [--map /Users/user=/home/alice] [--dry-run]

--map 可多次出现：左边是中性前缀，右边是你的实际前缀。默认映射：
    /Volumes/data/math-agent-glm5.2-tmux-agents-dir     -> $SOLVER_BASE
    /Volumes/data/math-agent-glm5.2-tmux-agents-trajectory -> $TRAJECTORY_BASE
    /Users/user/glm5.2-math-worktree                     -> $KNOWLEDGE_BASE
（默认值取自环境变量 SOLVER_BASE / TRAJECTORY_BASE / KNOWLEDGE_BASE）
"""
import argparse, json, os, sys

DEFAULT_MAPS = [
    ('/Volumes/data/math-agent-glm5.2-tmux-agents-dir', 'SOLVER_BASE'),
    ('/Volumes/data/math-agent-glm5.2-tmux-agents-trajectory', 'TRAJECTORY_BASE'),
    ('/Users/user/glm5.2-math-worktree', 'KNOWLEDGE_BASE'),
]

PATH_FIELDS = ('solver_dir', 'trajectory_dir', 'local_path', 'work_dir', 'export_path',
               'prompt_path', 'proof_path', 'problem_file', 'dir', 'path')

def remap_doc(doc, maps):
    changed = []
    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, str) and any(v.startswith(a) or a in v for a, _ in maps):
                    nv = v
                    for a, b in maps:
                        nv = nv.replace(a, b)
                    if nv != v:
                        o[k] = nv; changed.append(k)
                elif isinstance(v, (dict, list)):
                    walk(v)
        elif isinstance(o, list):
            for x in o: walk(x)
    walk(doc)
    return changed

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='http://localhost:8529')
    ap.add_argument('--user', default='root')
    ap.add_argument('--password', required=True)
    ap.add_argument('--databases', default='xishujuzhen_math_glm52')
    ap.add_argument('--map', action='append', default=[], metavar='NEUTRAL=YOURS')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    maps = []
    for m in args.map:
        a, _, b = m.partition('=')
        maps.append((a, b))
    if not maps:
        for neutral, envvar in DEFAULT_MAPS:
            val = os.environ.get(envvar)
            if val: maps.append((neutral, val))
    if not maps:
        sys.exit('没有可用映射：请用 --map 或导出 SOLVER_BASE/TRAJECTORY_BASE/KNOWLEDGE_BASE')
    print('映射规则：')
    for a, b in maps: print(f'  {a}  ->  {b}')

    from arango import ArangoClient
    client = ArangoClient(hosts=args.host)
    for dbn in args.databases.split(','):
        db = client.db(dbn, username=args.user, password=args.password)
        print(f'== {dbn} ==')
        for c in db.collections():
            cn = c['name']
            if cn.startswith('_'): continue
            col = db.collection(cn)
            updated = 0
            cursor = db.aql.execute('FOR d IN @@c RETURN d', bind_vars={'@c': cn}, batch_size=2000, stream=True)
            for doc in cursor:
                if not isinstance(doc, dict): continue
                if not any(isinstance(v, str) and any(a in v for a, _ in maps) for v in doc.values()): continue
                doc2 = json.loads(json.dumps(doc, ensure_ascii=False))
                remap_doc(doc2, maps)
                if doc2 != doc and not args.dry_run:
                    col.update({'_key': doc['_key'], **{k: doc2[k] for k in doc2 if doc2[k] != doc.get(k)}})
                if doc2 != doc: updated += 1
            if updated: print(f'  {cn}: {"将更新" if args.dry_run else "已更新"} {updated} docs')
    print('DONE' + ('（dry-run，未写库）' if args.dry_run else ''))

if __name__ == '__main__':
    main()
