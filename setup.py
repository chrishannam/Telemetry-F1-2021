import setuptools
import telemetry_f1_2021

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='Telemetry-F1-2021',
    version=telemetry_f1_2021.__version__,
    author='Chris Hannam',
    author_email='ch@chrishannam.co.uk',
    description='Decode F1 2021 telemetry data.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/chrishannam/Telemetry-F1-2021',
    packages=setuptools.find_packages(exclude=('tests', 'examples')),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    entry_points={
        'console_scripts': [
            'telemetry-f1-2021-recorder=telemetry_f1_2021.main:main',
            'telemetry-f1-2021-update-packets=telemetry_f1_2021.main:save_packets',
        ]
    },
    include_package_data=True,
    python_requires='>=3.6',
)
