CodeBuilder - CLI helper for easy CI on AWS
===========================================

|Build Status| |Version|

CodeBuilder is a CLI tool which allows developpers to use simple commands
and helpers inside AWS CI/CD tools like CodePipeline and CodeBuild.

.. |Version| image:: https://img.shields.io/pypi/v/codebuilder.svg?style=flat
    :target: https://pypi.python.org/pypi/codebuilder/
    :alt: Version

.. |Build Status| image:: https://img.shields.io/travis/wnkz/codebuilder/master.svg?style=flat
    :target: https://travis-ci.org/wnkz/codebuilder
    :alt: Build Status

Quick Start
-----------

Generally, you would run CodeBuilder on an `AWS CodeBuild environment <https://docs.aws.amazon.com/codebuild/latest/userguide/build-env-ref.html>`__
where AWS CLI is properly installed and configured. CodeBuilder uses the exact same authentication method as Boto 3 and AWS CLI.

Install with ``pip``:

.. code-block:: sh

    $ pip install codebuilder

Example CodeBuild usage (``buildspec.yml``):

.. code-block:: yaml

    version: 0.1
    environment_variables:
      plaintext:
        KMS_CIPHERBLOB: "AQEC..."

    phases:
      install:
        commands:
          - pip install codebuilder
      pre_build:
        commands:
          - codebuilder aws ecr login
          - codebuilder aws kms decrypt ${KMS_CIPHERBLOB} > ${CODEBUILD_SRC_DIR}/secret
      build:
        commands:
          - docker build -t 123456789012.dkr.ecr.eu-west-1.amazonaws.com/foo .
      post_build:
        commands:
          - docker push 123456789012.dkr.ecr.eu-west-1.amazonaws.com/foo
          - codebuilder docker --image-name 123456789012.dkr.ecr.eu-west-1.amazonaws.com/foo get-image full --source-json-file config.json --in-place Parameters DockerImage
          - codebuilder aws ecr prune
