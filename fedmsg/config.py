import argparse
import inspect

def get_calling_docstring(n=1):
    """ Print the docstring of the calling function """
    frame = inspect.stack()[n][0]
    #return frame.f_globals[frame.f_code.co_name].__doc__
    return "docstring inspection doesn't work with decorator yet."


def process_arguments(declared_args):
    parser = argparse.ArgumentParser(description=get_calling_docstring(2))

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
