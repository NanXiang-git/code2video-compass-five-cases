from pathlib import Path
import subprocess, shutil, argparse, base64, os
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent
CHROME=next((str(p) for p in [Path(os.environ.get('PROGRAMFILES','C:/Program Files'))/'Google/Chrome/Application/chrome.exe',Path(os.environ.get('PROGRAMFILES(X86)','C:/Program Files (x86)'))/'Microsoft/Edge/Application/msedge.exe'] if p.exists()),None)
cases=[('C2VC-0234-v2v',48),('C2VC-0504-i2v',52),('C2VC-0429-v2v',53),('C2VC-0035-i2v',60),('C2VC-0410-v2v',36)]
parser=argparse.ArgumentParser()
parser.add_argument('--fps',type=int,default=24)
parser.add_argument('--case',choices=[x[0] for x in cases])
args=parser.parse_args(); fps=args.fps
if not 1<=fps<=60: raise ValueError('fps must be 1..60')
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True, executable_path=CHROME)
    page=browser.new_page(viewport={'width':1280,'height':720}, device_scale_factor=1)
    for cid,duration in cases:
        if args.case and args.case!=cid: continue
        out=ROOT/'cases'/cid
        page.goto((ROOT/'animation.html').as_uri()+f'?case={cid}&render=1')
        page.wait_for_timeout(250)
        video=out/'answer_codex.mp4'; temporary=out/'answer_codex.rendering.mp4'
        proc=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','image2pipe','-framerate',str(fps),'-vcodec','mjpeg','-i','pipe:0','-an','-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-movflags','+faststart',str(temporary)],stdin=subprocess.PIPE)
        try:
            for i in range(int(duration*fps)):
                encoded=page.evaluate('(t)=>{window.renderAt(t); return document.querySelector("canvas").toDataURL("image/jpeg",0.94).split(",")[1]}', i/fps)
                proc.stdin.write(base64.b64decode(encoded))
                if i%(fps*10)==0: print(f'{cid} {i/fps:.0f}/{duration}s',flush=True)
        finally:
            proc.stdin.close()
        if proc.wait()!=0: raise RuntimeError(f'ffmpeg failed for {cid}')
        temporary.replace(video)
        poster_time={'C2VC-0234-v2v':22,'C2VC-0504-i2v':12.6,'C2VC-0429-v2v':18.5,'C2VC-0035-i2v':21,'C2VC-0410-v2v':27}[cid]
        page.evaluate('(t)=>renderAt(t)',poster_time)
        page.locator('canvas').screenshot(path=str(out/'answer_poster.jpg'),type='jpeg',quality=90)
        print(cid, video.stat().st_size,flush=True)
    browser.close()
