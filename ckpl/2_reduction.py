import click
import numpy as np


@click.command()
@click.option('--science', prompt='Science images')
def cli(science):
    click.echo(science)
    run(ctx={})


def run(ctx, science, dark, bias, flat):
    return np.array([]), np.array([])