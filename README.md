# sns-email

HTTP server to implement forwarding of emails received by AWS SES to a local MTA.

# Deployment

This server should be run behind a HTTPS reverse proxy, and then subscribed to the SNS Topic notified by SES for email receipt.

The server can be also configured to poll the SQS queue used as dead letter for the SNS topic, in order to recover from longer downtimes not covered by SNS redelivery.

If S3 is used for email delivery by SES, the server must have permission to read from the bucket, using the default boto3 credential configuration.
