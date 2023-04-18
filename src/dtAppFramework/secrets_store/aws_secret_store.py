from .secret_store import AbstractSecretStore, SecretsStoreException
from shutil import which
from ..misc import run_cmd

import boto3
import logging


class AWSSecretsStore(AbstractSecretStore):

    def __init__(self, store_priority, aws_settings) -> None:
        super().__init__("AWS_Secrets_Store", store_priority)
        if not which("aws"):
            raise SecretsStoreException("AWS Secrets Store requires the AWS Command Line Utility to be installed.")
        self.aws_profile = aws_settings.get('aws_profile', None)
        self.aws_sso = aws_settings.get('aws_sso', False)

        if not self.aws_profile:
            raise SecretsStoreException("AWS Secrets Store requires a valid profile to be provided.")

        if self.aws_sso:
            aws_sso_resp = run_cmd(f'aws sso login --profile {self.aws_profile}')
            if not aws_sso_resp or "Successfully logged into Start URL" not in aws_sso_resp:
                raise SecretsStoreException(f"Unable to initialise SSO for the AWS profile {self.aws_profile}.")

        self.aws_session = boto3.session.Session(profile_name=self.aws_profile)
        self.aws_secretsmanager = self.aws_session.client('secretsmanager')
        try:
            self.aws_secretsmanager.list_secrets()
        except Exception as ex:
            raise SecretsStoreException(f'AWS Secrets Store, Not Available. Error: {str(ex)}')

    def get_secret(self, key, default_value=None):
        try:
            entry = self.aws_secretsmanager.get_secret_value(SecretId=key)['SecretString']
        except Exception as ex:
            logging.error(str(ex))
            entry = None

        if not entry:
            entry = default_value

        return entry

    def set_secret(self, key, value):
        try:
            resp = self.aws_secretsmanager.create_secret(Name=key, SecretString=value, ForceOverwriteReplicaSecret=True)
            if "Name" not in resp:
                raise SecretsStoreException(f'Inconsistent response from AWS: {str(resp)}')
        except Exception as ex:
            logging.error(str(ex))
            raise SecretsStoreException(str(ex))

    def delete_secret(self, key):
        try:
            resp = self.aws_secretsmanager.delete_secret(SecretId=key, ForceDeleteWithoutRecovery=True)
            if "Name" not in resp:
                raise SecretsStoreException(f'Inconsistent response from AWS: {str(resp)}')
        except Exception as ex:
            logging.error(str(ex))
            raise SecretsStoreException(str(ex))
