#!/usr/bin/env python3
"""Export a reviewable, non-restorable snapshot of local Hermes instructions and workflow."""
from pathlib import Path
import json, re, hashlib, shutil, subprocess, os
import yaml

ROOT=Path('/home/thomas/.hermes')
OUT=Path(__file__).resolve().parent/'setup'
TEXT={'.md','.py','.sh','.yaml','.yml','.json','.toml','.js','.ts','.mjs','.cjs','.txt','.css','.html','.xml','.gitignore','.dockerignore'}
IGNORE={'.git','.worktrees','node_modules','venv','.venv','__pycache__','.hub','.locks','.curator_backups','backups','output','logs','sessions','cache','.cache','state','state-snapshots','attachments','dist','build','.test-venvs','test-results','tmp','temp'}
SKIP_NAMES={'auth.json','.env','hosts.yml','jobs.lock','.usage.json','.curator_state','.curator_ledger.jsonl','.bundled_manifest','.install-metadata.json','.hermes-package.json','package-lock.json'}
SECRETS=[]
for envfile in [ROOT/'.env',*(p/'.env' for p in (ROOT/'profiles').iterdir() if p.is_dir())]:
 if envfile.exists():
  for line in envfile.read_text(errors='ignore').splitlines():
   if '=' in line and not line.lstrip().startswith('#'):
    key,val=line.split('=',1)
    val=val.strip().strip('"\'')
    if re.search(r'(?i)(?:TOKEN|SECRET|PASSWORD|API_KEY|PRIVATE_KEY|CLIENT_ID|PUBLIC_KEY|ALLOWED_USERS|CHANNEL_THREAD_ID|HOME_CHANNEL$)',key) and len(val)>8 and not val.startswith(('/', '${')): SECRETS.append(val)
# Credential material is never exported verbatim, even if embedded in scripts or docs.
PATTERNS=[
 re.compile(r'(?i)(?:gh[opusr]_|github_pat_)[A-Za-z0-9_]{16,}'),
 re.compile(r'(?i)(?:sk-[A-Za-z0-9_-]{20,}|sk_(?:live|test)_[A-Za-z0-9]{15,})'),
 re.compile(r'(?<![A-Za-z0-9_-])eyJ[A-Za-z0-9_-]{20,}\.eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{15,}'),
 re.compile(r'(?<![A-Za-z0-9])AKIA[0-9A-Z]{16}(?![A-Za-z0-9])'),
 re.compile(r'(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{25,}(?![A-Za-z0-9_-])'),
 re.compile(r'(?i)(?:bearer\s+)[A-Za-z0-9_.~+/-]{18,}'),
 re.compile(r'(?i)(?:https?://)[^\s:@/]+:[^\s@/]+@[^\s/]+'),
 re.compile(r'(?i)-----BEGIN (?:OPENSSH|RSA|EC|PRIVATE) KEY-----[\s\S]*?-----END [^-]+-----'),
 re.compile(r'(?i)(?:token|secret|password|api[_-]?key|client[_-]?secret)\s*[=:]\s*[\"\']?(?!\$|\{|\[|<|None|none|null|true|false)[A-Za-z0-9_.+/=-]{18,}'),
]
# IDs are routing targets and private identifiers, not useful in a shared architecture export.
DISCORD_ID=re.compile(r'(?<!\d)\d{17,20}(?!\d)')
ABS_HOME=re.compile(re.escape(str(Path.home())))
count=0; redactions=0; skipped=[]; exported=set()

def safe_text(s):
 global redactions
 for secret in SECRETS:
  if secret in s: s=s.replace(secret,'<REDACTED_SECRET>');redactions+=1
 for p in PATTERNS:
  s,n=p.subn('<REDACTED_SECRET>',s);redactions+=n
 s,n=DISCORD_ID.subn('<REDACTED_ID>',s);redactions+=n
 s=ABS_HOME.sub('~',s)
 return s

def safe_struct(v,key=''):
 if isinstance(v,dict): return {k:safe_struct(x,k) for k,x in v.items()}
 if isinstance(v,list): return [safe_struct(x,key) for x in v]
 if isinstance(v,int) and not isinstance(v,bool) and re.fullmatch(r'\d{17,20}',str(v)):return '<REDACTED_ID>'
 if isinstance(v,str):
  if re.search(r'(?i)(?:password|secret|token|api.key|credential|private.key|decision_owner_id|decision_dm_channel_id|basic_auth)',str(key)):
   return '<REDACTED_SECRET>' if v else v
  return safe_text(v)
 return v

