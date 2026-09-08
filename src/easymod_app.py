import json, os, platform, re, shutil, subprocess, sys, threading, urllib.request, urllib.error, zipfile, tempfile, hashlib, tarfile
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

APP='EasyMod'; VERSION='1.1.0'
HOME=Path.home()/'.easymod'; CACHE=HOME/'cache'; WORK=HOME/'workspaces'; JDKS=HOME/'jdks'
for p in (HOME,CACHE,WORK,JDKS): p.mkdir(parents=True,exist_ok=True)

# --------------------------- block language ---------------------------
BLOCKS={
'event_mod_load':('Events','When mod loads'),'event_player_join':('Events','When player joins'),'event_player_leave':('Events','When player leaves'),'event_right_click':('Events','When player right clicks'),'event_left_click':('Events','When player left clicks'),'event_block_break':('Events','When block breaks'),'event_block_place':('Events','When block is placed'),'event_entity_death':('Events','When entity dies'),'event_tick':('Events','Every tick'),'event_server_tick':('Events','Server tick'),
'if':('Control','If'),'else':('Control','Else'),'repeat':('Control','Repeat'),'while':('Control','While'),'for_each':('Control','For each'),'wait':('Control','Wait ticks'),'stop':('Control','Stop'),
'var_set':('Variables','Set variable'),'var_change':('Variables','Change variable'),'var_get':('Variables','Get variable'),'player_var_set':('Variables','Set player variable'),'world_var_set':('Variables','Set world variable'),
'number':('Values','Number'),'text':('Values','Text'),'boolean':('Values','Boolean'),'null':('Values','Null'),'random':('Math','Random'),'add':('Math','Add'),'sub':('Math','Subtract'),'mul':('Math','Multiply'),'div':('Math','Divide'),'mod':('Math','Modulo'),'equals':('Logic','Equals'),'greater':('Logic','Greater than'),'less':('Logic','Less than'),'and':('Logic','And'),'or':('Logic','Or'),'not':('Logic','Not'),
'player_get':('Player','Get player'),'player_health':('Player','Get health'),'player_set_health':('Player','Set health'),'player_heal':('Player','Heal'),'player_damage':('Player','Damage'),'give_item':('Player','Give item'),'remove_item':('Player','Remove item'),'send_message':('Player','Send message'),'send_actionbar':('Player','Send action bar'),'teleport':('Player','Teleport'),'add_effect':('Player','Add effect'),'remove_effect':('Player','Remove effect'),'set_food':('Player','Set food'),'set_xp':('Player','Set XP'),'kick':('Player','Kick'),
'get_block':('World','Get block'),'set_block':('World','Set block'),'break_block':('World','Break block'),'spawn_entity':('World','Spawn entity'),'kill_entity':('World','Kill entity'),'play_sound':('World','Play sound'),'particle':('World','Spawn particle'),'set_time':('World','Set time'),'weather':('World','Set weather'),'explosion':('World','Explosion'),
'custom_java':('Advanced','Custom Java'),'comment':('Advanced','Comment')}

FIELD_DEFAULTS={
'give_item':{'item':'minecraft:diamond','amount':'1'},'remove_item':{'item':'minecraft:diamond','amount':'1'},'send_message':{'message':'Hello world!'},'send_actionbar':{'message':'Hello!'},'player_set_health':{'health':'20'},'player_heal':{'amount':'4'},'player_damage':{'amount':'4'},'teleport':{'x':'0','y':'64','z':'0'},'add_effect':{'effect':'minecraft:speed','duration':'200','amplifier':'0'},'remove_effect':{'effect':'minecraft:speed'},'set_food':{'food':'20'},'set_xp':{'xp':'0'},'kick':{'message':'Kicked by a mod'},'get_block':{'x':'0','y':'64','z':'0'},'set_block':{'x':'0','y':'64','z':'0','block':'minecraft:stone'},'break_block':{'x':'0','y':'64','z':'0'},'spawn_entity':{'entity':'minecraft:pig','x':'0','y':'64','z':'0'},'kill_entity':{},'play_sound':{'sound':'minecraft:block.note_block.pling','volume':'1','pitch':'1'},'particle':{'particle':'minecraft:happy_villager','x':'0','y':'64','z':'0','count':'10'},'set_time':{'time':'1000'},'weather':{'weather':'clear'},'explosion':{'x':'0','y':'64','z':'0','power':'2'},'number':{'value':'0'},'text':{'value':'text'},'boolean':{'value':'true'},'random':{'min':'0','max':'1'},'add':{'a':'0','b':'0'},'sub':{'a':'0','b':'0'},'mul':{'a':'0','b':'0'},'div':{'a':'1','b':'1'},'mod':{'a':'0','b':'1'},'equals':{'a':'0','b':'0'},'greater':{'a':'0','b':'0'},'less':{'a':'0','b':'0'},'var_set':{'name':'value','value':'0'},'var_change':{'name':'value','amount':'1'},'var_get':{'name':'value'},'player_var_set':{'name':'value','value':'0'},'world_var_set':{'name':'value','value':'0'},'repeat':{'times':'10'},'while':{'condition':'true'},'for_each':{'variable':'item','collection':'items'},'wait':{'ticks':'20'},'custom_java':{'code':'// custom Java'},'comment':{'text':'Comment'} }

# --------------------------- project / source map ---------------------------
def uid():
 import uuid; return uuid.uuid4().hex

