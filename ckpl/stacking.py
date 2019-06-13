from reproject import reproject_interp
from astropy.io import fits
import numpy as np


def align(table_sci):
    table_sci = table_sci[table_sci['flag_ast']]
    stack_ids = np.unique(np.array(table_sci[table_sci['stack'] is not None]['stack']))
    for stack_id in stack_ids:
        table_sci_stack = table_sci[table_sci['stack'] == stack_id]
        reference_row = table_sci_stack[0]
        for i in range(1, len(table_sci_stack)):
            data, footprint = reproject_interp(table_sci_stack[i]['filename'], reference_row['filename'])
            image = fits.PrimaryHDU(data)
            image.writeto(table_sci_stack[i]['filename'] + f'.{stack_id}.fit')


def stack(table_sci):
    table_sci = table_sci[table_sci['flag_ast']]
    stack_ids = np.unique(np.array(table_sci[table_sci['stack'] is not None]['stack']))
    for stack_id in stack_ids:
        table_sci_stack = table_sci[table_sci['stack'] == stack_id]
        reference_row = table_sci_stack[0]
        for i, row in enumerate(table_sci_stack):
            hdu = fits.open(row['filename'])
            data = np.float64(hdu[0].data)
            if i == 0:
                frame = np.atleast_3d(data)
            else:
                frame = np.concatenate((frame, np.atleast_3d(data)), axis=2)
        # todo make this more robust
        fits.PrimaryHDU(np.median(frame, axis=2)).writeto(reference_row['filename'] + '.stacked.fit')
