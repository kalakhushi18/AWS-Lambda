# FTP to S3 File Transfer Lambda Function

This AWS Lambda function automatically transfers files from an FTP server to an AWS S3 bucket on a periodic basis. It uses encrypted environment variables for secure FTP authentication and AWS SDK for Python (Boto3) for S3 operations.

## Features

- Secure FTP authentication using KMS-encrypted credentials
- Checks for existing files in S3 to avoid duplicates
- Logs transfer activities for monitoring and debugging
- Configurable via environment variables

## Prerequisites

- AWS account with access to Lambda, S3, and KMS services
- FTP server details (host, username, password)
- S3 bucket for file storage
- IAM role for Lambda with necessary permissions

## Setup

1. Create a new Lambda function in your AWS account.
3. Copy the provided code into the Lambda function.
4. Set up the following environment variables in the Lambda configuration:
   - `FTP_HOST`: KMS-encrypted FTP host address
   - `FTP_USER`: KMS-encrypted FTP username
   - `FTP_PSWD`: KMS-encrypted FTP password
   - `AWS_LAMBDA_FUNCTION_NAME`: Name of your Lambda function
5. Update the `s3_bucket_name` and `s3_region_name` variables in the code.
6. Configure the AWS credentials in the code or use IAM roles.

## Configuration

Modify the following variables in the code as needed:

- `s3_bucket_name`: The name of your S3 bucket
- `s3_region_name`: The AWS region of your S3 bucket
- `aws_access_key_id` and `aws_secret_access_key`: Your AWS credentials (if not using IAM roles)

## Deployment

1. Package the Lambda function code and any dependencies.
2. Upload the package to AWS Lambda.
3. Configure the Lambda function's trigger (e.g., CloudWatch Events for periodic execution).

## Usage

Once deployed and configured, the Lambda function will:

1. Decrypt FTP credentials using KMS.
2. Connect to the FTP server.
3. List files in the FTP directory.
4. Check each file against existing files in the S3 bucket.
5. Transfer new or updated files to the S3 bucket.
6. Log the transfer activities.

## Logging

The function uses Python's `logging` module to log information and errors. You can view these logs in CloudWatch Logs.

## Security

- FTP credentials are encrypted using AWS KMS for enhanced security.
- Use IAM roles and policies to manage permissions for the Lambda function.
  
## Author

Khushi Kala

