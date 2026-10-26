"""Check the delivered artifacts, not model semantic quality."""
from pathlib import Path
import json, subprocess, hashlib, concurrent.futures
from urllib.parse import urlsplit, unquote
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'verification';OUT.mkdir(exist_ok=True)
TASKS=json.loads((ROOT/'tasks.json').read_text(encoding='utf-8'))

def check_video(path):
    probe=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],capture_output=True,text=True,check=True)
    metadata=json.loads(probe.stdout);video=next(s for s in metadata['streams'] if s['codec_type']=='video')
    decoded=subprocess.run(['ffmpeg','-hide_banner','-v','error','-xerror','-i',str(path),'-f','null','-'],capture_output=True,text=True)
    return {'path':path.relative_to(ROOT).as_posix(),'width':video['width'],'height':video['height'],'duration':float(metadata['format']['duration']),'fps':video['avg_frame_rate'],'codec':video['codec_name'],'decoded':decoded.returncode==0,'errors':decoded.stderr}

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    media=list(pool.map(check_video,sorted((ROOT/'cases').rglob('*.mp4'))))
report={'media':media,'browser_errors':[],'missing_links':[],'browser_playback':[]}
with sync_playwright() as p:
    chrome=next((str(x) for x in [Path(r'C:\Program Files\Google\Chrome\Application\chrome.exe'),Path(r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe')] if x.exists()),None)
    browser=p.chromium.launch(executable_path=chrome,headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1000})
    page.on('pageerror',lambda e:report['browser_errors'].append(str(e)))
    page.goto((ROOT/'index.html').as_uri())
    report['cards']=page.locator('.card').count()
    assert report['cards']==5
    report['prompt_lengths']=page.locator('.prompt pre').evaluate_all('(els)=>els.map(e=>e.textContent.length)')
    assert all(x>1000 for x in report['prompt_lengths'])
    links=page.locator('[href],[src],[poster]').evaluate_all('(els)=>els.flatMap(e=>[e.getAttribute("href"),e.getAttribute("src"),e.getAttribute("poster")].filter(Boolean))')
    for link in links:
        parsed=urlsplit(link)
        if not parsed.scheme and parsed.path and not (ROOT/unquote(parsed.path)).exists():report['missing_links'].append(link)
    for i in range(page.locator('video').count()):
        result=page.locator('video').nth(i).evaluate('''async (v)=>{
          v.muted=true; v.load();
          return await Promise.race([(async()=>{
            await v.play();await new Promise(r=>setTimeout(r,300));v.pause();
            return {path:v.getAttribute('src'),duration:v.duration,width:v.videoWidth,height:v.videoHeight,played:v.currentTime>0,error:v.error&&v.error.message};
          })().catch(e=>({path:v.getAttribute('src'),error:String(e)})),new Promise(r=>setTimeout(()=>r({path:v.getAttribute('src'),error:'timeout'}),12000))]);
        }''')
        report['browser_playback'].append(result)
    page.reload();page.wait_for_timeout(600)
    page.screenshot(path=str(OUT/'showcase.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':844})
    report['mobile_no_overflow']=page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.screenshot(path=str(OUT/'showcase_mobile.png'),full_page=True)
    for task in TASKS:
        cid=task['task_id'];page.set_viewport_size({'width':1280,'height':800})
        page.goto((ROOT/'animation.html').as_uri()+f'?case={cid}&render=1')
        for t in [0,1,5,12,20,30,page.evaluate('duration')-0.01]:page.evaluate('(t)=>renderAt(t)',t)
        page.locator('#seek').fill('10');page.locator('#toggle').click()
    browser.close()
report['passed']=all(x['decoded'] for x in media) and not report['browser_errors'] and not report['missing_links'] and all(x.get('played') for x in report['browser_playback']) and report['mobile_no_overflow']
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
manifest={'dataset':'Code2Video-Compass public 180-task preview','dataset_license':'CC BY-NC 4.0','answer_author':'Codex, current conversation, tool-assisted iterative code generation','exact_model_version':'not independently available','official_model_outputs':False,'official_scores':None,'answer_count_per_task':1,'format':'1280x720 H.264 24fps, no audio','cases':[],'files':[]}
for r in TASKS:
    folder=ROOT/'cases'/r['task_id']
    answer={'author':manifest['answer_author'],'generated_by_current_session':True,'source_code':['../../animation.html','../../animation.js'],'artifact':'answer_codex.mp4','source_video_is_answer':False,'evaluation_status':'not scored; execution verified only'}
    (folder/'answer_metadata.json').write_text(json.dumps(answer,ensure_ascii=False,indent=2),encoding='utf-8')
    manifest['cases'].append({'task_id':r['task_id'],'reference':json.loads((folder/'reference_status.json').read_text(encoding='utf-8')),'answer':answer})
for path in sorted(ROOT.rglob('*')):
    if path.is_file() and path.name!='manifest.json' and '__pycache__' not in path.parts:
        manifest['files'].append({'path':path.relative_to(ROOT).as_posix(),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(ROOT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'passed':report['passed'],'videos':len(media),'players':len(report['browser_playback']),'cards':report['cards'],'missing_links':report['missing_links'],'browser_errors':report['browser_errors']},ensure_ascii=False),flush=True)
if not report['passed']:raise SystemExit(1)