def slug(s):
 s=re.sub('[^a-zA-Z0-9_]','_',s).lower(); s=re.sub('_+','_',s).strip('_'); return s or 'mymod'

def new_project():
 a=uid(); b=uid()
 return {'format':1,'name':'My Mod','mod_id':'mymod','version':'1.0.0','minecraft':'26.2','loader':'fabric','language':'java','blocks':[
 {'id':a,'type':'event_player_join','x':80,'y':80,'fields':{},'next':b}, {'id':b,'type':'send_message','x':350,'y':115,'fields':dict(FIELD_DEFAULTS['send_message'])} ],'assets':[],'procedures':[],'items':[],'blocks_def':[],'entities':[],'guis':[],'recipes':[]}

class Project:
 def __init__(self,data=None,path=None): self.data=data or new_project(); self.path=Path(path) if path else None; self.dirty=False
 def save(self,path=None):
  if path:self.path=Path(path)
  if not self.path: raise ValueError('No project file')
  self.path.parent.mkdir(parents=True,exist_ok=True); self.path.write_text(json.dumps(self.data,indent=2),encoding='utf8'); self.dirty=False
 @classmethod
 def load(cls,path): return cls(json.loads(Path(path).read_text(encoding='utf8')),path)

class SourceMap:
 def __init__(self): self.entries={}
 def add(self,file,line,bid): self.entries[f'{file}:{line}']=bid
 def save(self,p): Path(p).write_text(json.dumps(self.entries,indent=2),encoding='utf8')
 @classmethod
 def load(cls,p):
  x=cls(); x.entries=json.loads(Path(p).read_text(encoding='utf8')); return x
 def lookup(self,file,line):
  file=Path(file).name; exact=self.entries.get(f'{file}:{line}')
  if exact:return exact
  best=None
  for k,v in self.entries.items():
   f,l=k.rsplit(':',1)
   if Path(f).name==file:
    d=abs(int(l)-line)
    if best is None or d<best[0]:best=(d,v)
  return best[1] if best else None

# --------------------------- online metadata ---------------------------
def get_json(url,timeout=12):
 req=urllib.request.Request(url,headers={'User-Agent':'EasyMod/1.0'})
 with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode('utf8'))

def fetch_versions():
 try:
  d=get_json('https://piston-meta.mojang.com/mc/game/version_manifest_v2.json')
  return [v['id'] for v in d['versions'] if v['type']=='release']
 except Exception:return []

def version_tuple(v):
    m=re.match(r'^(\d+)\.(\d+)(?:\.(\d+))?',v)
    return tuple(int(x or 0) for x in m.groups()) if m else (0,0,0)

def supports_fabric(mc): return version_tuple(mc) >= (1,14,0)
def supports_neoforge(mc): return version_tuple(mc) >= (1,20,2)
def java_major_for(mc):
    a,b,c=version_tuple(mc)
    if a>=26:return 25
    if a==1 and b>=20 and c>=5:return 21
    if a==1 and b>=20:return 17
    if a==1 and b>=18:return 17
    if a==1 and b>=17:return 16
    if a==1 and b>=13:return 8
    return 8

def forge_promotions():
    return get_json('https://files.minecraftforge.net/net/minecraftforge/forge/promotions_slim.json')

def forge_version_for(mc):
    if mc=='1.7.10': return '10.13.4.1614'
    d=forge_promotions()
    return d.get('promos',{}).get(mc+'-recommended') or d.get('promos',{}).get(mc+'-latest')

def download_file(url,dest,progress=None):
    dest=Path(dest); dest.parent.mkdir(parents=True,exist_ok=True)
    req=urllib.request.Request(url,headers={'User-Agent':'EasyMod/1.1'})
    with urllib.request.urlopen(req,timeout=60) as r, open(dest,'wb') as f:
        total=int(r.headers.get('Content-Length') or 0); done=0
        while True:
            b=r.read(1024*256)
            if not b: break
            f.write(b); done+=len(b)
            if progress and total: progress(done,total)
    return dest

