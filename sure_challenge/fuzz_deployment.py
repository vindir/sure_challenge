#!/usr/bin/env python3
from optparse import OptionParser
import boto3
import random
import requests
import time
import sys

s3 = boto3.client("s3")
word_site = "https://www.mit.edu/~ecprice/wordlist.10000"
response = requests.get(word_site)
ALL_WORDS = response.content.splitlines()
FUZZ_WORDS = [word for word in ALL_WORDS if len(word) > 5]

SAMPLE_KEYS = [
    "index.html",
    "base.html",
    "root.html",
    "css/font.css",
    "images/hey.png",
    "styles/font.css",
    "img/hey.png",
    "fonts/font.css",
    "png/hey.png",
]


def random_deploy_name():
    base_name = FUZZ_WORDS[random.randint(0, len(FUZZ_WORDS))].decode("utf-8")
    random_int = random.randint(1000, 9999)
    return f"{base_name}_{random_int}"


def create_deployment(bucket, deploy_name):
    for file_name in random.sample(SAMPLE_KEYS, 3):
        s3.put_object(Bucket=bucket, Key=f"{deploy_name}/{file_name}")


def main(args):
    parser = OptionParser()
    parser.add_option(
        "-n",
        "--deploy_count",
        dest="deploy_count",
        type="int",
        default=1,
        help="specify the number of fake deployments to create",
    )
    parser.add_option(
        "-b",
        "--bucket_name",
        dest="bucket_name",
        type="string",
        default="test-bucket",
        help="specify the S3 bucket to manage",
    )

    (options, args) = parser.parse_args()
    if options.bucket_name == None:
        print(parser.usage)
        sys.exit(0)

    for _ in range(options.deploy_count):
        create_deployment(options.bucket_name, random_deploy_name())
        time.sleep(1)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
