import click
import pathlib
from os.path import join
from os import path
from astropy.io import ascii
from . import preprocessing
from . import reduction
from . import astrometry


@click.command()
@click.argument(
    'imdir',
    default='.',
    type=click.Path(exists=True, dir_okay=True, readable=True, resolve_path=True))
@click.argument(
    'outdir',
    default='./out',
    type=click.Path(exists=False, dir_okay=True, writable=True, resolve_path=True))
@click.option('--blind', is_flag=True, help='Do blind Astrometry?')
@click.option('--nosave', is_flag=True, help='Use to no save the intermediate calibration files')
def main(imdir, outdir, blind, nosave):

    reduced_path = join(outdir, 'reduced')
    # ast_path = join(outdir, 'ast') delete

    pathlib.Path(reduced_path).mkdir(parents=True, exist_ok=True)
    # pathlib.Path(ast_path).mkdir(parents=True, exist_ok=True) delete
    if not nosave:
        calib_path = path.join(outdir, 'calib')
        pathlib.Path(calib_path).mkdir(parents=True, exist_ok=True)

    click.echo("Exploring the files...")
    table_raw = preprocessing.ls(imdir)
    click.echo("Making the reduction...")
    table_reduced = reduction.reduce(table_raw, reduced_path, calib_path).table_reduced
    click.echo("Astrometrizing...")
    astrometry.astrometrize(table_reduced, blind)
    ascii.write(table_reduced, 'reduced.dat', format='ecsv', overwrite=True)

    click.echo(str(table_reduced))

if __name__ == '__main__':
    main()

