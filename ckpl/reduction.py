import click
import numpy as np
from . import preprocessing
from astropy.io import fits
import pathlib
from os import path


@click.command()
@click.option('--imdir', prompt='Directory for processed data')
@click.option('--outdir', prompt='Directory for processed data')
def cli(imdir, outdir):

    calib_path = path.join(outdir, 'calib')
    reduced_path = path.join(outdir, 'reduced')

    # https://stackoverflow.com/a/600612
    pathlib.Path(calib_path).mkdir(parents=True, exist_ok=True)
    pathlib.Path(reduced_path).mkdir(parents=True, exist_ok=True)

    masterbias, masterdark, masterflats = reduct(preprocessing.ls(imdir))

    fits.PrimaryHDU(masterbias).writeto(path.join(calib_path, 'masterbias.fits'), overwrite=True)
    fits.PrimaryHDU(masterdark).writeto(path.join(calib_path, 'masterdark.fits'), overwrite=True)

    [
        fits.PrimaryHDU(masterflat).writeto(path.join(calib_path, f'masterflat_{band}.fits'), overwrite=True)
        for band, masterflat
        in masterflats.items()
    ]


def reduct(table):
    """

    :param df: pandas.DataFrame
    :return:
    """

    filenames_bias = np.array(table[table['imagetype'] == 'bias']['filename'])
    masterbias = make_masterbias(filenames_bias)

    table_darks = table[table['imagetype'] == 'dark']
    masterdark = make_masterdark(masterbias, table_darks)

    bands = np.unique(table[table['imagetype'] == 'flat']['band'])

    print(bands)

    #images_flat_by_band = {
    #    band: table[table['imagetype'] == 'flat' and table['band'] == band]
    #    for band in bands
    #}
    images_flat_by_band = {}
    for band in bands:
        images_flat_by_band[band] = table[(table['imagetype'] == 'flat') * (table['band'] == band)]

    print('images_flat_by_band', images_flat_by_band)

    masterflats = {
        band: make_master_flat(images_flat, masterbias, masterdark)
        for band, images_flat in images_flat_by_band.items()
    }

    print(masterflats)

    return masterbias, masterdark, masterflats


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
        print('|', end='')
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
        print('|', end='')
    masterflat = np.mean(flat, axis=2)
    median = np.median(masterflat)
    return masterflat / median


