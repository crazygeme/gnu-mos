"""Validate continuous browser video audio through a loopback DevTools connection."""
import argparse
import json
import time

from browser_h264 import CDP, get


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=9222)
    parser.add_argument("--seconds", type=int, default=60)
    parser.add_argument("--url-match", default="haokan.baidu.com/v?")
    args = parser.parse_args()
    if args.seconds < 10:
        parser.error("Duration must be at least ten seconds")
    target = next(item for item in get(args.port, "/json/list")
                  if item["type"] == "page" and args.url_match in item["url"])
    connection = CDP(target["webSocketDebuggerUrl"], args.port)
    connection.call("Media.enable")

    def evaluate(expression):
        response = connection.call("Runtime.evaluate", {
            "expression": expression, "returnByValue": True,
            "awaitPromise": True, "userGesture": True,
        })
        if "exceptionDetails" in response:
            raise RuntimeError(response["exceptionDetails"])
        return response["result"].get("value")

    canvas = evaluate("""(()=>{
        const c=document.createElement('canvas'),x=c.getContext('2d');
        x.fillStyle='#112233';x.fillRect(0,0,1,1);
        return [...x.getImageData(0,0,1,1).data];
    })()""")
    assert canvas == [17, 34, 51, 255], canvas
    ready_deadline = time.monotonic() + 30
    while not evaluate("""(()=>{
        const v=document.querySelector('video');
        return !!(v&&v.readyState>=2&&v.currentSrc);
    })()"""):
        if time.monotonic() >= ready_deadline:
            raise RuntimeError("Video media initialization timed out")
        time.sleep(0.5)
    initial = evaluate("""(async()=>{
        const v=document.querySelector('video');
        v.muted=false;v.volume=1;await v.play();
        return {time:v.currentTime,paused:v.paused};
    })()""")
    states = []
    started = previous_wall = time.monotonic()
    previous_time = initial["time"]
    failures = []
    try:
        while time.monotonic() - started < args.seconds:
            remaining = args.seconds - (time.monotonic() - started)
            if remaining <= 0:
                break
            time.sleep(min(5, remaining))
            state = evaluate("""(()=>{
                const v=document.querySelector('video'),q=v.getVideoPlaybackQuality();
                return {url:location.href,title:document.title,time:v.currentTime,
                    paused:v.paused,muted:v.muted,volume:v.volume,ready:v.readyState,
                    audioDecoded:v.webkitAudioDecodedByteCount,
                    videoFrames:q.totalVideoFrames,droppedFrames:q.droppedVideoFrames,
                    error:v.error&&v.error.message};
            })()""")
            now = time.monotonic()
            state["wallInterval"] = now - previous_wall
            state["mediaInterval"] = state["time"] - previous_time
            states.append(state)
            print(json.dumps(state, ensure_ascii=False), flush=True)
            if not state["url"].startswith("https://"):
                failures.append("HTTPS page is unavailable")
            if state["error"] or state["paused"] or state["muted"]:
                failures.append("Playback state is invalid")
            if state["mediaInterval"] < state["wallInterval"] * 0.85:
                failures.append("Media progress is below 85 percent of elapsed time")
            previous_wall, previous_time = now, state["time"]
    finally:
        evaluate("document.querySelector('video').pause(); true")
    properties = [event["params"] for event in connection.events if event.get("method") in
                  ("Media.playerErrorsRaised", "Media.playerPropertiesChanged")]
    print(json.dumps({"media": properties}, ensure_ascii=False), flush=True)
    assert not failures, failures
    assert states[-1]["audioDecoded"] > states[0]["audioDecoded"], states
    print("EDGE_AUDIO_OK https=1 javascript=1 canvas=1 audio=1 continuous=1", flush=True)


if __name__ == "__main__":
    main()
