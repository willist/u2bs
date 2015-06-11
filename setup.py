try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='u2bs',
    version="0.0.2",
    py_modules=['u2bs'],
    tests_require=[
        'nose>=1.0',
        'coverage',
    ],
)
