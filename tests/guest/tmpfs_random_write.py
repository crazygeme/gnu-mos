#!/usr/bin/python3
"""Validate multi-page extension, positioned writes, and shared mapping coherence."""
import mmap
import os
import random
import tempfile

with tempfile.TemporaryFile(dir='/dev/shm') as stream:
    fd = stream.fileno()
    stream.write(b'X' * 512)
    stream.flush()
    expected = bytes((index * 17 + 3) % 251 for index in range(8192))
    os.lseek(fd, 0, os.SEEK_SET)
    assert os.write(fd, expected) == len(expected)
    actual = os.pread(fd, len(expected), 0)
    assert actual == expected, next((index for index, pair in enumerate(zip(actual, expected)) if pair[0] != pair[1]), 'length')
    model = bytearray(expected)
    randomizer = random.Random(7183)
    for iteration in range(40):
        offset = randomizer.randrange(6 * 4096)
        payload = randomizer.randbytes(randomizer.randrange(1, 3 * 4096))
        if offset + len(payload) > len(model):
            model.extend(b'\0' * (offset + len(payload) - len(model)))
        model[offset:offset + len(payload)] = payload
        assert os.pwrite(fd, payload, offset) == len(payload)
        assert os.pread(fd, len(model), 0) == model, iteration
    with mmap.mmap(fd, len(model), flags=mmap.MAP_SHARED, prot=mmap.PROT_READ | mmap.PROT_WRITE) as mapping:
        mapping[4090:4102] = b'mapped-write'
        model[4090:4102] = b'mapped-write'
        assert os.pread(fd, len(model), 0) == model
        os.pwrite(fd, b'positioned', 8190)
        model[8190:8200] = b'positioned'
        assert mapping[:] == model
print('TMPFS_RANDOM_WRITE_OK')
