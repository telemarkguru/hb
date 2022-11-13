from ._path import pathset, relative, cwd
import sys


def explist():
    paths = pathset(sys.argv[1:], anchor=cwd())
    for p in relative(cwd(), paths):
        print(p)


def main():
    print("RUN")
