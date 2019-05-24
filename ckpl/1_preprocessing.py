
def run(ctx):
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
    print("sin manos!")