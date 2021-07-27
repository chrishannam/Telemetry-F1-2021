import setuptools
import telemetry_f1_2021

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='telemetry_f1_2021',
    version=telemetry_f1_2021.__version__,
    author='Chris Hannam',
    author_email='ch@chrishannam.co.uk',
    description='Decode F1 2021 telemetry data.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/chrishannam/telemetry_f1_2021',
    packages=setuptools.find_packages(exclude=('tests', 'examples')),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    include_package_data=True
)
