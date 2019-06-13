import subprocess
from . import reduction
import click
import numpy as np
from os import path
import pathlib
from . import preprocessing
from astropy.io import fits
import os



@click.command()
@click.option('--imdir', prompt='Directory for processed data')
@click.option('--outdir', prompt='Directory for processed data')
@click.option('--blind', default=False, is_flag=True, help='Blind Astrometry?')
def cli(imdir, outdir, blind):

    calib_path = path.join(outdir, 'calib')
    reduced_path = path.join(outdir, 'reduced')
    ast_path = path.join(outdir, 'ast')

    # https://stackoverflow.com/a/600612
    pathlib.Path(calib_path).mkdir(parents=True, exist_ok=True)
    pathlib.Path(reduced_path).mkdir(parents=True, exist_ok=True)
    pathlib.Path(ast_path).mkdir(parents=True, exist_ok=True)

    table = preprocessing.ls(imdir)

    masterbias, masterdark, masterflats, table_reduced = reduction.reduction(imdir, outdir, calib_path, reduced_path, table)

    click.echo(table_reduced)

    print(f"blind? {blind}")

    # table_sci = table[table['imagetype' == 'light']]
    do_astrometry(table_reduced, blind, ast_path)


def do_astrometry(table_sci, blind, ast_path, rdls=False):
    """
    This function run astrometry.net software to perform blind astrometry.
    :param file:
    :param blind:
    :return:
    """

    # options = {
    #     'tweak-order': 3,
    #     'downsample': 2
    # }
    #
    # if rdls is False:
    #     options['rdls'] = 'none'
    #
    # options_str = [f'--{key} {val}' for key, val in options].join(' ')

    options = "--tweak-order 3 --downsample 2 --overwrite --no-plots --cpulimit 30 "
    dir = f"--dir {ast_path} "
    print(dir)
    #outfiles = "--axy none --corr none --solved none --match none --rdls none --index-xyls none --wcs none "
    outfiles = "--axy none --corr none --match none --rdls none --index-xyls none --wcs none "
    # outfiles += "--new-fits none"
    coords = ""
    scale = "--scale-units arcsecperpix --scale-low 0.46 --scale-high 0.47 "


    for i, row in enumerate(table_sci):
        imname = row['filename']

        if not blind:
            ra = str(row['ra']).replace(' ', ':')
            dec = str(row['dec']).replace(' ', ':')
            coords = f"--ra {ra} --dec {dec} --radius 0.5 "
            print(f"coords: {coords}")


        try:
            command = "solve-field " + options + outfiles + coords + scale + dir + imname
            subprocess.call(command, shell=True)
            #subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, shell=True)


        except Exception as err:
            print("Astrometry.net failed", err)