def export(source,dest,structured=False):
 global count
 if source.is_symlink() or not source.is_file() or source.stat().st_size>1_000_000 or source.suffix.lower() not in TEXT and source.name not in ('SOUL.md','AGENTS.md','CLAUDE.md','HERMES.md','.hermes.md'):
  skipped.append(str(source.relative_to(ROOT)) if source.is_relative_to(ROOT) else str(source));return
 try:
  raw=source.read_text('utf-8')
 except UnicodeError:
  skipped.append(str(source));return
 if structured:
  data=(yaml.safe_load(raw) if source.suffix in ('.yaml','.yml') else json.loads(raw))
  clean=safe_struct(data)
  text=(yaml.safe_dump(clean,sort_keys=False,allow_unicode=True) if source.suffix in ('.yaml','.yml') else json.dumps(clean,indent=2,ensure_ascii=False))+'\n'
 else: text=safe_text(raw)
 dest.parent.mkdir(parents=True,exist_ok=True)
 dest.write_text(text)
 count+=1;exported.add(str(dest.relative_to(OUT.parent)))

def tree(src,dst):
 if not src.exists():return
 for path in sorted(src.rglob('*')):
  rel=path.relative_to(src)
  if any(part in IGNORE or part.startswith('.fire-') for part in rel.parts):continue
  if path.name in SKIP_NAMES or path.name.startswith('.') and path.suffix in ('.db','.lock'):continue
  if path.is_file() and not path.is_symlink():export(path,dst/rel,structured=path.suffix in ('.yaml','.yml','.json'))

OUT.mkdir(exist_ok=True)
for name in ['SOUL.md','config.yaml']:
 export(ROOT/name,OUT/name,structured=name.endswith('.yaml'))
for name in ['team','scripts','skills','plugins','desktop-plugins','hooks']:
 tree(ROOT/name,OUT/name)
# Include only authored profile configuration and skill/plugin content, not runtime state.
for profile in sorted((ROOT/'profiles').iterdir()):
 if not profile.is_dir():continue
 target=OUT/'profiles'/profile.name
 for name in ['SOUL.md','config.yaml']:
  if (profile/name).exists():export(profile/name,target/name,structured=name.endswith('.yaml'))
 for name in ['skills','plugins','hooks']:
  tree(profile/name,target/name)
 for job in [profile/'cron/jobs.json']:
  if job.exists():export(job,target/'cron/jobs.json',structured=True)
for name in ['jobs.json','work-checkin.yaml','work-hours-checkin.json','workhours-checkin.sh','work-hours-checkin.sh']:
 p=ROOT/'cron'/name
 if p.exists():export(p,OUT/'cron'/name,structured=p.suffix in ('.json','.yaml','.yml'))
# A narrowly selected deployment snapshot. Do not touch its dirty working tree or git history.
rail=Path('/home/thomas/Hermes Workspace/projects/hermes-agent-railway')
for path in [rail/'README.md',rail/'OPERATIONS.md',rail/'RAILWAY.md',rail/'Dockerfile',rail/'railway.toml',rail/'entrypoint.sh',rail/'team/TEAM.md',rail/'team/task-template.md']:
 if path.exists():export(path,OUT/'deployment'/path.relative_to(rail))
for name in ['scripts','patches','deploy','.github']:
 src=rail/name
 if src.exists():
  for p in src.rglob('*'):
   if p.is_file() and not p.is_symlink() and not any(x in IGNORE for x in p.relative_to(src).parts):export(p,OUT/'deployment'/p.relative_to(rail),structured=p.suffix in ('.yaml','.yml','.json'))
# Mirror core's agent instruction files, without copying upstream's large public source tree.
core=Path('/home/thomas/Hermes Workspace/projects/hermes-agent-core')
for base,dirs,files in os.walk(core):
 dirs[:]=[d for d in dirs if d not in IGNORE and not d.startswith('.')]
 if 'AGENTS.md' in files:
  path=Path(base)/'AGENTS.md';export(path,OUT/'core-instructions'/path.relative_to(core))
for name in ['SOUL.md','COMPAT_MANIFEST.md']:
 if (core/name).exists(): export(core/name,OUT/'core-instructions'/name)
# Residual high-confidence checks; never print a detected value.
issues=[]
for f in OUT.rglob('*'):
 if not f.is_file():continue
 data=f.read_text()
 if any(s in data for s in SECRETS):issues.append(str(f.relative_to(OUT)))
 if any(p.search(data) for p in PATTERNS):issues.append(str(f.relative_to(OUT)))
 if re.search(r'(?<!\d)\d{17,20}(?!\d)',data):issues.append(str(f.relative_to(OUT)))
if issues:raise SystemExit('Residual credential patterns in: '+', '.join(sorted(set(issues))))
print(json.dumps({'files':count,'redactions':redactions,'skipped_nontext_large_or_runtime':len(skipped),'export_root':str(OUT),'total_bytes':sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())}))
