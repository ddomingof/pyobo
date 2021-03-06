# -*- coding: utf-8 -*-

"""Interface for caching data on AWS S3."""

import logging
import os
from typing import Optional

import boto3
import click
import humanize
from tabulate import tabulate

from pyobo.cli_utils import verbose_option
from pyobo.constants import PYOBO_HOME
from pyobo.extract import (
    get_id_name_mapping, get_id_synonyms_mapping, get_properties_df, get_relations_df,
    get_xrefs_df,
    iter_cached_obo,
)
from pyobo.path_utils import prefix_directory_join

__all__ = [
    'download_artifacts',
    'upload_artifacts',
    'upload_artifacts_for_prefix',
    'list_artifacts',
    'aws',
]

logger = logging.getLogger(__name__)


def download_artifacts(bucket: str, suffix: Optional[str] = None) -> None:
    """Download compiled parts from AWS.

    :param bucket: The name of the S3 bucket to download
    :param suffix: If specified, only download files with this suffix. Might
     be useful to specify ``suffix='names.tsv`` if you just want to run the
     name resolution service.
    """
    s3_client = boto3.client('s3')
    all_objects = s3_client.list_objects(Bucket=bucket)
    for entry in all_objects['Contents']:
        key = entry['Key']
        if suffix and not key.endswith(suffix):
            pass
        path = os.path.join(PYOBO_HOME, key)
        if os.path.exists(path):
            continue  # no need to download again
        logging.info('downloading %s to %s', key, path)
        s3_client.download_file(bucket, key, path)


def upload_artifacts(bucket: str) -> None:
    """Upload all artifacts to AWS."""
    s3_client = boto3.client('s3')
    all_objects = s3_client.list_objects(Bucket=bucket)
    uploaded_prefixes = {
        entry['Key'].split('/')[0]
        for entry in all_objects['Contents']
    }

    for prefix, _ in sorted(iter_cached_obo()):
        if prefix in uploaded_prefixes:
            continue
        upload_artifacts_for_prefix(prefix=prefix, bucket=bucket)


def upload_artifacts_for_prefix(*, prefix: str, bucket: str):
    """Upload compiled parts for the given prefix to AWS."""
    logger.info('[%s] getting id->name mapping', prefix)
    get_id_name_mapping(prefix)
    id_name_path = prefix_directory_join(prefix, 'cache', 'names.tsv')
    id_name_key = os.path.join(prefix, 'cache', 'names.tsv')
    logger.info('[%s] uploading id->name mapping', prefix)
    upload_file(path=id_name_path, bucket=bucket, key=id_name_key)

    logger.info('[%s] getting id->synonyms mapping', prefix)
    get_id_synonyms_mapping(prefix)
    id_synonyms_path = prefix_directory_join(prefix, 'cache', 'synonyms.tsv')
    id_synonyms_key = os.path.join(prefix, 'cache', 'synonyms.tsv')
    logger.info('[%s] uploading id->synonyms mapping', prefix)
    upload_file(path=id_synonyms_path, bucket=bucket, key=id_synonyms_key)

    logger.info('[%s] getting xrefs', prefix)
    get_xrefs_df(prefix)
    xrefs_path = prefix_directory_join(prefix, 'cache', 'xrefs.tsv')
    xrefs_key = os.path.join(prefix, 'cache', 'xrefs.tsv')
    logger.info('[%s] uploading xrefs', prefix)
    upload_file(path=xrefs_path, bucket=bucket, key=xrefs_key)

    logger.info('[%s] getting relations', prefix)
    get_relations_df(prefix)
    relations_path = prefix_directory_join(prefix, 'cache', 'relations.tsv')
    relations_key = os.path.join(prefix, 'cache', 'relations.tsv')
    logger.info('[%s] uploading relations', prefix)
    upload_file(path=relations_path, bucket=bucket, key=relations_key)

    logger.info('[%s] getting properties', prefix)
    get_properties_df(prefix)
    properties_path = prefix_directory_join(prefix, 'cache', 'properties.tsv')
    properties_key = os.path.join(prefix, 'cache', 'properties.tsv')
    logger.info('[%s] uploading properties', prefix)
    upload_file(path=properties_path, bucket=bucket, key=properties_key)


def upload_file(*, path, bucket, key):
    """Upload a file to an S3 bucket.

    :param path: The local file path
    :param bucket: The name of the S3 bucket
    :param key: The relative file path to put on the S3 bucket
    """
    s3_client = boto3.client('s3')
    s3_client.upload_file(path, bucket, key)


def list_artifacts(bucket: str) -> None:
    """List the files in a given bucket."""
    s3_client = boto3.client('s3')
    all_objects = s3_client.list_objects(Bucket=bucket)
    rows = [
        (entry['Key'], humanize.naturalsize(entry['Size']))
        for entry in all_objects['Contents']
    ]
    print(tabulate(rows, headers=['File', 'Size']))


bucket_argument = click.argument('bucket')


@click.group()
def aws():
    """CLI for storing OBO artifacts on S3."""


@aws.command()
@bucket_argument
@verbose_option
def download(bucket):
    """Download all artifacts from the S3 bucket."""
    download_artifacts(bucket)


@aws.command()
@bucket_argument
@verbose_option
def upload(bucket):
    """Download all artifacts from the S3 bucket."""
    upload_artifacts(bucket)


@aws.command()
@bucket_argument
@verbose_option
def ls(bucket):
    """List all artifacts on the S3 bucket."""
    list_artifacts(bucket)


if __name__ == '__main__':
    aws()
