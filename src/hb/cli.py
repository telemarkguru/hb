from ._path import pathset, relative, cwd
import click


@click.command()
@click.option("-a", "--absolute", help="Output absolute paths")
@click.argument("listfiles", nargs=-1)
def explist(absolute, listfiles):
    paths = pathset(listfiles, anchor=cwd())
    if absolute:
        for p in paths:
            print(p)
    else:
        for p in relative(cwd(), paths):
            print(p)


def main():
    print("RUN")
