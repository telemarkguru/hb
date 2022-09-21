from . import path
import sys
import os


def explist():
    paths = path.pathset(sys.argv[1:], anchor=path.cwd())
    for p in path.relative(path.cwd(), paths):
        print(p)


def main():
    print("RUN")
