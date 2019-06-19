import subprocess
import click
from os import path, rename, remove
import pathlib
from astropy.table import Table
from astropy.io import ascii


@click.command()
@click.option(
    '-r',
    '--reducedtable',
    default='./reduced.dat',
    type=click.Path(exists=True, file_okay=True, readable=True, resolve_path=True))
@click.argument(
    'outdir',
    default='./out',
    type=click.Path(exists=False, dir_okay=True, writable=True, resolve_path=True))
@click.option('--blind', is_flag=True, help='Do blind Astrometry?')
def cli(reducedtable, outdir, blind):

    ast_path = path.join(outdir, 'ast')
    pathlib.Path(ast_path).mkdir(parents=True, exist_ok=True)

    reduced_table = Table.read(reducedtable, format='ascii.ecsv')
    reduced_table = astrometrize(reduced_table, blind)
    ascii.write(reduced_table, 'reduced.dat', format='ecsv', overwrite=True)


def astrometrize(reduced_table, blind, rdls=False):
    """
    This function run astrometry.net software to perform blind astrometry.
    :param file:
    :param blind:
    :return:
    """

    options = {
        'tweak-order': 3,
        'downsample': 2,
        'overwrite': '',
        'no-plots': '',
        'cpulimit': 30,

        'axy': 'none',
        'corr': 'none',
        'solved': 'none',
        'match': 'none',
        'rdls': 'none',
        'index-xyls': 'none',

        'scale-units': 'arcsecperpix',
        'scale-low': 0.46,
        'scale-high': 0.47
    }

    if rdls is False:
        options['rdls'] = 'none'

    with click.progressbar(length=len(reduced_table), label='images astrometrically calibrated') as bar:
        for i, row in enumerate(reduced_table):
            filename = row['filename']
            base, ext = path.splitext(filename)
            extra_options = {
                'ra': str(row['ra']).replace(' ', ':'),
                'dec': str(row['dec']).replace(' ', ':'),
                'radius': 0.5,
                'dir': path.dirname(row['filename'])
            }
            options_i = options if blind else {**options, **extra_options}

            options_str = ' '.join([f'--{key} {val}' for key, val in options_i.items()])

            try:
                cmd = f'solve-field {options_str} {filename}'
                subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, shell=True)
                row['flag_astr'] = True
                rename(base + '.new', row['filename'])
                remove(base + '.wcs')
            except Exception as err:
                print("Astrometry.net failed", err)
            finally:
                bar.update(1)

    return reduced_table
