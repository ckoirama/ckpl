import click
import astropy.io.fits as fits
from glob import glob
from os import path
from astropy.table import Table
from astropy.io import ascii


@click.command()
@click.argument(
    'imdir',
    default='.',
    type=click.Path(exists=True, dir_okay=True, readable=True, resolve_path=True))
@click.option(
    '-o',
    '--output',
    type=click.Path(exists=False, file_okay=True, writable=True, resolve_path=True),
    default='raw.dat',
    help='The name of the file to save the table')
@click.option(
    '-v',
    '--verbose',
    is_flag=True)
@click.option('--nosave', is_flag=True)
def cli(imdir, output=None, verbose=None, nosave=None):
    table = ls(imdir)
    if not nosave:
        ascii.write(table, output, overwrite=True, format='ecsv')

    if verbose:
        click.echo(str(table))


def ls(dir):
    """
    In this stage the idea is mainly identify the image: science, calibration
    (bias, flat, dark), filter (r, g, i, L), exposure time, date, etc.
    Also check for the quality of the data (is not saturated, etc..) and then
    classify it. Also the header info can be stored in the data base.
    :param ctx:
        .indata: a directory with the incoming data
        .outdata: a directory with the outcoming data
    :return:
    """
    cols = ['filename', 'imagetype', 'band', 'object', 'exptime', 'date_obs',
            'ra', 'dec', 'airmass', 'saturated']
    files_list = glob(path.join(dir, '*.fit'))

    rows = []
    for file in files_list:        
        hdu = fits.open(file)
        header = hdu[0].header
        obj = header['OBJECT']
        exp_t = header['EXPTIME']
        date = header['DATE-OBS']
        im_type = header['IMAGETYP']

        im_type = im_type.lower().replace(' frame', '').replace(' field', '')

        band = header['FILTER'].replace("'", '').lower() if 'FILTER' in header else ''
        airmass = header['AIRMASS'] if 'AIRMASS' in header else ''
        ra = header['OBJCTRA'] if 'OBJCTRA' in header else ''
        dec = header['OBJCTDEC'] if 'OBJCTDEC' in header else ''

        rows.append((file, im_type, band, obj, exp_t, date, ra, dec, airmass, check_saturation(hdu)))
        hdu.close(file)

    if len(rows) == 0:
        raise Exception(f'{dir} do not contains .fit files :c')

    return Table(
        rows=rows,
        names=cols,
        #dtype=('S1', ''), TODO
        meta={'name': 'List of file to be processed by the Ckoirama Pipeline'}
    )


def check_saturation(hdu):
    """TODO"""
    return None
