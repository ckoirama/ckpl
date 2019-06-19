from reproject import reproject_interp
from astropy.io import fits
import numpy as np
import click
from astropy.table import Table
from os import path


@click.command()
@click.option('-v', '--verbose', is_flag=True)
@click.option(
    '-r',
    '--reducedtable',
    default='./reduced.dat',
    type=click.Path(exists=True, file_okay=True, readable=True, resolve_path=True))
def cli(verbose, reducedtable):

    reduced_table = Table.read(reducedtable, format='ascii.ecsv')

    print(reduced_table)

    # work only with the astrometrized files
    align(reduced_table[reduced_table['flag_astr']])
    stack(reduced_table[reduced_table['flag_astr']])


def align(reduced_table):
    stack_ids = np.unique(np.array(reduced_table[reduced_table['stack'] is not None]['stack']))
    for stack_id in stack_ids:
        table_sci_stack = reduced_table[reduced_table['stack'] == stack_id]
        reference_row = table_sci_stack[0]
        for i in range(1, len(table_sci_stack)):
            data, footprint = reproject_interp(table_sci_stack[i]['filename'], reference_row['filename'])
            image = fits.PrimaryHDU(data)
            path_dir = path.dirname(table_sci_stack[i]['filename'])
            path_base = path.basename(table_sci_stack[i]['filename'])
            image.writeto(f'{path_dir}{path.sep}ALIGNED-{stack_id}-{path_base}.fit')


def stack(reduced_table):
    stack_ids = np.unique(np.array(reduced_table[reduced_table['stack'] is not None]['stack']))
    for stack_id in stack_ids:
        table_sci_stack = reduced_table[reduced_table['stack'] == stack_id]
        reference_row = table_sci_stack[0]
        for i, row in enumerate(table_sci_stack):
            with fits.open(row['filename']) as hdu:
                data = np.float64(hdu[0].data)
                if i == 0:
                    frame = np.atleast_3d(data)
                else:
                    frame = np.concatenate((frame, np.atleast_3d(data)), axis=2)
        path_dir = path.dirname(reference_row['filename'])
        path_base = path.basename(reference_row['filename'])
        # todo make this more robust
        fits.PrimaryHDU(np.median(frame, axis=2)).writeto(f'{path_dir}{path.sep}STACKED-{stack_id}-{path_base}.fit')
