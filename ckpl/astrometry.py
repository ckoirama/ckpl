import subprocess
from . import reduction
import click
import numpy as np

@click.command()
@click.option('--imdir', prompt='Directory for processed data')
@click.option('--outdir', prompt='Directory for processed data')
@click.option('--blind', default=False, is_flag=True, help='Blind Astrometry?')
def cli(imdir, outdir, blind):

    print(f"blind? {blind}")
    table = reduction.cli(imdir, outdir).table
    table = table[table['imagetype' == 'light']]
    do_astrometry(table, blind)


def do_astrometry(table_sci, blind):
    """
    This function run astrometry.net software to perform blind astrometry.
    :param file:
    :param blind:
    :return:
    """
    options = "--tweak-order 3 --downsample 2 --overwrite --no-plots --cpu-limit 30 "
    options += "--new-fits none --axy none --corr none --match none --rlds none --solved none"
    options += "--index-xyls none"
    coords = ""
    scale = "--scale-units arcsecperpix --scale-low 0.46 --scale-high 0.47 "

    for i, row in enumerate(table_sci):
        imname = row['filename']

        if not blind:
            ra = str(row['ra']).replace(' ', ':')
            dec = str(row['dec']).replace(' ', ':')
            coords = f"--ra {ra} --dec {dec} --radius 0.5 "


        try:
            command = "solve-field " + options + coords + scale + imname
            subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, shell=True)
        except:
            print("Astrometry.net failed")
