"""Re-fetch public media from recorded official source URLs. No login or cookies."""
from pathlib import Path
import json, re, subprocess, requests

ROOT=Path(__file__).resolve().parent
HEADERS={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/132.0.0.0 Safari/537.36'}

for task in json.loads((ROOT/'tasks.json').read_text(encoding='utf-8')):
    folder=ROOT/'cases'/task['task_id']; full=folder/'reference_full.mp4'
    if not full.exists():
        source=task['reference_url']
        if 'x.com/' in source:
            result=requests.get('https://api.fxtwitter.com/status/'+source.rsplit('/',1)[-1],timeout=30)
            result.raise_for_status(); data=result.json()
            (folder/'source_metadata.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
            media=data['tweet']['media']['videos'][0]['url']
            route='Public FxTwitter metadata -> original media CDN'
        else:
            result=requests.get(source.replace('www.rednote.com','www.xiaohongshu.com'),headers=HEADERS,timeout=30)
            result.raise_for_status()
            match=re.search(r'"masterUrl"\s*:\s*"([^"]+)"',result.text)
            if not match: raise RuntimeError('Public page has no masterUrl. Existing package is unaffected.')
            media=json.loads('"'+match.group(1)+'"').replace('http://','https://')
            route='Public source HTML masterUrl; normal browser User-Agent; no login/cookies'
        response=requests.get(media,headers=HEADERS,timeout=120);response.raise_for_status()
        temp=folder/'reference_full.downloading';temp.write_bytes(response.content)
        subprocess.run(['ffprobe','-v','error',str(temp)],check=True);temp.replace(full)
        (folder/'reference_status.json').write_text(json.dumps({'status':'downloaded','bytes':full.stat().st_size,'media_url':media,'retrieval':route,'source_url':source},ensure_ascii=False,indent=2),encoding='utf-8')
    stamp=task.get('keyframe_timestamp_s',task.get('keyclip_start_s'))
    prefix=['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(stamp),'-i',str(full)]
    if task['task']=='i2v':
        args=['-frames:v','1',str(folder/'reference.png')]
    else:
        args=['-t',str(task['keyclip_end_s']-stamp),'-c:v','libx264','-crf','19','-an',str(folder/'reference.mp4')]
    subprocess.run(prefix+args,check=True)
    subprocess.run(prefix+['-frames:v','1','-vf','scale=960:-1',str(folder/'reference_preview.jpg')],check=True)
    print(task['task_id'],'ready',flush=True)
