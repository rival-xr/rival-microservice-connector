import os
import boto3

def get_client(id):
    return get_session().client(id)

def get_session():
    aws_region = os.environ.get('AWS_REGION')
    if not aws_region:
        raise Exception("Error: AWS_REGION environment variable must be set.")
    
    token_file_path = os.getenv('AWS_WEB_IDENTITY_TOKEN_FILE')
    if token_file_path:
        with open(os.getenv("AWS_WEB_IDENTITY_TOKEN_FILE"), 'r') as content_file:
            web_identity_token = content_file.read()
        role_arn = os.getenv('AWS_ROLE_ARN')
        if not role_arn:
            raise Exception("Error: AWS_ROLE_ARN environment variable must be set when using web identity.")
        role = boto3.client('sts').assume_role_with_web_identity(
            RoleArn=os.getenv("AWS_ROLE_ARN"),RoleSessionName='assume-role',
            WebIdentityToken=web_identity_token)
        credentials = role['Credentials']
        return boto3.session.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'],
            region_name=aws_region)
    # use the default, it might be in via AWS_SECRET_ACCESS_KEY and AWS_ACCESS_KEY_ID
    return boto3.session.Session(region_name=aws_region)