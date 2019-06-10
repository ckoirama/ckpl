import click
import numpy as np
from astropy.io import fits
from astropy.stats import sigma_clip

@click.command()
@click.option('--science', prompt='Science images')
def cli(science):
    click.echo(science)
    reduct()


def reduct(df):
    """

    :param df: pandas.DataFrame
    :return:
    """

    filenames_bias = df[df.IMAGETYP == 'BIAS']['File Name'].values
    masterbias = make_masterbias(filenames_bias)

    filters = np.unique(df[df.IMAGETYP == 'FLAT']['FILTER'].values)

    filenames_flat_by_filter = {
        filter: df[df.IMAGETYP == 'FLAT' and df.FITER == filter_].values
        for filter_ in filters
    }

    masterflats = [
        make_master_flat(filenames_flat, masterbias)
        for filenames_flat in filenames_flat_by_filter
    ]

    return masterbias, masterflats


def make_masterbias(filenames_bias):
    for i, filename in enumerate(filenames_bias):
        hdu = fits.open(filename)
        data = np.float32(hdu[0].data)
        if i == 0:
            bias = np.atleast_3d(data)
        else:
            bias = np.concatenate((bias, np.atleast_3d(data)), axis=2)
    return np.mean(bias, axis=2)


def make_master_flat(filenames_flat, master_bias):
    for i, filename in enumerate(filenames_flat):
        hdu = fits.open(filename)
        data = np.float32(hdu[0].data)
        if i == 0:
            flat = np.atleast_3d(data - master_bias)
        else:
            flat = np.concatenate((flat, np.atleast_3d(data - master_bias)),axis=2)
    masterflat = np.mean(flat, axis=2)
    median = np.median(masterflat)
    return masterflat / median


