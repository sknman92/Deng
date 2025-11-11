import dotenv
import os
import boto3
import re
from datetime import datetime, timedelta

# loading env var
dotenv.load_dotenv()
aws_key = os.getenv('AWS_ACCESS_KEY')
aws_secret_key = os.getenv('AWS_SECRET_KEY')
bucket=os.getenv('AWS_BUCKET_NAME')

# creating s3 client
s3_client = boto3.client(
's3'
, aws_access_key_id = aws_key
, aws_secret_access_key=aws_secret_key
)
    
def amp_data_load():

    try:
        
        files = os.listdir('data/')
        
        # collating all files in directory
        file_list = [os.path.join('data/', file) for file in files if file.endswith('.json')]

        num_files = len(file_list)
        # check that there is file        
        if num_files > 0:

            # uploading and removing file
            for file in file_list:
                if file.endswith('.json'):
                    if 'list' in file:
                        sub_dir = 'list/'
                    else:
                        sub_dir = 'events/'
                    s3_filename= 'python-import/' + sub_dir + re.sub(r'data/', '', file)
                    # for splitting out events and list data
                    s3_client.upload_file(file, bucket, s3_filename)
                    os.remove(file)

            print(f'Successfully loaded {num_files} file(s) to S3 bucket')
        
        else: 
            print('No files found')

    except Exception as e:
        print(f'Error occured: {e}')
        raise e

def return_s3_files():

    paginator = s3_client.get_paginator('list_objects_v2')
    
    files = []
    for page in paginator.paginate(Bucket=bucket, Prefix='python-import/events'):
        # we are only interested in pulling events jsons
        if 'Contents' in page:
            files.extend([obj['Key'] for obj in page['Contents'] if obj['Key'].endswith('.json')])
    
    return files

def pull_missing_events(files):

    # extract date and time
    datetime_list = []
    for file in files:
        match = re.search(r'(\d{4}-\d{2}-\d{2}_\d{1,2})', file)
        datetime_list.append(match.group())
    
    # formatting datetime list
    datetime_list = [datetime.strptime(d, "%Y-%m-%d_%H") for d in datetime_list]

    # sorting 
    datetime_list.sort()

    # finding min and max datetime
    min_dt = min(datetime_list)
    max_dt = max(datetime_list)

    # scaffolding to fill in gaps
    date = min_dt
    date_scaffold = []
    while date <= max_dt:
        date_scaffold.append(date)
        date += timedelta(hours=1)

    # collating missing dt
    missing_dt = [dt for dt in date_scaffold if dt not in datetime_list]

    # creating start, end ranges to retry api call
    ## has to be within 24 hours
    if missing_dt:
        start = missing_dt[0]
        end = start

        ranges = []
        for dt in missing_dt[1:]:
            if dt == end + timedelta(hours=1) and (dt - start).total_seconds() <= 24*3600:
                end = dt
            else:
                start_formatted = start.strftime("%Y%m%dT%H")
                end_formatted = end.strftime("%Y%m%dT%H")
                range_dict = {'start' : start_formatted,
                            'end' : end_formatted}
                ranges.append(range_dict)
                start = dt
                end = dt

        start_formatted = start.strftime("%Y%m%dT%H")
        end_formatted = end.strftime("%Y%m%dT%H")
        range_dict = {'start' : start_formatted,
                    'end' : end_formatted}
        ranges.append(range_dict)

    return ranges


