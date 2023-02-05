from ._path import pathset, relative, context
import click
from os import getcwd


@click.command()
@click.option("-a", "--absolute", help="Output absolute paths")
@click.argument("listfiles", nargs=-1)
def explist(absolute, listfiles):
    ctx = context()
    paths = pathset(ctx, listfiles)
    if absolute:
        for p in paths:
            print(p)
    else:
        for p in relative(getcwd(), paths):
            print(p)


def main():
    print("RUN")
