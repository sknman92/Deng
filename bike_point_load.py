import dotenv
import os
import boto3

# loading env var
dotenv.load_dotenv()
aws_key = os.getenv('AWS_ACCESS_KEY')
aws_secret_key = os.getenv('AWS_SECRET_KEY')
bucket=os.getenv('BUCKET_NAME')
print(bucket)

# creating s3 client
s3_client = boto3.client(
    's3'
    , aws_access_key_id=aws_key
    , aws_secret_access_key=aws_secret_key
)

def bike_load():
    try:
        # fetching list of buckets
        # nest w. try and except to test s3_client.list_objects_v2 function
        s3_client.list_objects_v2(Bucket=bucket)
        
        files = os.listdir('data/')
        
        # collating all files in directory
        file_list = [os.path.join('data/', file) for file in files if file.endswith('.json')]

        num_files = len(file_list)
        # check that there is file        
        if num_files > 0:

            # uploading and removing file
            for file in file_list:
                s3_filename = os.path.join('python-import', file)
                s3_client.upload_file(file, bucket, s3_filename)
                os.remove(file)

            print(f'Successfully loaded {num_files} file(s) to S3 bucket')
        
        else: 
            print('No files found')

    except Exception as e:
        print(f'Error occured: {e}')
        raise e

if __name__ == '__main__':
    bike_load()

