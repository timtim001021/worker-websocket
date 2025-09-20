#!/usr/bin/env python3
"""
Create diagnostic records for WAV payloads the Worker builds.
Usage:
  python3 record_encoded.py --file /path/to/file.wav [--full]

This will create a directory `test/encoded_records/<timestamp>/` with:
 - meta.json (sample rate, samples, bytes length)
 - head.b64 (first 64 bytes base64)
 - tail.b64 (last 64 bytes base64)
 - full.b64 (optional full wav base64, large)
 - as_json_array.json (optional: the numeric array the worker currently sends)
"""

import argparse
import os
import wave
import struct
import json
import base64
import datetime


def build_wav_bytes(samples, sample_rate=16000, num_channels=1, bits_per_sample=16):
    # samples: list of signed 16-bit ints
    # create pcm bytes little-endian
    pcm = struct.pack('<' + 'h' * len(samples), *samples)

    num_channels = num_channels
    bits_per_sample = bits_per_sample
    block_align = num_channels * bits_per_sample // 8
    byte_rate = sample_rate * block_align
    data_size = len(pcm)

    # build header
    header = bytearray(44)
    def write_string(b, offset, s):
        b[offset:offset+len(s)] = s.encode('ascii')

    write_string(header, 0, 'RIFF')
    header[4:8] = (36 + data_size).to_bytes(4, 'little')
    write_string(header, 8, 'WAVE')
    write_string(header, 12, 'fmt ')
    header[16:20] = (16).to_bytes(4, 'little')
    header[20:22] = (1).to_bytes(2, 'little')
    header[22:24] = (num_channels).to_bytes(2, 'little')
    header[24:28] = (sample_rate).to_bytes(4, 'little')
    header[28:32] = (byte_rate).to_bytes(4, 'little')
    header[32:34] = (block_align).to_bytes(2, 'little')
    header[34:36] = (bits_per_sample).to_bytes(2, 'little')
    write_string(header, 36, 'data')
    header[40:44] = (data_size).to_bytes(4, 'little')

    return bytes(header) + pcm


def read_wav_file(path):
    with wave.open(path, 'rb') as wf:
        channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        nframes = wf.getnframes()
        raw = wf.readframes(nframes)

    if sampwidth != 2:
        raise RuntimeError('Only 16-bit PCM supported')

    fmt = '<' + 'h' * (len(raw)//2)
    ints = list(struct.unpack(fmt, raw))

    if channels == 2:
        ints = ints[0::2]

    return ints, framerate


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', '-f', required=True)
    parser.add_argument('--full', action='store_true', help='also save full base64 (can be large)')
    parser.add_argument('--as-json-array', action='store_true', help='also save the numeric JSON array (worker approach)')
    args = parser.parse_args()

    samples, sr = read_wav_file(args.file)
    print(f'Read {len(samples)} samples at {sr} Hz')

    wav = build_wav_bytes(samples, sample_rate=sr)

    ts = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    outdir = os.path.join(os.path.dirname(__file__), 'encoded_records', ts)
    ensure_dir(outdir)

    meta = {'file': args.file, 'samples': len(samples), 'sample_rate': sr, 'wav_bytes': len(wav)}
    with open(os.path.join(outdir, 'meta.json'), 'w') as f:
        json.dump(meta, f, indent=2)

    head = wav[:64]
    tail = wav[-64:]
    with open(os.path.join(outdir, 'head.b64'), 'wb') as f:
        f.write(base64.b64encode(head))
    with open(os.path.join(outdir, 'tail.b64'), 'wb') as f:
        f.write(base64.b64encode(tail))

    if args.full:
        with open(os.path.join(outdir, 'full.b64'), 'wb') as f:
            f.write(base64.b64encode(wav))

    if args.as_json_array:
        # This creates the same array the worker currently sends: an array of ints representing each byte
        arr = list(wav)
        with open(os.path.join(outdir, 'as_json_array.json'), 'w') as f:
            json.dump({'bytes': arr, 'length': len(arr)}, f)

    print('Wrote diagnostics to', outdir)

if __name__ == '__main__':
    main()
