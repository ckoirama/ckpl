import click
import numpy as np
from . import preprocessing
from astropy.io import fits
from astropy.table import Table
import pathlib
from os import path
import ntpath


@click.command()
@click.option('--imdir', prompt='Directory for processed data')
@click.option('--outdir', prompt='Directory for processed data')
def cli(imdir, outdir):

    calib_path = path.join(outdir, 'calib')
    reduced_path = path.join(outdir, 'reduced')

    # https://stackoverflow.com/a/600612
    pathlib.Path(calib_path).mkdir(parents=True, exist_ok=True)
    pathlib.Path(reduced_path).mkdir(parents=True, exist_ok=True)

    table = preprocessing.ls(imdir)

    masterbias, masterdark, masterflats, table_reduced = reduction(imdir, outdir, calib_path, reduced_path, table)

    click.echo(table_reduced)

    return masterbias, masterdark, masterflats, table_reduced


def reduction(imdir, outdir, calib_path, reduced_path, table):
    """

    :param df: pandas.DataFrame
    :return:
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
    #images_flat_by_band = {}
    #for band in bands_flat:
#        images_flat_by_band[band] = table[(table['imagetype'] == 'flat') * (table['band'] == band)]

    masterflats = {
        band: make_master_flat(images_flat, masterbias, masterdark) if masterdark is not None else None
        for band, images_flat in images_flat_by_band.items()
    }

    bands_sci = np.unique(table[table['imagetype'] == 'light']['band'])
    images_sci_by_band = {
        band: table[(table['imagetype'] == 'light') * (table['band'] == band)]
        for band in bands_sci
    }

    table_reduced = reducing_sci_by_band(table, reduced_path, masterbias, masterdark, masterflats)

    fits.PrimaryHDU(masterbias).writeto(path.join(calib_path, 'masterbias.fits'), overwrite=True)
    fits.PrimaryHDU(masterdark).writeto(path.join(calib_path, 'masterdark.fits'), overwrite=True)

    [
        fits.PrimaryHDU(masterflat).writeto(path.join(calib_path, f'masterflat_{band}.fits'), overwrite=True)
        for band, masterflat
        in masterflats.items()
    ]

    return masterbias, masterdark, masterflats, table_reduced


def make_masterbias(filenames_bias):
    for i, filename in enumerate(filenames_bias):
        hdu = fits.open(filename)
        data = np.float64(hdu[0].data)
        if i == 0:
            bias = np.atleast_3d(data)
        else:
            bias = np.concatenate((bias, np.atleast_3d(data)), axis=2)
    return np.median(bias, axis=2)


def make_masterdark(masterbias, table_darks):
    for i, row in enumerate(table_darks):
        hdu = fits.open(row['filename'])
        data = np.float64(hdu[0].data)
        data -= masterbias
        data = data / row['exptime']
        if i == 0:
            darks = np.atleast_3d(data)
        else:
            darks = np.concatenate((darks, np.atleast_3d(data)), axis=2)
    return np.median(darks, axis=2)


def make_master_flat(table, master_bias, masterdark):
    for i, row in enumerate(table):
        hdu = fits.open(row['filename'])
        data = np.float64(hdu[0].data)
        masterdark_factor = masterdark * row['exptime']
        if i == 0:
            flat = np.atleast_3d(data - master_bias - masterdark_factor)
        else:
            flat = np.concatenate((flat, np.atleast_3d(data - master_bias - masterdark_factor)), axis=2)
    masterflat = np.mean(flat, axis=2)
    median = np.median(masterflat)
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
            'ra', 'dec', 'airmass', 'saturated', 'flag_bias', 'flag_dark', 'flag_flat', 'flag_astr', 'stack']
    sci_list = []
    for row in table[table['imagetype'] == 'light']:
        hdu = fits.open(row['filename'])
        data = np.float64(hdu[0].data)
        band = row['band']

        if masterbias is not None:
            data -= masterbias

        if masterdark is not None:
            data -= masterdark * row['exptime']

        if masterflats[band] is not None:
            data /= masterflats[band]

        image = fits.PrimaryHDU(data)
        image.header = hdu[0].header

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
            row['airmass'],
            row['saturated'],
            masterbias is not None,
            masterdark is not None,
            masterflats[band] is not None,
            None,
            None
        ))
    return Table(
        rows=sci_list,
        names=cols,
        # dtype=('S1', ''), TODO
        meta={'name': 'Ckoirama Pipeline recuded data'}
    )
