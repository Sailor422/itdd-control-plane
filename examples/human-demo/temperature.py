#!/usr/bin/env python3
"""Tiny demo application; the Builder candidate is produced by demo.py."""
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: temperature.py FAHRENHEIT", file=sys.stderr)
        return 2
    try:
        fahrenheit = float(sys.argv[1])
    except ValueError:
        print("error: temperature must be numeric", file=sys.stderr)
        return 2
    print((fahrenheit - 32) * 5 / 9)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
