from distutils.core import setup

setup(
    name='Footballmetrics',
    version='1.0dev',
    author='Andy Goldschmidt',
    author_email='andygoldschmidt@me.com',
    packages=['footballmetrics'],
    url='http://www.footballissexbaby.de',
    license='GPL',
    description='A package for statistical analysis of football data.',
    long_description=open('README').read(),
    install_requires=[
        "numpy >= 1.6.0",
        "scipy >= 0.10.0",
        "html5lib >= 0.95",
    ],
)