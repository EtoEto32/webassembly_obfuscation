"""Rooted labeled transition-isomorphism propagation, not a novel algorithm."""
import json
import sys
from collections import deque


def solve(source, target, root):
    n = len(source[0])
    mapping, reverse = [-1] * n, [-1] * n
    mapping[0], reverse[root] = root, 0
    queue = deque([0])
    while queue:
        x = queue.popleft()
        for s, t in zip(source, target):
            y, v = s[x], t[mapping[x]]
            if mapping[y] != -1:
                if mapping[y] != v:
                    return None
            else:
                if reverse[v] != -1:
                    return None
                mapping[y], reverse[v] = v, y
                queue.append(y)
    if -1 in mapping:
        raise ValueError("source is not reachable from its root")
    return mapping


if __name__ == "__main__":
    public = json.load(sys.stdin)
    print(json.dumps([solve(public["source"], c["transitions"], c["root"])
                      for c in public["cases"]]))
