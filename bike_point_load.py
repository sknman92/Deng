import dotenv
import os
import boto3

# loading env var
dotenv.load_dotenv()
aws_key = os.getenv('aws_access_key')
aws_secret_key = os.getenv('aws_secret_key')
bucket=os.getenv('bucket_name')

# creating s3 client
s3_client = boto3.client(
    's3'
    , aws_access_key_id = aws_key
    , aws_secret_access_key=aws_secret_key
)

try:
    # fetching list of buckets
    # nest w. try and except to test s3_client.list_objects_v2 function
    s3_client.list_objects_v2(Bucket=bucket)
    files = os.listdir('data/')

    # collating all files in directory
    file_list = []
    for file in files:
        if file.endswith('.json'):
            files_path = os.path.join('data/', file)
            file_list.append(files_path)

    num_files = len(file_list)

    # check that there is file        
    if num_files > 0:
        
        s3_filename = files[0]

        # uploading
        s3_client.upload_file(file_list[0], bucket, s3_filename)

        # removing uploaded file
        os.remove(file_list[0])

        print(f'Successfully loaded {num_files} file(s) to S3 bucket')
    
    else: 
        print('No files found')

except Exception as e:
    print(f'Error occured: {e}')
    raise e


