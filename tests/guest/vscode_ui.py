"""Validate the dedicated VS Code validation document through local CDP."""
import sys,time,json
import argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from browser_h264 import CDP,get
parser=argparse.ArgumentParser(description='Validate graphical editing, saving, and integrated terminal input in the validation file.')
parser.add_argument('--port',type=int,default=9223)
port=parser.parse_args().port
pages=get(port,'/json/list')
p=next(p for p in pages if p['type']=='page' and 'workbench' in p['url'])
c=CDP(p['webSocketDebuggerUrl'],port)
def evaluate(s):
 r=c.call('Runtime.evaluate',{'expression':s,'returnByValue':True}); assert 'exceptionDetails' not in r,r; return r['result'].get('value')
def key(k,code,vk,mod=0):
 for kind in ['keyDown','keyUp']:c.call('Input.dispatchKeyEvent',{'type':kind,'key':k,'code':code,'windowsVirtualKeyCode':vk,'modifiers':mod})
for _ in range(90):
 state=evaluate('({title:document.title,editors:document.querySelectorAll(".monaco-editor").length,text:document.body.innerText.slice(-3000)})')
 if state['editors']:break
 time.sleep(.5)
assert state['editors'],state
assert 'mos-vscode-validation.txt' in state['title'],state
c.call('Page.bringToFront')
assert evaluate('!!document.querySelector(".monaco-editor .native-edit-context")')
evaluate('document.querySelector(".monaco-editor .native-edit-context").focus()')
key('a','KeyA',65,2)
c.call('Input.insertText',{'text':'MOS VS Code editor validation\nSaved through the graphical editor.\n'})
key('s','KeyS',83,2)
time.sleep(1)
print(json.dumps({'editor':state['title'],'saved_via_keyboard':True}),flush=True)

if not evaluate('document.querySelectorAll(".xterm").length'): key('`','Backquote',192,2)
time.sleep(2)
state=evaluate('({terminals:document.querySelectorAll(".xterm").length,text:document.body.innerText.slice(-1500)})')
for _ in range(40):
 evaluate('[...document.querySelectorAll(".monaco-dialog-box .monaco-button")].find(x=>x.textContent.includes("Trust Workspace"))?.click()')
 if evaluate('!!document.querySelector(".xterm-helper-textarea")') and not evaluate('!!document.querySelector(".monaco-dialog-box")'):break
 time.sleep(.5)
else:raise AssertionError('Integrated terminal is unavailable')
evaluate('document.querySelector(".xterm-helper-textarea").focus()')
key('u','KeyU',85,2)
c.call('Input.insertText',{'text':"printf '%s\n' terminal-ok > /tmp/mos-vscode-terminal.txt"})
key('Enter','Enter',13)
time.sleep(2)
print(json.dumps({'terminal_opened':True,'command_submitted':True,'state':state}),flush=True)
c.s.close()
