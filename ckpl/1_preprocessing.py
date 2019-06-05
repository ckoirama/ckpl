import os
import pandas as pd
import astropy.io.fits as fits
from tkinter import Tk, filedialog

def lst(im_dir):
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

    #List for objects, to convert later to a data frame
    
    cols = ['File Name', 'IMAGETYP', 'FILTER', 'OBJECT', 'EXPTIME', 'DATE-OBS']
    os.chdir(im_dir)
    files_list = os.listdir()
    objs = []
    
    for file in files_list:        
        hdu = fits.open(file)
        header = hdu[0].header
        #parameter we want to list for our pipeline
        obj = header['OBJECT']
        exp_t = header['EXPTIME']
        date = header['DATE-OBS']
        im_type = header['IMAGETYP']
        
        if 'FILTER' in header:
            filt = header['FILTER']
        else:
            filt = 'N.A'

        objs.append([file,im_type,filt,obj,str(exp_t),date])
        hdu.close(file)

    df = pd.DataFrame(objs, columns = cols)

    return(df)

def lst_gui():
    # Dialog window to look for the directory path through GUI
    root = Tk()
    root.withdraw() #use to hide tkinter window

    cwd = os.getcwd()
    im_dir = filedialog.askdirectory(\
                                       parent=root, initialdir=cwd,\
                                       title='Please select images\' directory')
    
    return(lst(im_dir))