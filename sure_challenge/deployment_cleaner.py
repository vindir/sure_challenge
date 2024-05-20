#!/usr/bin/env python3
import logging
import boto3
import sys
import os


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

s3 = boto3.resource("s3")


def get_timestamped_deployments(bucket):
    timestamped_deployments = []
    bucket_objets = bucket.meta.client.list_objects(Bucket=bucket.name, Delimiter="/")

    for o in bucket_objets.get("CommonPrefixes"):
        prefix = o.get("Prefix")

        # Grab a single key object from each deployment prefix to act as a
        # representative for retrieving timestamp information.
        deployment_object = next(iter(bucket.objects.filter(Prefix=prefix)))
        timestamped_deployments.append(
            (prefix, deployment_object.key, deployment_object.last_modified)
        )
    return timestamped_deployments


def deployments_by_age(timestamped_deployments, deployment_retention):
    timestamped_deployments.sort(key=lambda x: x[2], reverse=True)
    for deployment in timestamped_deployments[deployment_retention:]:
        logger.info(f"Removing out of date deployment {deployment[0]}")
        yield deployment


def delete_by_prefix(bucket, deployment):
    try:
        bucket.objects.filter(Prefix=deployment[0]).delete()
    except Exception as err:
        logger.error(f"Removing out of date deployment: {err=}")
        print(f"Unexpected {err=}")
        raise


def main(args):
    try:
        deployment_retention = int(os.environ["DEPLOYMENT_RETENTION"])
        deployment_bucket = os.environ["DEPLOYMENT_BUCKET"]
    except:
        sys.exit("Must set environment vars DEPLOYMENT_RETENTION and DEPLOYMENT_BUCKET")

    bucket = s3.Bucket(deployment_bucket)

    timestamped_deployments = get_timestamped_deployments(bucket)

    for deployment in deployments_by_age(timestamped_deployments, deployment_retention):
        delete_by_prefix(bucket, deployment)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
