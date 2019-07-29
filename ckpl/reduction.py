import click
import numpy as np
from astropy.io import fits
from astropy.table import Table
import pathlib
from os import path
import ntpath
from astropy.io import ascii
from collections import namedtuple

Reducted = namedtuple('Reducted', 'masterbias,masterdark,masterflats,table_reduced')


@click.command()
@click.option('-v', '--verbose', is_flag=True)
@click.option(
    '-r',
    '--rawtable',
    default='./raw.dat',
    type=click.Path(exists=True, file_okay=True, readable=True, resolve_path=True))
@click.argument(
    'outdir',
    default='./out',
    type=click.Path(exists=False, dir_okay=True, writable=True, resolve_path=True))
def cli(verbose, rawtable, outdir):

    calib_path = path.join(outdir, 'calib')
    reduced_path = path.join(outdir, 'reduced')

    # https://stackoverflow.com/a/600612
    pathlib.Path(calib_path).mkdir(parents=True, exist_ok=True)
    pathlib.Path(reduced_path).mkdir(parents=True, exist_ok=True)

    table = Table.read(rawtable, format='ascii.ecsv')

    masterbias, masterdark, masterflats, table_reduced = reduce(table, reduced_path)

    if masterbias:
        fits.PrimaryHDU(masterbias).writeto(path.join(calib_path, 'masterbias.fits'), overwrite=True)
    if masterdark:
        fits.PrimaryHDU(masterdark).writeto(path.join(calib_path, 'masterdark.fits'), overwrite=True)
    if masterflats:
        [
            fits.PrimaryHDU(masterflat).writeto(path.join(calib_path, f'masterflat_{band}.fits'), overwrite=True)
            for band, masterflat
            in masterflats.items()
        ]

    ascii.write(table_reduced, 'reduced.dat', overwrite=True, format='ecsv')

    if verbose:
        click.echo(table_reduced)


def reduce(table, reduced_path):
    """

    :param table: an astropy Table instance that contains the files that must be reduced
    :param reduced_path: a directory where the reduced images will be stored
    :return: Reducted
    """

    filenames_bias = np.array(table[table['imagetype'] == 'bias']['filename'])
    masterbias = make_masterbias(filenames_bias) if len(filenames_bias) > 0 else None

    table_darks = table[table['imagetype'] == 'dark']
    masterdark = make_masterdark(masterbias, table_darks) if len(table_darks) > 0 else None

    bands_flat = np.unique(table[table['imagetype'] == 'flat']['band'])
    images_flat_by_band = {
        band: table[(table['imagetype'] == 'flat') * (table['band'] == band)]
        for band in bands_flat
    }

    masterflats = {
        band: make_master_flat(images_flat, masterbias, masterdark) if masterdark is not None else None
        for band, images_flat in images_flat_by_band.items()
    }

    table_reduced = reducing_sci_by_band(table, reduced_path, masterbias, masterdark, masterflats)

    return Reducted(masterbias, masterdark, masterflats, table_reduced)


def make_masterbias(filenames_bias):
    """

    :param filenames_bias: an astropy Table of bias files
    :return:
    """
    with click.progressbar(length=len(filenames_bias), label='Making Masterbias') as bar:
        for i, filename in enumerate(filenames_bias):
            with fits.open(filename) as hdu:
                data = np.float64(hdu[0].data)
                if i == 0:
                    bias = np.atleast_3d(data)
                else:
                    bias = np.concatenate((bias, np.atleast_3d(data)), axis=2)
                bar.update(1)
    return np.median(bias, axis=2)


def make_masterdark(masterbias, table_darks):
    """

    :param masterbias: and numpy data for masterbias
    :param table_darks: an astropy Table of darks files
    :return:
    """
    if masterbias is None:
        masterbias = 0
    with click.progressbar(length=len(table_darks), label='Making Masterdark') as bar:
        for i, row in enumerate(table_darks):
            with fits.open(row['filename']) as hdu:
                data = np.float64(hdu[0].data)
                data -= masterbias
                data = data / row['exptime']
                if i == 0:
                    darks = np.atleast_3d(data)
                else:
                    darks = np.concatenate((darks, np.atleast_3d(data)), axis=2)
                bar.update(1)
    return np.median(darks, axis=2)


def make_master_flat(table, masterbias, masterdark):
    """
    (Assuming the linearity of the darks over the time)
    :param table: an astropy table with the files
    :param masterbias:
    :param masterdark:
    :return:
    """
    if masterbias is None:
        masterbias = 0
    if masterdark is None:
        masterdark = 1
    with click.progressbar(length=len(table) + 2, label=f'Making MasterFlat (one per filter)') as bar:
        for i, row in enumerate(table):
            with fits.open(row['filename']) as hdu:
                data = np.float64(hdu[0].data)
                masterdark_factor = masterdark * row['exptime']
                if i == 0:
                    flat = np.atleast_3d(data - masterbias - masterdark_factor)
                else:
                    flat = np.concatenate((flat, np.atleast_3d(data - masterbias - masterdark_factor)), axis=2)
                bar.update(1)
        masterflat = np.mean(flat, axis=2)
        median = np.median(masterflat)
        bar.update(2)
        return masterflat / median


def reducing_sci_by_band(table, outdir, masterbias, masterdark, masterflats):
    """
    para cada imagen de la tabla, tengo que hacer:
    1. sci[i] -= masterbias
    2. sci[i] -= masterdark * exptime[i]
    3. sci[i] /= masterflat_{band}
    :param table:
    :return:
    """

    cols = ['filename', 'imagetype', 'band', 'object', 'exptime', 'date_obs',
            'ra', 'dec', 'ra_offset', 'dec_offset','airmass', 'saturated',
            'flag_bias', 'flag_dark', 'flag_flat', 'flag_astr', 'stack']
    sci_list = []
    with click.progressbar(length=len(table[table['imagetype'] == 'light']), label='Reducing science images') as bar:
        for row in table[table['imagetype'] == 'light']:
            with fits.open(row['filename']) as hdu:
                data = np.float64(hdu[0].data)
                band = row['band']

                if masterbias is not None:
                    data -= masterbias

                if masterdark is not None:
                    data -= masterdark * row['exptime']

                if masterflats[band] is not None:
                    data /= masterflats[band]

                image = fits.PrimaryHDU(data)
                #image.header = hdu[0].header Todo

                filename = ntpath.basename(row['filename'])
                filename = path.join(outdir, 'sci_' + filename)
                image.writeto(filename, overwrite=True)

                sci_list.append((
                    filename,
                    'sci',
                    row['band'],
                    row['object'],
                    row['exptime'],
                    row['date_obs'],
                    row['ra'],
                    row['dec'],
                    None,
                    None,
                    row['airmass'],
                    row['saturated'],
                    masterbias is not None,
                    masterdark is not None,
                    masterflats[band] is not None,
                    False,
                    None
                ))
                bar.update(1)
    return Table(
        rows=sci_list,
        names=cols,
        # dtype=('S1', ''), TODO
        meta={'name': 'Ckoirama Pipeline recuded data'}
    )
