import os
from setuptools import setup, find_packages
from setuptools.extension import Extension
from Cython.Build import cythonize


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


extensions = [
    Extension("modules.pseudonymize.filter.doublehash",
              ["modules/pseudonymize/filter/doublehash.pyx"])
]

setup(
    name="abbo_tools",

    version="0.3.3",

    author="Daniel Arp, Alwin Maier",
    author_email="d.arp@tu-bs.de, alwin.maier@tu-bs.de",

    description="The ABBO Toolbox",
    license="GPLv3",

    packages=find_packages(exclude=['tests']),
    package_data={'modules': ['generate/data/*.csv', 'predict/data/toy.model']},
    test_suite='tests',
    include_package_data=True,

    scripts=['abbo_cli.py'],
    entry_points={
        'console_scripts': [
            'abbo_cli = abbo_cli:main_func'
        ],
    },

    install_requires=[
        'numpy == 1.13.3',
        'scipy == 1.0.0',
        'scikit-learn == 0.18.1',
        'simplejson == 3.8.2',
        'mmh3 == 2.3.1',
        'bitarray == 0.8.1',
        'progressbar == 2.3'
    ],
    ext_modules=cythonize(extensions)
)
