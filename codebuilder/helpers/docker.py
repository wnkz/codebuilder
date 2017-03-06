import os

from .aws import AWSHelper

class DockerHelper(AWSHelper):

    def __init__(self, image_name=None, artifact_name=None):
        super(DockerHelper, self).__init__()

        self._image_name = image_name or self.__guess_image_name()
        self._version = self.get_version()
        self._branch = os.getenv('GITHUB_BRANCH', None)
        self._build_id = os.getenv('CODEBUILD_BUILD_ID', None)
        self._revision_id = self.codepipeline_get_artifact_attribute(artifact_name, 'revisionId')
        self._short_revision_id = None
        if self._revision_id:
            self._short_revision_id = self._revision_id[:8]

        self._available_tags = {
            'latest': 'latest'
        }

        if self._version:
            self._available_tags['version'] = self._version

        if self._branch:
            self._available_tags['branch'] = self._branch

        if self._short_revision_id:
            self._available_tags['revision-id'] = self._short_revision_id

        if self._short_revision_id and self._version:
            self._available_tags['full'] = '{}-{}'.format(self._version, self._short_revision_id)

        self._available_images = {}
        if self._image_name:
            for k, v in self._available_tags.items():
                self._available_images[k] = '{}:{}'.format(self._image_name, v)

    def get_image(self, tag):
        return self._available_images.get(tag, None)

    def get_tag(self, tag):
        return self._available_tags.get(tag, None)

    def get_apply_tags_commands(self, tags=[]):
        commands = []
        for tag in tags:
            if tag in self._available_images:
                commands.append(['docker', 'tag', self._image_name, self._available_images[tag]])
        return commands

    def __guess_image_name(self):
        docker_registry = os.getenv('DOCKER_REGISTRY', None)
        image_name = os.getenv('IMAGE_NAME', None)

        if docker_registry and image_name:
            return '{}/{}'.format(docker_registry, image_name)
        return None
