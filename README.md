# s3-default-bucket-encrypter
AWS Lambda function to automatically enable default encryption on S3 buckets in
your entire account.

## Motivation
Have you ever heard the following?

> _"Please enable encryption at rest on these 483 buckets for compliance
reasons, **and** make sure all new buckets have encryption in the future"_

or thought to yourself?

> _"Dang, I forgot to enable encryption on that bucket I created yesterday"_

... or have an autonomous organization where anyone can create buckets?

_the list goes on..._

## Why not AWS Config Rules?
I tried using [AWS Config Rules](https://aws.amazon.com/config/) for this use
case and it wasn't a great experience. I found it very odd that AWS Config Rules
had to be applied to every region, that takes quite abit of coordination and
oversight to make sure it always works in the future. Plus, AWS Config Rules are
expensive! $2/rule per region plus extra costs per resource tracked.

### Cost
This code runs twice per day and executes in under 30 seconds for an account
with 50 buckets.

128MB Function = $0.000000208/100ms  
30,000ms per execution * 2x/day = ~1,800,000ms/month  
(1,800,000/100) * .000000208 = $0.003744/month

Unfortunately, for true _cloud-scale_ usage, this approach will not scale past
500 buckets as written (due to the 5 minute lambda timeout). This example
implementation will need to be re-written to use threads or AWS Fargate like I
experimented with [here](https://github.com/jolexa/fargate-from-lambda)

#### Deploy
- Load AWS credentials
- Modify `deployment.yml` for your own lambda bucket location
- Run `make`

#### Tagging Exclusion
To exclude this lambda function from automatically enabling encryption, you can
set `X-StopAutoEncrypt = true` on the bucket.

#### SNS Support
Once this is deployed, find the SNS Topic and add your email address to receive
notifications that look like:
> _"Bucket 'mybucket' was automatically encrypted, there were 123 items that are
[maybe] not encrypted."_

### Conclusion
AWS Config Rules are promising, but need some work for real life usage in a way
that is not cumbersome to maintain and expensive. In this case, I have an example of one
lambda function that takes the place of 15 Rules and will automatically fix the
buckets when they are _not_ in compliance. There is no AWS-Managed config rule
for this case and the current rules check for bucket policy not bucket
encryption status, so I would have to write my own custom rule anyway! (and
get charged for Lambda execution, management, etc)

I'm happy with this approach for my personal usage and will point people here in
the future until AWS Config becomes more approachable for this case.