class ToolchainManager:
    def __init__(self,log=None): self.log=log or (lambda x: None)
    def gradle_version(self,mc,loader):
        # Known current toolchains; legacy projects use their own old Gradle plugin.
        if loader=='fabric' and mc.startswith('26.'): return '9.5.1'
        if version_tuple(mc) >= (1,21,0): return '8.14.3'
        if version_tuple(mc) >= (1,20,0): return '8.5'
        if version_tuple(mc) >= (1,19,0): return '7.6'
        if version_tuple(mc) >= (1,18,0): return '7.4.2'
        return '7.0'
    def ensure_gradle(self,version):
        base=HOME/'gradle'/version; exe=base/('bin/gradle.bat' if os.name=='nt' else 'bin/gradle')
        if exe.exists(): return exe
        self.log(f'Downloading Gradle {version}…')
        z=CACHE/f'gradle-{version}-bin.zip'
        download_file(f'https://services.gradle.org/distributions/gradle-{version}-bin.zip',z)
        with zipfile.ZipFile(z) as zz: zz.extractall(HOME/'gradle')
        if not exe.exists(): raise RuntimeError(f'Gradle {version} installation failed')
        if os.name!='nt': exe.chmod(exe.stat().st_mode|0o111)
        return exe
    def ensure_java(self,major):
        tag=str(major); root=JDKS/tag
        candidates=list(root.glob('*/bin/java*')) if root.exists() else []
        if candidates: return candidates[0] if os.name!='nt' or candidates[0].name.endswith('.exe') else candidates[0]
        osname='windows' if os.name=='nt' else ('mac' if sys.platform=='darwin' else 'linux')
        arch='x64' if platform.machine().lower() in ('x86_64','amd64') else 'aarch64'
        url=f'https://api.adoptium.net/v3/assets/latest/{major}/hotspot?architecture={arch}&image_type=jdk&os={osname}&vendor=eclipse'
        data=get_json(url)
        if not data: raise RuntimeError(f'No Eclipse Temurin JDK {major} found for {osname}/{arch}')
        pkg=data[0]['binary']['package']; u=pkg['link']; suffix='.zip' if os.name=='nt' else '.tar.gz'; archive=CACHE/f'temurin-{major}-{osname}-{arch}{suffix}'
        self.log(f'Downloading Java {major} (Temurin)…'); download_file(u,archive)
        root.mkdir(parents=True,exist_ok=True)
        if suffix=='.zip':
            with zipfile.ZipFile(archive) as z: z.extractall(root)
        else:
            with tarfile.open(archive,'r:gz') as t: t.extractall(root)
        candidates=list(root.glob('*/bin/java*'))
        if not candidates: raise RuntimeError(f'JDK {major} extraction failed')
        return candidates[0]
    def environment(self,mc,loader):
        env=os.environ.copy(); major=java_major_for(mc)
        try:
            java=self.ensure_java(major); jhome=java.parent.parent
            env['JAVA_HOME']=str(jhome); env['PATH']=str(java.parent)+os.pathsep+env.get('PATH','')
        except Exception as e:
            self.log(f'Java bootstrap skipped: {e}')
        return env
    def command(self,mc,loader,workspace):
        return str(self.ensure_gradle(self.gradle_version(mc,loader)))

def fabric_loader_versions(mc):
 try:return get_json(f'https://meta.fabricmc.net/v2/versions/loader/{mc}')
 except Exception:return []

def fabric_api_versions(mc):
 try:
  # Maven metadata endpoint; parse XML without external packages.
  u='https://maven.fabricmc.net/net/fabricmc/fabric-api/fabric-api/maven-metadata.xml'
  txt=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'EasyMod/1.0'}),timeout=10).read().decode()
  vals=re.findall(r'<version>([^<]+)</version>',txt)
  return vals
 except Exception:return []

def forge_versions(mc):
 try:
  d=get_json(f'https://files.minecraftforge.net/net/minecraftforge/forge/index_{mc}.html')
  return d
 except Exception:return []

# --------------------------- version resolver ---------------------------
class Resolver:
 def resolve(self,mc,loader):
  if loader=='fabric':
   if not supports_fabric(mc): raise RuntimeError(f'Fabric is not available for {mc}; official Fabric releases start at 1.14.')
   loaders=fabric_loader_versions(mc)
   if not loaders: raise RuntimeError(f'Fabric Loader metadata unavailable for {mc}')
   latest=loaders[0]['loader']['version']
   api=''
   vals=fabric_api_versions(mc)
   for x in reversed(vals):
    if mc in x or x.endswith('+'+mc): api=x; break
   return {'loader':latest,'api':api,'java':java_major_for(mc),'loom':'1.17' if mc.startswith('26.') else '1.6-SNAPSHOT'}
  if loader=='neoforge':
   if not supports_neoforge(mc): raise RuntimeError(f'NeoForge is not available for {mc}; choose Forge or Fabric for this version.')
   xml=urllib.request.urlopen('https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml',timeout=15).read().decode()
   vals=re.findall(r'<version>([^<]+)</version>',xml)
   matches=[x for x in vals if x.startswith(mc+'.') or x.startswith(mc+'-')]
   if not matches: raise RuntimeError(f'No NeoForge version found for {mc}')
   return {'neoforge':matches[-1],'java':java_major_for(mc)}
  if loader=='forge':
   fv=forge_version_for(mc)
   if not fv: raise RuntimeError(f'No Forge build metadata found for {mc}')
   return {'forge':fv,'java':java_major_for(mc),'legacy':mc=='1.7.10'}
  raise RuntimeError('Unknown loader')

# --------------------------- IR + generators ---------------------------
class IR:
 def __init__(self,project):self.project=project; self.nodes=[]
 def build(self):
  self.nodes=[]
  for b in self.project.data['blocks']:
   self.nodes.append({'id':b['id'],'type':b['type'],'fields':b.get('fields',{}),'next':b.get('next')})
  return self

