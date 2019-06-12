import click

from . import preprocessing
from . import reduction


@click.command()
def main(a):

    ctx = {}

    results = preprocessing.run(ctx)
    reduction.run(ctx, *results)
