import subprocess
import click

@click.command()
@click.option('--blind', default=False, help='Blind Astrometry?')
def astrometry(file, blind):
    """
    This function run astrometry.net software to perform blind astrometry.
    :param file:
    :param blind:
    :return:
    """
    options = " --tweak-order 3 --downsample 2 --overwrite --no-plots --cpu-limit 30"
    coords = ""
    scale = " --scale-units arcsecperpix --scale-low 0.46 --scale-high 0.47 "
    image = file
    if not blind:
        coords = "--ra 14:09:35 --dec -38:46:12 --radius 0.5"

    try:
        command = "solve-field " + options + coords + scale + image
        subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, shell=True)
    except:
        print("Astrometry.net failed")

    pass

