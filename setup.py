from setuptools import setup, find_packages, Extension

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='elab',
    version="1.0.0",
    license='GPL3',
    author='Michael Pence',
    author_email='mapence2@illinois.edu',
    description='Open source lab automation control for electrochemical experiments',
    packages=find_packages('src'),
    package_dir={'':'src'},
    keywords='Electrochemistry',
    python_requires=">=3.6",
    install_requires=[
        'numpy',
        'pandas',
        'pyserial',
        'scipy',
        'scikit-learn'
    ],
)