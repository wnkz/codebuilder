from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

from codebuilder import __version__

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='codebuilder',

    version=__version__,

    description='CLI helper for AWS CodeBuild and CodePipeline',
    long_description=long_description,

    url='http://github.com/wnkz/codebuilder',
    download_url='https://github.com/wnkz/codebuilder/archive/{}.tar.gz'.format(__version__),

    author='wnkz',
    author_email='wnkz@users.noreply.github.com',

    license='MIT',

    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',

        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],

    keywords='aws codebuild codepipeline docker kms',

    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    package_data={
        'codebuilder': [
            'codebuilder-complete.sh'
        ]
    },
    include_package_data=True,

    install_requires=[
        'click==6.7',
        'botocore>=1.5.0,<1.6.0',
        'boto3>=1.4.4',
        'dpath==1.4'
    ],

    entry_points={
        'console_scripts': [
            'codebuilder=codebuilder.cli:cli',
        ],
    },

    setup_requires=[
        'pytest-runner'
    ],

    tests_require=[
        'pytest'
    ],

    zip_safe=False
)
