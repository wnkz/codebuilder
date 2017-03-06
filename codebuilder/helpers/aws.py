import os
import click
import boto3
import botocore
import dpath.util

import botocore.vendored.requests.packages.urllib3 as urllib3
urllib3.disable_warnings(urllib3.exceptions.SecurityWarning)

from base64 import b64decode

from .base import BaseHelper


# TODO: Better permissions checking
class AWSHelper(BaseHelper):

    def __init__(self):
        self._session = boto3.session.Session()

    def codepipeline_get_artifacts_revision(self):
        CODEBUILD_BUILD_ID = os.getenv('CODEBUILD_BUILD_ID')
        CODEBUILD_INITIATOR = os.getenv('CODEBUILD_INITIATOR')

        if not CODEBUILD_BUILD_ID or not CODEBUILD_INITIATOR:
            return None

        (service, pipeline_name) = CODEBUILD_INITIATOR.split('/')
        client = self._session.client('codepipeline')
        response = client.get_pipeline_state(name=pipeline_name)

        pipeline_execution_id = None
        for stage_state in response['stageStates']:
            if CODEBUILD_BUILD_ID in dpath.util.values(stage_state, '/actionStates/*/latestExecution/externalExecutionId'):
                pipeline_execution_id = stage_state['latestExecution']['pipelineExecutionId']
                break

        if not pipeline_execution_id:
            return None

        response = client.get_pipeline_execution(
            pipelineName=pipeline_name,
            pipelineExecutionId=pipeline_execution_id
        )

        return response['pipelineExecution']['artifactRevisions']

    def codepipeline_get_artifact_attribute(self, name, attribute):
        artifacts = self.codepipeline_get_artifacts_revision()
        if not artifacts:
            return None
        if not name:
            return artifacts[0].get(attribute, None)
        else:
            for artifact in artifacts:
                if name == artifact['name']:
                    return artifact.get(attribute, None)
        return None

    def ecr_get_authorization(self):
        client = self._session.client('ecr')
        response = client.get_authorization_token()
        user, token = b64decode(response['authorizationData'][0]['authorizationToken']).split(':')
        return (user, token, response['authorizationData'][0]['proxyEndpoint'])

    def ecr_prune(self, repository_name):
        client = self._session.client('ecr')
        response = client.list_images(
            repositoryName=repository_name,
            filter={
                'tagStatus': 'UNTAGGED'
            }
        )
        images_to_delete = response['imageIds']
        if images_to_delete:
            response = client.batch_delete_image(
                repositoryName=repository_name,
                imageIds=images_to_delete
            )
            return response['imageIds']
        return []

    def kms_decrypt(self, blob):
        return self._session.client('kms').decrypt(CiphertextBlob=b64decode(blob))['Plaintext']
