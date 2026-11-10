import os.path

try:
    from pkg_resources import resource_filename
except ImportError:  # setuptools fara pkg_resources
    resource_filename = None


def get_resource(filename):
    if resource_filename is not None:
        return resource_filename(__package__, os.path.join('data', filename))
    return os.path.join(os.path.dirname(__file__), 'data', filename)
