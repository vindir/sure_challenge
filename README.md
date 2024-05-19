# Challenge: Pruning Deployments from S3

<!-- TOC start (generated with https://github.com/derlin/bitdowntoc) -->

- [Challenge Notes](#challenge-notes)
   * [Task Definition](#task-definition)
   * [Considerations and Assumptions](#considerations-and-assumptions)
      + [Considerations](#considerations)
      + [Assumptions](#assumptions)
   * [Challenge Questions and Answers](#challenge-questions-and-answers)
- [Usage Guide](#usage-guide)
   * [Prerequisites](#prerequisites)
   * [Local Test Walkthrough](#local-test-walkthrough)
   * [Remote Deployment](#remote-deployment)

<!-- TOC end -->

<!-- TOC --><a name="challenge-notes"></a>
## Challenge Notes

<!-- TOC --><a name="task-definition"></a>
### Task Definition
As a member of the Infrastructure team, I want to cleanup old deployment folders in s3 to help manage AWS costs.

Write a script to remove all but the most recent X deployments. The script should take in X as a parameter.

If a deployment is older than X deployments, we will delete the entire folder.

S3 folder bucket assets will look similar to below:
```
s3-bucket-name
    deployhash112/index.html
        /css/font.css
        /images/hey.png 
    dsfsfsl9074/root.html
        /styles/font.css
        /img/hey.png 
    delkjlkploy3/base.html
        /fonts/font.css
        /png/hey.png 
    dsfff1234321/...
    klljkjkl123/...
```

<!-- TOC --><a name="considerations-and-assumptions"></a>
### Considerations and Assumptions

<!-- TOC --><a name="considerations"></a>
#### Considerations
* This solution is less than ideal for real world use
  * Our time cost and value would probably be better served using something else
    * Something like using [S3Cleaner](https://github.com/jordansissel/s3cleaner) by Jordan Sissel of fpm fame.
    * Even better, just set up [bucket lifecycle configurations](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)
* S3 buckets don't naturally have a folder hierarchy
  * Need to be careful when parsing the object listings.
  * Example bucket layout implies we'll use each key up to the first `/` as our *"deployment identifer"* prefix
* Timestamps aren't well preserved in S3
  * There isn't a create time tracked in s3 objects. Modified time is the best we have available by default
  * Timestamps aren't preserved when syncing or creating bucket objects
  * Timestamps can't be explicitly set via the api
* A naming style to prefix would simplify identification of deployments 
  * A naming style could could easily include a creation timestamp in the key for easy reference
* Sample bucket definition doesn't outline any metadata associated
  * date_created metadata would allow finer control over managing order of deployment removal
  * A small lambda triggered on object creation could be used to automatically set the date_created metadata
    * Sample code to use as a base for this is [provided by Amazon](https://aws.amazon.com/blogs/storage/preserving-last-modified-timestamps-when-restoring-amazon-s3-objects-with-aws-backup/)
    * Putting this approach off as future improvement


<!-- TOC --><a name="assumptions"></a>
#### Assumptions
* Bucket keys up to the first `/` delimiter will be used as deployment directories checking modify times
* Last modify time is suitable for identifying X most recent deployments
* We'll use modify date of a single key under each deployment folder
  * This is because we lack any standardized file layout or naming conventions
  * We'll use the modify date of the first key we identify under eaach deployment
* A *"deployment"* will be all objects sharing a prefix matching from the first character up to the first `/` in the key.
* We'll use either minio or localstack for locally mocking and testing the S3 api calls

<!-- TOC --><a name="challenge-questions-and-answers"></a>
### Challenge Questions and Answers

**1. Where should we run this script?**

There are several options open to us for where to run this.

For one-off or on demand use cases we can run this from any developer laptop
with the proper IAM permissions to manage the bucket. In a more typical setup
we could easily drop this into any CI or other tool that supports being used
as a scheduler and run it hourly or daily as needed. A more modern solution
would be to write this as a lambda and deploy it to each environment where we
expect to manage S3 deployment buckets.

More important than where we run it is that we build it into our automation
processes. The code should be generalized so that it can easily be deployed
and configured across as many environments as necessary unless were lucky
enough to work in an organization with a single account managing all deployments.

**2. How should we test the script before running it production?**

The script can be tested locally by following the dev guide below. With a little
polish we'd wrap it up in a terraform or SAM lambda deploy and we could test it
in a dev and/or QA environment before letting it into production.

For local testing a fuzzer script has been added that generates sample deploys. These
are randomized "good-enough" analogues of the example bucket to use for any amount of
testing someone might do. The fuzzer can easily be pointed at a live S3 bucket for
testing as well by setting up the aws access properly.

**3. If we want to add an additional requirement of deleting deploys older than X days but we must maintain at least Y number of deploys. What additional changes would you need to make in the script?**

Since we're already maintaining Y number of deploys we can update the script to
delete based on modified date instead of everything older than Y deploys. We are
already using the modify time to identify deployment ages so implementing this
should be as easy as acting on the list against each modified date past position
Y rather than everything past position Y.

<!-- TOC --><a name="usage-guide"></a>
## Usage Guide

<!-- TOC --><a name="prerequisites"></a>
### Prerequisites

* Python3
* Poetry
* AWS CLI: `brew install awscli`
* Localstack: see install steps below

**Install Localstack:**
1. Pull the LocalStack Docker image: `docker pull localstack/localstack:latest`
2. Start the LocalStack container: `docker run -p 4566:4566 --name localstack -d localstack/localstack:s3-latest`
3. Configure your AWS client to use the LocalStack server:
    - Set the endpoint URL: `export AWS_ENDPOINT_URL=http://localhost:4566`
    - Set initial access key and secret key as below. LocalStack uses a default access key test and a default secret key test
        - `export AWS_ACCESS_KEY_ID=test`
        - `export AWS_SECRET_ACCESS_KEY=test`
        - `export AWS_DEFAULT_REGION=us-east-1`
4. Create an initial bucket for local testing: `aws s3api create-bucket --bucket test-bucket`

**NOTE:** You can also use localstack/localstack:s3-latest in step 1 if you want to just run localstack S3 without other services


<!-- TOC --><a name="local-test-walkthrough"></a>
### Local Test Walkthrough

1. Initialize poetry environment and install dependencies

```
poetry install
```

2. Run static tests and validations against code

```
poetry run black sure_challenge/
poetry run pytest
```

3. Create some sample deployments

Each run of fuzz_deployment will add several keys underneath a randomized deployment
folder. The number passed into the script specifies how many deployments to add.

```
poetry run sure_challenge/fuzz_deployment.py --bucket_name test-bucket --deploy_count 5
```

4. Run deployment cleaner and let it clear out deployments older than specified

In our example case we'll set an environment variable to specify to the code that we
intend to only keep the latest N deployments. All deployments older than N will be
deleted in full.

```
export DEPLOYMENT_RETENTION=3
export DEPLOYMENT_BUCKET='test-bucket'
poetry run sure_challenge/deployment_cleaner.py
```

Once this runs we can use something like `aws s3 ls test-bucket` to verify we only
have as many prefixes listed as the value we set for DEPLOYMENT_RETENTION. From here
we can update code and reiterate on steps 3 and 4 until we're satisfied with our
changes.


<!-- TOC --><a name="remote-deployment"></a>
### Remote Deployment

My intention was to set up a quick folder structure to show off how to deploy
the script both locally as a lambda against Localstack and to a live environment
using SAM and localstack SAM integrations.

Unfortunately, the laptop I'm on is ancient and running big sur which doesn't play
nicely with brew anymore so I'm limited by localstack-cli not installing cleanly.

The basic setup would showcase a few things if it were workable on this machine:
  * [SAM integrations for Localstack](https://docs.localstack.cloud/user-guide/integrations/aws-sam/)
  * VSCode debugging attachments
  * Setting a scheduled lambda up using SAM
  * Hooking the python handler
  * [Basic configuration using SAM templates](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-specification-template-anatomy.html)
