import os
import boto3

def get_client(id):
    return get_session().client(id)

def get_session():
    aws_region = os.environ.get('AWS_REGION')
    if not aws_region:
        raise Exception("Error: AWS_REGION environment variable must be set.")
    access_key, secret_key = get_credentials()
    return boto3.session.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=aws_region)

def get_credentials():
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    token_file_path = os.getenv('AWS_WEB_IDENTITY_TOKEN_FILE')
    role_arn = os.getenv('AWS_ROLE_ARN')

    if access_key:
        if not secret_key:
            raise Exception("Error: AWS_SECRET_ACCESS_KEY environment variable must be set when using access key.")
        return access_key, secret_key
    elif token_file_path:
        if not role_arn:
            raise Exception("Error: AWS_ROLE_ARN environment variable must be set when using web identity.")

        role = boto3.client('sts').assume_role_with_web_identity(
            RoleArn=os.getenv("AWS_ROLE_ARN"),RoleSessionName='assume-role',
            WebIdentityTokenFile=token_file_path)
        credentials = role['Credentials']
        return credentials['AccessKeyId'], credentials['SecretAccessKey']
    else:
        raise Exception("Error: Neither AWS_ACCESS_KEY_ID nor AWS_WEB_IDENTITY_TOKEN_FILE is set.")