import argparse
import inspect


def process_arguments(declared_args, doc):
    parser = argparse.ArgumentParser(description=doc)

    # TODO -- put arguments that belong to *all* commands here.
    #parser.add_argument(
    #    dest='topic',
    #    metavar="TOPIC",
    #    help="org.fedoraproject.logger.TOPIC",
    #)

    for args, kwargs in declared_args:
        parser.add_argument(*args, **kwargs)

    args = parser.parse_args()
    return args