class JavaGenerator:
 def __init__(self,project):self.p=project;self.sm=SourceMap();self.lines=[]
 def emit(self,text,bid=None):
  self.lines.append(text)
  if bid:self.sm.add('EasyModGenerated.java',len(self.lines),bid)
 def generate(self,out):
  out=Path(out); src=out/'src/main/java/generated/EasyModGenerated.java';src.parent.mkdir(parents=True,exist_ok=True)
  self.emit('package generated;');self.emit('');self.emit('public final class EasyModGenerated {');self.emit('    public static void run(Object player, Object world) {')
  for n in IR(self.p).build().nodes:self.block(n)
  self.emit('    }');self.emit('}')
  src.write_text('\n'.join(self.lines)+'\n',encoding='utf8');self.sm.save(out/'easymod.sourcemap.json');return src
 def q(self,x):return '"'+str(x).replace('\\','\\\\').replace('"','\\"')+'"'
 def block(self,n):
  t=n['type'];f=n['fields'];bid=n['id'];self.emit(f'        // EasyMod block {bid}: {t}',bid)
  if t=='send_message':self.emit(f'        EasyModRuntime.sendMessage(player, {self.q(f.get("message",""))});',bid)
  elif t=='send_actionbar':self.emit(f'        EasyModRuntime.sendActionbar(player, {self.q(f.get("message",""))});',bid)
  elif t=='give_item':self.emit(f'        EasyModRuntime.giveItem(player, {self.q(f.get("item","minecraft:diamond"))}, {f.get("amount",1)});',bid)
  elif t=='remove_item':self.emit(f'        EasyModRuntime.removeItem(player, {self.q(f.get("item","minecraft:diamond"))}, {f.get("amount",1)});',bid)
  elif t=='player_set_health':self.emit(f'        EasyModRuntime.setHealth(player, {f.get("health",20)});',bid)
  elif t=='player_heal':self.emit(f'        EasyModRuntime.heal(player, {f.get("amount",4)});',bid)
  elif t=='player_damage':self.emit(f'        EasyModRuntime.damage(player, {f.get("amount",4)});',bid)
  elif t=='teleport':self.emit(f'        EasyModRuntime.teleport(player, {f.get("x",0)}, {f.get("y",64)}, {f.get("z",0)});',bid)
  elif t=='add_effect':self.emit(f'        EasyModRuntime.addEffect(player, {self.q(f.get("effect","minecraft:speed"))}, {f.get("duration",200)}, {f.get("amplifier",0)});',bid)
  elif t=='remove_effect':self.emit(f'        EasyModRuntime.removeEffect(player, {self.q(f.get("effect","minecraft:speed"))});',bid)
  elif t=='set_block':self.emit(f'        EasyModRuntime.setBlock(world, {f.get("x",0)}, {f.get("y",64)}, {f.get("z",0)}, {self.q(f.get("block","minecraft:stone"))});',bid)
  elif t=='break_block':self.emit(f'        EasyModRuntime.breakBlock(world, {f.get("x",0)}, {f.get("y",64)}, {f.get("z",0)});',bid)
  elif t=='spawn_entity':self.emit(f'        EasyModRuntime.spawnEntity(world, {self.q(f.get("entity","minecraft:pig"))}, {f.get("x",0)}, {f.get("y",64)}, {f.get("z",0)});',bid)
  elif t=='play_sound':self.emit(f'        EasyModRuntime.playSound(world, {self.q(f.get("sound","minecraft:block.note_block.pling"))}, {f.get("volume",1)}, {f.get("pitch",1)});',bid)
  elif t=='particle':self.emit(f'        EasyModRuntime.particle(world, {self.q(f.get("particle","minecraft:happy_villager"))}, {f.get("x",0)}, {f.get("y",64)}, {f.get("z",0)}, {f.get("count",10)});',bid)
  elif t=='set_time':self.emit(f'        EasyModRuntime.setTime(world, {f.get("time",1000)});',bid)
  elif t=='weather':self.emit(f'        EasyModRuntime.weather(world, {self.q(f.get("weather","clear"))});',bid)
  elif t=='explosion':self.emit(f'        EasyModRuntime.explosion(world, {f.get("x",0)}, {f.get("y",64)}, {f.get("z",0)}, {f.get("power",2)});',bid)
  elif t=='custom_java':
   for line in str(f.get('code','')).splitlines():self.emit('        '+line,bid)
  elif t=='comment':self.emit('        // '+str(f.get('text','')),bid)
  elif t=='if':self.emit('        if (/* '+str(f.get('condition','true'))+' */ true) {',bid);self.emit('        }',bid)
  elif t=='repeat':self.emit(f'        for (int i=0; i<{f.get("times",10)}; i++) {{',bid);self.emit('        }',bid)
  elif t=='while':self.emit('        while (true) {',bid);self.emit('        }',bid)
  elif t=='var_set':self.emit(f'        // variable {f.get("name","value")} = {f.get("value",0)}',bid)
  else:self.emit(f'        // TODO generator for {t}',bid)

