"""Pick a varied, repeatable sample of Wasalt listing URLs (pure function).

Used to prepare the list of pages a human saves by hand, since automated access
is blocked by a bot challenge (see docs/decisions/0001-wasalt-access-note.md).
"""
from __future__ import annotations

import random
import re
from collections import defaultdict

_LISTING = re.compile(r"/en/property/(sale|rent)/([a-z]+)-[^/]*-sqm-with-(\d+)-bedrooms-\d+$")


def stratified_sample(urls: list[str], n: int, seed: int) -> list[str]:
    groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    for url in dict.fromkeys(urls):
        match = _LISTING.search(url)
        if match:
            groups[(match.group(1), match.group(2))].append(url)

    rng = random.Random(seed)
    queues = []
    for key in sorted(groups):
        members = groups[key][:]
        rng.shuffle(members)
        queues.append(members)
    rng.shuffle(queues)

    picked: list[str] = []
    while queues and len(picked) < n:
        for queue in list(queues):
            if len(picked) >= n:
                break
            picked.append(queue.pop())
            if not queue:
                queues.remove(queue)
    return picked
