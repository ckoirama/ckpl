from importlib import import_module
import click

preprocessing = import_module('ckpl.1_preprocessing')
reduction = import_module('ckpl.2_reduction')

@click.command()
def main(a):

    ctx = {}

    results = preprocessing.run(ctx)
    reduction.run(ctx, *results)
