from importlib import import_module

preprocessing = import_module('ckpl.1_preprocessing')
reduction = import_module('ckpl.2_reduction')


def main():

    ctx = {}

    preprocessing.run(ctx)
    reduction.run(ctx)