class ProjectGenerator:
 def __init__(self,project,resolved):self.p=project;self.r=resolved
 def generate(self,w):
  w=Path(w);(w/'src/main/java/generated').mkdir(parents=True,exist_ok=True);(w/'src/main/resources').mkdir(parents=True,exist_ok=True)
  JavaGenerator(self.p).generate(w)
  mc=self.p.data['minecraft'];loader=self.p.data['loader'];mid=self.p.data['mod_id'];name=self.p.data['name']
  if loader=='fabric':self.fabric(w,mc,mid,name)
  elif loader=='neoforge':self.neoforge(w,mc,mid,name)
  elif loader=='forge':self.forge(w,mc,mid,name)
  self.write_runtime(w)
 def fabric(self,w,mc,mid,name):
  api=self.r.get('api',''); loader=self.r.get('loader',''); java=self.r.get('java',17)
  if not api: api='0.100.0+1.20.6' if mc=='1.20.6' else ''
  remap=not mc.startswith('26.')
  plugin='net.fabricmc.fabric-loom-remap' if remap else 'net.fabricmc.fabric-loom'
  loom=self.r.get('loom','1.17' if mc.startswith('26.') else '1.6-SNAPSHOT')
  (w/'settings.gradle').write_text("pluginManagement { repositories { maven { url='https://maven.fabricmc.net/' }; gradlePluginPortal() } }\nrootProject.name='%s'\n"%mid,encoding='utf8')
  (w/'gradle.properties').write_text(f'minecraft_version={mc}\nloader_version={loader}\nfabric_version={api}\nmod_version={self.p.data["version"]}\nmaven_group=com.easymod\narchives_base_name={mid}\n',encoding='utf8')
  mapping='mappings loom.officialMojangMappings();' if remap else ''
  api_dep=f'modImplementation "net.fabricmc.fabric-api:fabric-api:${{project.fabric_version}}"' if api else ''
  deps=f'dependencies {{ minecraft "com.mojang:minecraft:${{project.minecraft_version}}"; {mapping} modImplementation "net.fabricmc:fabric-loader:${{project.loader_version}}"; {api_dep} }}'
  build=f"""plugins {{ id 'java'; id '{plugin}' version '{loom}' }}
repositories {{ maven {{ url='https://maven.fabricmc.net/' }}; mavenCentral() }}
{deps}
java {{ toolchain {{ languageVersion = JavaLanguageVersion.of({java}) }} }}
"""
  (w/'build.gradle').write_text(build,encoding='utf8')
  depends={'fabricloader':'>=0.15.0','minecraft':mc}
  if api: depends['fabric-api']='*'
  (w/'src/main/resources/fabric.mod.json').write_text(json.dumps({'schemaVersion':1,'id':mid,'version':self.p.data['version'],'name':name,'environment':'*','entrypoints':{'main':['generated.EasyModEntrypoint']},'depends':depends},indent=2),encoding='utf8')
  (w/'src/main/java/generated/EasyModEntrypoint.java').write_text('package generated;\nimport net.fabricmc.api.ModInitializer;\npublic final class EasyModEntrypoint implements ModInitializer { @Override public void onInitialize() { } }\n',encoding='utf8')
 def neoforge(self,w,mc,mid,name):
  nv=self.r.get('neoforge','');
  if not nv: raise RuntimeError(f'NeoForge version missing for {mc}')
  url=f'https://maven.neoforged.net/releases/net/neoforged/neoforge/{nv}/neoforge-{nv}-mdk.zip'
  z=CACHE/f'neoforge-{nv}-mdk.zip'
  try:
   if not z.exists(): download_file(url,z,self._progress)
   with zipfile.ZipFile(z) as zz: zz.extractall(w)
  except Exception as e:
   raise RuntimeError(f'Could not download the official NeoForge MDK for {nv}: {e}')
  props=w/'gradle.properties'
  if props.exists():
   txt=props.read_text(encoding='utf8')
   txt += f'\n# EasyMod\neasymod_minecraft={mc}\neasymod_neoforge={nv}\n'
   props.write_text(txt,encoding='utf8')
  (w/'src/main/resources/META-INF').mkdir(parents=True,exist_ok=True)
  (w/'src/main/resources/META-INF/easymod.toml').write_text(f'# EasyMod generated for NeoForge {nv}\n',encoding='utf8')
 def forge(self,w,mc,mid,name):
  fv=self.r.get('forge','')
  if not fv: raise RuntimeError(f'Forge version missing for {mc}')
  # Use the official Forge MDK so every Forge release gets its own correct Gradle/plugin setup.
  url=f'https://maven.minecraftforge.net/net/minecraftforge/forge/{mc}-{fv}/forge-{mc}-{fv}-mdk.zip'
  z=CACHE/f'forge-{mc}-{fv}-mdk.zip'
  try:
   if not z.exists(): download_file(url,z,self._progress)
   with zipfile.ZipFile(z) as zz: zz.extractall(w)
  except Exception as e:
   raise RuntimeError(f'Could not download the official Forge MDK for {mc}-{fv}: {e}')
  # Remove sample sources that can collide with EasyMod output.
  for sample in ('src/main/java/com/example/examplemod','src/main/resources/META-INF/mods.toml'):
   q=w/sample
   if q.is_dir(): shutil.rmtree(q)
   elif q.exists(): q.unlink()
  props=w/'gradle.properties'
  if props.exists():
   txt=props.read_text(encoding='utf8')
   txt += f'\n# EasyMod\neasymod_minecraft={mc}\neasymod_forge={fv}\n'
   props.write_text(txt,encoding='utf8')
  (w/'src/main/resources/META-INF').mkdir(parents=True,exist_ok=True)
  (w/'src/main/resources/META-INF/easymod.toml').write_text(f'# EasyMod generated for Forge {mc}-{fv}\n',encoding='utf8')
 def _progress(self,done,total):
  pass
 def write_runtime(self,w):
  (w/'src/main/java/generated/EasyModRuntime.java').write_text('''package generated;\npublic final class EasyModRuntime {\n public static void sendMessage(Object p,String s){} public static void sendActionbar(Object p,String s){} public static void giveItem(Object p,String i,int n){} public static void removeItem(Object p,String i,int n){} public static void setHealth(Object p,int n){} public static void heal(Object p,int n){} public static void damage(Object p,int n){} public static void teleport(Object p,double x,double y,double z){} public static void addEffect(Object p,String e,int d,int a){} public static void removeEffect(Object p,String e){} public static void setBlock(Object w,int x,int y,int z,String b){} public static void breakBlock(Object w,int x,int y,int z){} public static void spawnEntity(Object w,String e,double x,double y,double z){} public static void playSound(Object w,String s,double v,double p){} public static void particle(Object w,String p,double x,double y,double z,int c){} public static void setTime(Object w,long t){} public static void weather(Object w,String s){} public static void explosion(Object w,double x,double y,double z,float p){}\n}\n''',encoding='utf8')

