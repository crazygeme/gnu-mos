"""Capture host microphone and output monitor while executing a guest audio test."""
import argparse
import array
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys
import time
import wave


def analyze(path, frequency):
    with wave.open(str(path), "rb") as stream:
        rate, channels = stream.getframerate(), stream.getnchannels()
        samples = array.array("h", stream.readframes(stream.getnframes()))
    if sys.byteorder != "little":
        samples.byteswap()
    signal = [v / 32768 for v in samples[::channels]]
    block = rate // 100
    rms = [math.sqrt(sum(v * v for v in signal[i:i + block]) / block)
           for i in range(0, len(signal) - block + 1, block)]
    baseline = statistics.median(rms[:50]) if rms else 0
    active = [i for i, value in enumerate(rms)
              if value > max(baseline * 4, 0.0005)]
    result = {"rate": rate, "seconds": len(signal) / rate,
              "peak": max(map(abs, signal), default=0),
              "baseline_rms": baseline, "active_blocks": len(active),
              "clipped_samples": sum(abs(value) >= 0.9999 for value in signal)}
    if active:
        first, last = active[0] + 10, active[-1] - 10
        core = rms[first:last + 1]
        if core:
            median = statistics.median(core)
            result.update(active_start=active[0] / 100,
                          active_end=(active[-1] + 1) / 100,
                          active_rms=median,
                          low_blocks=sum(value < median * 0.25 for value in core),
                          min_block_rms=min(core))
            if frequency:
                data = signal[first * block:(last + 1) * block:4]
                # Integer-Hz Goertzel analysis uses the full steady interval.
                def power(hz):
                    coefficient = 2 * math.cos(2 * math.pi * hz / (rate / 4))
                    a = b = 0
                    for value in data:
                        next_value = value + coefficient * b - a
                        a, b = b, next_value
                    return a * a + b * b - coefficient * a * b
                candidates = range(round(frequency) - 10, round(frequency) + 11)
                result["dominant_hz_near_reference"] = max(candidates, key=power)
                result["max_sample_step"] = max(
                    (abs(b - a) for a, b in zip(
                        signal[first * block:last * block],
                        signal[first * block + 1:last * block + 1])), default=0)
                core_signal = signal[first * block:last * block]
                silence_runs, run = [], 0
                for value in core_signal:
                    if abs(value) < 1 / 32768:
                        run += 1
                    else:
                        if run >= rate / 1000:
                            silence_runs.append(run * 1000 / rate)
                        run = 0
                if run >= rate / 1000:
                    silence_runs.append(run * 1000 / rate)
                result["digital_silence_runs_ms"] = silence_runs
                limit = 2 * math.sqrt(2) * median * 2 * math.sin(math.pi * frequency / rate)
                result["large_sample_steps"] = sum(
                    abs(b - a) > limit for a, b in zip(core_signal, core_signal[1:]))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--name", default="audio")
    parser.add_argument("--frequency", type=float)
    parser.add_argument("--microphone", default="@DEFAULT_SOURCE@")
    parser.add_argument("--monitor", default="@DEFAULT_MONITOR@")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("A playback command is required")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    try:
        for label, device in (("mic", args.microphone), ("monitor", args.monitor)):
            raw = args.output_dir / f"{args.name}-{label}.raw"
            output = raw.open("wb")
            proc = subprocess.Popen([
                "parec", "--device=" + device, "--rate=48000", "--channels=2",
                "--format=s16le", "--latency-msec=20", "--process-time-msec=10", "--raw"], stdout=output, stderr=subprocess.PIPE)
            records.append((label, raw, output, proc))
        time.sleep(1)
        completed = subprocess.run(command, capture_output=True, text=True)
        (args.output_dir / f"{args.name}-playback.log").write_text(
            completed.stdout + completed.stderr)
        print(completed.stdout + completed.stderr, end="")
        time.sleep(1)
    finally:
        for _, _, output, proc in records:
            proc.terminate()
            proc.wait(timeout=5)
            output.close()
    results = {}
    for label, raw, _, proc in records:
        error = proc.stderr.read().decode()
        if error:
            print(error, file=sys.stderr)
        wav = raw.with_suffix(".wav")
        with wave.open(str(wav), "wb") as stream:
            stream.setnchannels(2)
            stream.setsampwidth(2)
            stream.setframerate(48000)
            stream.writeframes(raw.read_bytes())
        raw.unlink()
        results[label] = analyze(wav, args.frequency)
        if label == "mic":
            results[label].pop("digital_silence_runs_ms", None)
            results[label].pop("large_sample_steps", None)
        results[label]["source"] = (subprocess.check_output(
            ["pactl", "get-default-source" if label == "mic" else "get-default-sink"],
            text=True).strip() + (".monitor" if label == "monitor" else "")) if (
                (label == "mic" and args.microphone == "@DEFAULT_SOURCE@") or
                (label == "monitor" and args.monitor == "@DEFAULT_MONITOR@")) else (
                    args.microphone if label == "mic" else args.monitor)
    (args.output_dir / f"{args.name}-analysis.json").write_text(
        json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))
    if completed.returncode:
        return completed.returncode
    if not results["mic"]["active_blocks"] or not results["monitor"]["active_blocks"]:
        return 1
    if args.frequency:
        for result in results.values():
            if abs(result.get("dominant_hz_near_reference", 0) - args.frequency) > 1:
                return 1
            if result.get("low_blocks", 1) or result["clipped_samples"]:
                return 1
        if results["monitor"].get("digital_silence_runs_ms") or results["monitor"].get("large_sample_steps"):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
