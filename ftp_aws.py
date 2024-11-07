import json
import boto3
import ftplib
import botocore
from botocore.errorfactory import ClientError
from boto3.s3.transfer import TransferConfig
import os 
from base64 import b64decode
import logging
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# encryption decryption for host
ENCRYPTED_HOST = os.environ['FTP_HOST']
DECRYPTED_HOST = boto3.client('kms').decrypt(
    CiphertextBlob=b64decode(ENCRYPTED_HOST),
    EncryptionContext={'LambdaFunctionName': os.environ['AWS_LAMBDA_FUNCTION_NAME']}
)['Plaintext'].decode('utf-8')

# encryption decryption for  for user
ENCRYPTED_USER = os.environ['FTP_USER']
DECRYPTED_USER = boto3.client('kms').decrypt(
    CiphertextBlob=b64decode(ENCRYPTED_USER),
    EncryptionContext={'LambdaFunctionName': os.environ['AWS_LAMBDA_FUNCTION_NAME']}
)['Plaintext'].decode('utf-8')

# encryption decryption for  for pswd
ENCRYPTED_PSWD = os.environ['FTP_PSWD']
DECRYPTED_PSWD = boto3.client('kms').decrypt(
    CiphertextBlob=b64decode(ENCRYPTED_PSWD),
    EncryptionContext={'LambdaFunctionName': os.environ['AWS_LAMBDA_FUNCTION_NAME']}
)['Plaintext'].decode('utf-8')

FTP_HOST = DECRYPTED_HOST
FTP_USER = DECRYPTED_USER
FTP_PSWD = DECRYPTED_PSWD

#Bucket name
s3_bucket_name = <bucket_name>
s3_region_name = <region_name>

# Initialize S3 client
s3_client = boto3.client(
   's3',
   aws_access_key_id= <id>,
   aws_secret_access_key= <key>,
   region_name=s3_region_name
)

# checking if file exists in S3 bucket
def file_exists_in_s3(s3_client, bucket, key):
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        else:
            raise

# Function to get the list of files in the S3 bucket
def list_s3_files(bucket_name):
    s3_files = []
    response = s3_client.list_objects_v2(Bucket=bucket_name)
    if 'Contents' in response:
        for obj in response['Contents']:
            s3_files.append(obj['Key'])
    return s3_files

# downloading file
def download_file(ftp, ftp_file, local_filename, retries=3):
    """Download a file from the FTP server with retry mechanism."""
    for attempt in range(retries):
        try:
            with open(local_filename, 'wb') as local_file:
                ftp.retrbinary('RETR ' + ftp_file, local_file.write)
            logger.info(f'Successfully downloaded {ftp_file}')
            return True
        except ftplib.all_errors as e:
            logger.error(f"Attempt {attempt + 1} failed to download {ftp_file}: {e}")
            time.sleep(1)  # Wait before retrying
    return False

def lambda_handler(event, context):

    tmp_files = os.listdir('/tmp/')
    
    statuscode = 200
    statusmessage = 'Executed'
    file_size = 0
    threshold_file_size = 52428800  #1024*1024*50 (50MB)
  
    # Get list of files already in the S3 bucket
    s3_files = list_s3_files(s3_bucket_name)
    
    # Connect to FTP server
    ftp = ftplib.FTP(FTP_HOST)
    
    try:
        ftp.login(user=FTP_USER, passwd=FTP_PSWD)
        ftp.set_pasv(True)
        ftp.sendcmd('TYPE I')  # Ensure binary mode
    except ftplib.error_perm as e:
        statuscode = 403
        statusmessage = f"Error {e} in connecting to FTP Server"
        logger.error(f"Error during login or setting binary mode: {e}")
        ftp.quit()
        raise
    
    # List files in the FTP directory
    try:
        ftp_files = ftp.nlst()
    except ftplib.all_errors as e:
        logger.error(f"Failed to list files in FTP directory: {e}")
        ftp.quit()
        raise

    for ftp_file in ftp_files:
        # Check if the file already exists in S3
        if ftp_file in s3_files:
            logger.info(f'Skipping {ftp_file} as it already exists in S3')
            continue
    
        # Download each file with retry mechanism
        local_filename = f"/tmp/{ftp_file}"
          
        if not download_file(ftp, ftp_file, local_filename):
            logger.error(f"Failed to download {ftp_file} after multiple attempts")
            continue
    
        # Upload to S3
        try:
            if os.path.exists(local_filename):
                file_size = os.path.getsize(local_filename)
                logger.info(f"Size of the file '{local_filename}': {file_size} bytes")
            else:
                logger.error(f"File '{local_filename}' does not exist")
            
            if file_size >= threshold_file_size:
                s3_client.upload_file(local_filename, s3_bucket_name, ftp_file)
                logger.info(f'Successfully uploaded {ftp_file} to S3')
            else:
                logger.error(f"Size of the file '{local_filename}': {file_size} bytes is not uploaded to S3 Bucket")
                continue
                
        except Exception as e:
            logger.error(f"Failed to upload {ftp_file} to S3: {e}")
            continue
        finally:
            # Remove local file after upload although the tmp files are removed 
            if os.path.exists(local_filename):
                os.remove(local_filename)
        logger.info("After Removing Files checking in /tmp: %s", tmp_files)

    # Close FTP connection
    try:
      ftp.quit()
    except Exception as e: 
        logger.error(f"Error {e} in Closing the FTP connection")    

    return {
        'statusCode': statuscode,
        'body': statusmessage
    }