# --------------------------- compiler diagnostics ---------------------------
def diagnostics(text,smap):
 out=[]
 pats=[re.compile(r'(?P<file>[A-Za-z0-9_./\\-]+\.java):(?P<line>\d+):(?:(?P<col>\d+):)?\s*(?P<msg>.*)'),re.compile(r'(?P<file>[A-Za-z0-9_./\\-]+\.java):(?P<line>\d+):\s*(?P<msg>.*)')]
 for line in text.splitlines():
  for p in pats:
   m=p.search(line)
   if m:
    f=Path(m.group('file')).name;ln=int(m.group('line'));bid=smap.lookup(f,ln);out.append({'file':f,'line':ln,'message':m.group('msg').strip(),'block_id':bid});break
 return out

# --------------------------- GUI ---------------------------
class App(tk.Tk):
 def __init__(self):
  super().__init__();self.title(f'{APP} {VERSION}');self.geometry('1500x900');self.minsize(1100,700);self.configure(bg='#111318');self.project=Project();self.selected=None;self.errors=set();self.flash=False;self.drag=None;self.online_versions=[];self._style();self.ui();self.load_ui();self.after(400,self.flash_errors)
 def _style(self):
  s=ttk.Style(self)
  try:s.theme_use('clam')
  except:pass
  s.configure('.',background='#20232b',foreground='#eee');s.configure('TButton',background='#30343e',foreground='#fff',padding=7);s.configure('TLabel',background='#20232b',foreground='#eee');s.configure('TCombobox',fieldbackground='#2a2d35',foreground='#fff')
 def ui(self):
  top=tk.Frame(self,bg='#0b0d11',height=54);top.pack(fill='x')
  tk.Label(top,text='EASYMOD',bg='#0b0d11',fg='white',font=('TkDefaultFont',17,'bold')).pack(side='left',padx=14)
  for n,f in [('New',self.new),('Open',self.open),('Save',self.save),('Sync Versions',self.sync),('Generate',self.generate),('Build',self.build),('Run',self.run),('Export',self.export)]:tk.Button(top,text=n,command=f,bg='#2d313b',fg='white',relief='flat',padx=11).pack(side='left',padx=2,pady=8)
  self.status=tk.Label(top,text='Ready',bg='#0b0d11',fg='#9ca3af');self.status.pack(side='right',padx=15)
  pan=tk.PanedWindow(self,orient='horizontal',bg='#0b0d11',sashwidth=4);pan.pack(fill='both',expand=True)
  left=tk.Frame(pan,bg='#20232b',width=240);center=tk.Frame(pan,bg='#15171c');right=tk.Frame(pan,bg='#20232b',width=330);pan.add(left,minsize=220);pan.add(center,minsize=600);pan.add(right,minsize=300)
  tk.Label(left,text='BLOCK PALETTE',bg='#20232b',fg='#aab0bb',font=('TkDefaultFont',10,'bold')).pack(anchor='w',padx=12,pady=10)
  self.tree=ttk.Treeview(left,show='tree');self.tree.pack(fill='both',expand=True,padx=7);cats={}
  for typ,(cat,name) in BLOCKS.items():cats.setdefault(cat,self.tree.insert('', 'end',text=cat,open=True))
  for typ,(cat,name) in BLOCKS.items():self.tree.insert(cats[cat],'end',iid='p:'+typ,text=name)
  self.tree.bind('<Double-1>',self.add_block)
  tk.Label(center,text='BLOCK WORKSPACE',bg='#15171c',fg='#aab0bb',font=('TkDefaultFont',10,'bold')).pack(anchor='w',padx=10,pady=8)
  self.cv=tk.Canvas(center,bg='#101217',highlightthickness=0);self.cv.pack(fill='both',expand=True,padx=7);self.cv.bind('<Button-1>',self.click);self.cv.bind('<B1-Motion>',self.move);self.cv.bind('<ButtonRelease-1>',self.release);self.cv.bind('<Double-1>',self.double)
  tk.Label(right,text='PROJECT',bg='#20232b',fg='#aab0bb',font=('TkDefaultFont',10,'bold')).pack(anchor='w',padx=12,pady=9)
  f=tk.Frame(right,bg='#20232b');f.pack(fill='x',padx=10)
  self.name=tk.StringVar();self.mid=tk.StringVar();self.mc=tk.StringVar();self.loader=tk.StringVar()
  for lab,var in [('Name',self.name),('Mod ID',self.mid)]:tk.Label(f,text=lab,bg='#20232b',fg='#bbb').pack(anchor='w');tk.Entry(f,textvariable=var,bg='#2a2d35',fg='white',insertbackground='white',relief='flat').pack(fill='x',pady=(0,7))
  tk.Label(f,text='Minecraft',bg='#20232b',fg='#bbb').pack(anchor='w');self.mcb=ttk.Combobox(f,textvariable=self.mc,state='readonly');self.mcb.pack(fill='x',pady=(0,7));self.mcb.bind('<<ComboboxSelected>>',lambda e:self.mc_changed())
  tk.Label(f,text='Loader',bg='#20232b',fg='#bbb').pack(anchor='w');self.lb=ttk.Combobox(f,textvariable=self.loader,state='readonly');self.lb.pack(fill='x',pady=(0,7));self.lb.bind('<<ComboboxSelected>>',lambda e:self.changed())
  tk.Label(right,text='BLOCK PROPERTIES',bg='#20232b',fg='#aab0bb',font=('TkDefaultFont',10,'bold')).pack(anchor='w',padx=12,pady=10)
  self.info=tk.Label(right,text='Select a block.',bg='#20232b',fg='white',justify='left',anchor='nw');self.info.pack(fill='x',padx=12)
  self.fields=tk.Frame(right,bg='#20232b');self.fields.pack(fill='x',padx=10,pady=5)
  tk.Button(right,text='Delete block',command=self.delete,bg='#52282b',fg='white',relief='flat').pack(fill='x',padx=10,pady=5);tk.Button(right,text='View generated code',command=self.code,bg='#30343e',fg='white',relief='flat').pack(fill='x',padx=10)
  bot=tk.Frame(self,bg='#090b0e',height=180);bot.pack(fill='x');tk.Label(bot,text='BUILD / DIAGNOSTICS',bg='#090b0e',fg='#aab0bb').pack(anchor='w',padx=8);self.out=tk.Text(bot,bg='#090b0e',fg='#d5d7dd',height=8,relief='flat');self.out.pack(fill='both',expand=True,padx=8,pady=3)
  self.name.trace_add('write',lambda *_:self.changed());self.mid.trace_add('write',lambda *_:self.changed())
 def load_ui(self):
  d=self.project.data;self.name.set(d['name']);self.mid.set(d['mod_id']);self.mc.set(d['minecraft']);self.set_loaders();self.loader.set(d['loader']);self.draw()
 def changed(self,*a):self.project.data['name']=self.name.get();self.project.data['mod_id']=slug(self.mid.get());self.project.data['loader']=self.loader.get() or self.project.data['loader'];self.project.dirty=True
 def mc_changed(self):self.project.data['minecraft']=self.mc.get();self.set_loaders();self.changed()
 def set_loaders(self):
  mc=self.mc.get(); vals=['forge']
  if supports_fabric(mc): vals.append('fabric')
  if supports_neoforge(mc): vals.append('neoforge')
  self.lb['values']=vals
  if self.loader.get() not in vals:self.loader.set(vals[0])
 def sync(self):
  self.status.config(text='Downloading version manifest…')
  def w():
   v=fetch_versions()
   def done():
    if v:
     # Keep the requested range plus current official releases.
     self.online_versions=v;self.mcb['values']=v;self.status.config(text=f'{len(v)} Minecraft releases loaded')
    else:self.mcb['values']=list(dict.fromkeys(['1.7.10','1.12.2','1.16.5','1.20.1','1.21.1','26.1','26.2']));self.status.config(text='Offline version list loaded')
   self.after(0,done)
  threading.Thread(target=w,daemon=True).start()
 def new(self):
  if self.project.dirty and not messagebox.askyesno('Unsaved','Discard changes?'):return
  self.project=Project();self.selected=None;self.errors.clear();self.load_ui()
 def open(self):
  p=filedialog.askopenfilename(filetypes=[('EasyMod','*.easymod'),('JSON','*.json')]);
  if not p:return
  try:self.project=Project.load(p);self.selected=None;self.load_ui();self.status.config(text='Opened')
  except Exception as e:messagebox.showerror('Open failed',str(e))
 def save(self):
  if not self.project.path:
   p=filedialog.asksaveasfilename(defaultextension='.easymod',filetypes=[('EasyMod','*.easymod')]);
   if not p:return
   self.project.path=Path(p)
  try:self.project.save();self.status.config(text='Saved')
  except Exception as e:messagebox.showerror('Save failed',str(e))
 def add_block(self,e=None):
  s=self.tree.selection()
  if not s or not s[0].startswith('p:'):return
  typ=s[0][2:];i=len(self.project.data['blocks']);b={'id':uid(),'type':typ,'x':80+(i%4)*250,'y':80+(i//4)*95,'fields':dict(FIELD_DEFAULTS.get(typ,{}))};self.project.data['blocks'].append(b);self.selected=b['id'];self.project.dirty=True;self.properties(b);self.draw()
 def find(self,x,y):
  for b in reversed(self.project.data['blocks']):
   bx,by=b.get('x',80),b.get('y',80)
   if bx<=x<=bx+215 and by<=y<=by+70:return b
 def click(self,e):
  b=self.find(e.x,e.y);self.selected=b['id'] if b else None
  if b:self.drag=(b,e.x-b['x'],e.y-b['y']);self.properties(b)
  self.draw()
 def move(self,e):
  if self.drag:
   b,ox,oy=self.drag;b['x']=max(10,e.x-ox);b['y']=max(10,e.y-oy);self.project.dirty=True;self.draw()
 def release(self,e):self.drag=None
 def double(self,e):
  b=self.find(e.x,e.y)
  if b:self.selected=b['id'];self.properties(b)
 def properties(self,b):
  for w in self.fields.winfo_children():w.destroy()
  self.info.config(text=f'{BLOCKS.get(b["type"],("Advanced",b["type"]))[1]}\n{b["id"]}')
  for k,v in b.get('fields',{}).items():
   tk.Label(self.fields,text=k,bg='#20232b',fg='#aaa').pack(anchor='w');var=tk.StringVar(value=str(v));ent=tk.Entry(self.fields,textvariable=var,bg='#2a2d35',fg='white',insertbackground='white',relief='flat');ent.pack(fill='x',pady=(0,4));ent.bind('<FocusOut>',lambda e,k=k,var=var:self.setfield(k,var.get()))
 def setfield(self,k,v):
  b=next((x for x in self.project.data['blocks'] if x['id']==self.selected),None)
  if b:b['fields'][k]=v;self.project.dirty=True;self.draw()
 def delete(self):
  if not self.selected:return
  self.project.data['blocks']=[b for b in self.project.data['blocks'] if b['id']!=self.selected];self.selected=None;self.project.dirty=True;self.draw()
 def draw(self):
  self.cv.delete('all');self.cv.create_text(12,12,anchor='nw',text='Double-click a palette block to add it. Drag blocks to arrange.',fill='#5f6672')
  for b in self.project.data['blocks']:
   x,y=b.get('x',80),b.get('y',80);broken=b['id'] in self.errors and self.flash;sel=b['id']==self.selected;fill='#8b1e25' if broken else '#303540';outline='#ff3344' if broken else ('#fff' if sel else '#596170');self.cv.create_rectangle(x,y,x+215,y+70,fill=fill,outline=outline,width=3 if broken else 1)
   cat,n=BLOCKS.get(b['type'],('Advanced',b['type']));self.cv.create_text(x+10,y+8,anchor='nw',text=cat.upper(),fill='#a5acb8',font=('TkDefaultFont',8,'bold'));self.cv.create_text(x+10,y+28,anchor='nw',text=n,fill='white')
   self.cv.create_text(x+10,y+48,anchor='nw',text=self.preview(b),fill='#d2d5db')
   if b.get('next'): self.cv.create_line(x+215,y+35,x+245,y+35,fill='#626a78',width=2)
 def preview(self,b):
  f=b.get('fields',{});t=b['type']
  for k in ('message','item','block','entity','effect','value','name'):
   if k in f:return str(f[k])[:27]
  return ''
 def workspace(self):
  self.save();w=WORK/self.project.data['mod_id'];w.mkdir(parents=True,exist_ok=True);r=Resolver().resolve(self.project.data['minecraft'],self.project.data['loader']);ProjectGenerator(self.project,r).generate(w);return w
 def generate(self):
  try:w=self.workspace();self.status.config(text=f'Generated {w}');self.log('Generated project and source map.')
  except Exception as e:messagebox.showerror('Generate failed',str(e));self.log('ERROR: '+str(e))
 def build(self):
  try:w=self.workspace()
  except Exception as e:messagebox.showerror('Build setup failed',str(e));return
  self.errors.clear();self.draw();self.log('Starting build…');self.status.config(text='Building…')
  def worker():
   exe=ToolchainManager(self.log).command(self.project.data['minecraft'],self.project.data['loader'],w)
   cmd=[exe,'build','--stacktrace']
   try:
    p=subprocess.Popen(cmd,cwd=w,env=ToolchainManager(self.log).environment(self.project.data['minecraft'],self.project.data['loader']),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    lines=[]
    for line in p.stdout:
     lines.append(line.rstrip());self.after(0,self.log,line.rstrip())
    code=p.wait();sm=SourceMap.load(w/'easymod.sourcemap.json');ds=diagnostics('\n'.join(lines),sm);self.after(0,self.finish_build,code,ds)
   except Exception as e:self.after(0,self.finish_build,127,[{'message':str(e),'block_id':None,'file':'','line':0}])
  threading.Thread(target=worker,daemon=True).start()
 def finish_build(self,code,ds):
  mapped={d['block_id'] for d in ds if d.get('block_id')};self.errors=mapped
  for d in ds:self.log(f'ERROR {d.get("file")}:{d.get("line")} → block {d.get("block_id") or "unmapped"}: {d.get("message")}')
  self.status.config(text='Build successful' if code==0 and not ds else 'Build failed — errors mapped to blocks');self.draw()
 def run(self):
  try:w=self.workspace();exe=ToolchainManager(self.log).command(self.project.data['minecraft'],self.project.data['loader'],w);cmd=[exe,'runClient'];subprocess.Popen(cmd,cwd=w,env=ToolchainManager(self.log).environment(self.project.data['minecraft'],self.project.data['loader']))
  except Exception as e:messagebox.showerror('Run failed',str(e))
 def export(self):
  try:w=self.workspace();dest=filedialog.asksaveasfilename(defaultextension='.zip',filetypes=[('ZIP','*.zip')],initialfile=self.project.data['mod_id']+'.zip');
  except Exception as e:messagebox.showerror('Export failed',str(e));return
  if not dest:return
  with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
   for f in w.rglob('*'):
    if f.is_file():z.write(f,f.relative_to(w))
  self.status.config(text='Exported');messagebox.showinfo('Export','Project exported.')
 def code(self):
  try:w=self.workspace();src=w/'src/main/java/generated/EasyModGenerated.java';win=tk.Toplevel(self);win.title('EasyMod Generated Code');win.geometry('1000x700');t=tk.Text(win,bg='#0d0f12',fg='#ddd',font=('Courier New',10));t.pack(fill='both',expand=True);t.insert('1.0',src.read_text(encoding='utf8'))
  except Exception as e:messagebox.showerror('Code generation failed',str(e))
 def log(self,s):self.out.insert('end',str(s)+'\n');self.out.see('end')
 def flash_errors(self):
  if self.errors:self.flash=not self.flash;self.draw()
  self.after(450,self.flash_errors)

if __name__=='__main__':App().mainloop()
