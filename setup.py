from setuptools import setup, find_packages

from codebuilder import __version__

setup(
    name='codebuilder',
    version=__version__,
    description='CLI helper for AWS CodeBuild and CodePipeline',
    url='http://github.com/wnkz/codebuilder',
    author='wnkz',
    author_email='g@predicsis.ai',
    license='MIT',
    packages=find_packages(),
    zip_safe=False,
    install_requires = [
        'Click',
        'boto3',
        'dpath'
    ],
    entry_points = {
        'console_scripts': [
            'codebuilder=codebuilder.cli:cli',
        ],
    },
)
