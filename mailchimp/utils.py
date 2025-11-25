import pandas as pd
import requests
import os
from dotenv import load_dotenv
import re
import logging

import boto3
import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing.api_client import ApiClientError

from datetime import datetime, timedelta 

# logging config
logging.basicConfig(
    filename="mailchimp.log",
    filemode = "a",
    format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.INFO)

logger = logging.getLogger()

########### loading env ###########
load_dotenv(override=True)
API_KEY = os.getenv('API_KEY')
aws_key = os.getenv('AWS_ACCESS_KEY')
aws_secret_key = os.getenv('AWS_SECRET_KEY')
bucket=os.getenv('AWS_BUCKET_NAME')

########### listing campaigns ###########
def list_campaigns(days_since = 180):
    try:
        client = MailchimpMarketing.Client()
        client.set_config({
            "api_key": API_KEY
        })

        since_send_time = (datetime.utcnow() - timedelta(days=days_since)).isoformat()

        response = client.campaigns.list(since_send_time=since_send_time, count=1000)
        campaigns = [c['id'] for c in response['campaigns']]
        total_items = response['total_items']
        logger.info(f'Successfully retrieved {total_items} campaigns')
        print(f'Successfully retrieved {total_items} campaigns')
        return campaigns, total_items
        
    except ApiClientError as error:
        logger.error(f'Error retrieving campaigns: {error.text}')
        print("Error: {}".format(error.text))

########### getting info for specific campaigns ###########
def get_campaign_info(campaign_id):
    try:
        client = MailchimpMarketing.Client()
        client.set_config({
            "api_key": API_KEY
        })

        response = client.campaigns.get(campaign_id)
        list_id = response['recipients']['list_id']

        print(f'Campaign {campaign_id} is associated with list {list_id}')
        logger.info(f'Campaign {campaign_id} is associated with list {list_id}')

        return list_id
        
    except ApiClientError as error:

        print("Error: {}".format(error.text))
        logger.error(f'Error retrieving campaign info for {campaign_id}: {error.text}')

########### getting click info for specific campaigns ###########
def get_campaign_click_info(campaign_id):
    url = f'https://us2.api.mailchimp.com/3.0/reports/{'908a77c7ab'}/click-details'
    clicks = []
    offset = 0
    count = 1000  # max Mailchimp allows

    # Get total number of members
    response = requests.get(
        url,
        auth=("anystring", API_KEY),
        params={"count": 1, "offset": 0}
    )
    data = response.json()
    temp = pd.json_normalize(data)
    total_items = data.get('total_items', 0)

    response_test = requests.get(url = 'https://us2.api.mailchimp.com/3.0/reports/908a77c7ab/click-details/62df2a81b6/members',
                                auth=("anystring", API_KEY))

    rows = []
    for members in response_test.json().get('members', []):
        row = {'email_id' : members['email_id'],
               'email_address' : members['email_address'],
               'clicks' : members['clicks'],
               'link' : members['link'],
               'campaigin_id' : members['campaign_id'],
               'url_id' : members['url_id'],
               ''}
        rows.append(row)
    
    df_clicks = pd.DataFrame(rows)

    print(f'Total members in list {list_id}: {total_items}')

    # Paginate properly
    while True:
        response = requests.get(
            url,
            auth=("anystring", API_KEY),
            params={"count": count, "offset": offset}
        )
        data = response.json()
        page_members = data.get('members', [])

        # If no more members returned, stop
        if not page_members:
            break

        # Process this page
        for d in page_members:
            members.append({
                'email_address': d.get('email_address'),
                'status': d.get('status'),
                'company': d.get('company', ''),
                'full_name': d.get('full_name', ''),
                'timestamp_signup': d.get('timestamp_signup'),
                'last_changed': d.get('last_changed'),
                'extract_time': extract_time
            })

        # Increase offset for next page
        offset += count


########### getting all recipients who received campaign ###########
def get_campaign_recipients(list_id, extract_time):
    url = f'https://us2.api.mailchimp.com/3.0/lists/{list_id}/members'
    members = []
    offset = 0
    count = 1000  # max Mailchimp allows

    # Get total number of members
    response = requests.get(
        url,
        auth=("anystring", API_KEY),
        params={"count": 1, "offset": 0}
    )
    data = response.json()
    total_items = data.get('total_items', 0)

    print(f'Total members in list {list_id}: {total_items}')

    # Paginate properly
    while True:
        response = requests.get(
            url,
            auth=("anystring", API_KEY),
            params={"count": count, "offset": offset}
        )
        data = response.json()
        page_members = data.get('members', [])

        # If no more members returned, stop
        if not page_members:
            break

        # Process this page
        for d in page_members:
            members.append({
                'email_address': d.get('email_address'),
                'status': d.get('status'),
                'company': d.get('company', ''),
                'full_name': d.get('full_name', ''),
                'timestamp_signup': d.get('timestamp_signup'),
                'last_changed': d.get('last_changed'),
                'extract_time': extract_time
            })

        # Increase offset for next page
        offset += count

        # Stop if we’ve fetched all items
        if len(members) >= total_items:
            break

    df_members = pd.DataFrame(members)

    print(f'Retrieved {len(members)} of {total_items} members from list {list_id}')
    logger.info(f'Retrieved {len(members)} of {total_items} members from list {list_id}')

    return df_members, extract_time


########### getting all recipient activity ###########
def get_recipient_activity(list_id, extract_time):

    try:
        client = MailchimpMarketing.Client()
        client.set_config({
            "api_key": API_KEY
        })

        response = client.lists.get_list_recent_activity('fafd01e9c4')
        print(response)
    except ApiClientError as error:
        print("Error: {}".format(error.text))

########### saving results to local directory ###########
def saving_file(df, extract_time):
    # Convert timestamp to safe string
    safe_time = extract_time.strftime("%Y-%m-%d_%H-%M-%S")
    file_path = f'data/mail_chimp_data_{safe_time}.csv'

    print(f'Saving data to {file_path}')
    logger.info(f'Saving data to {file_path}')
    
    df.to_csv(file_path, index=False)


########### uploading to s3 ###########

# creating s3 client
s3_client = boto3.client(
's3'
, aws_access_key_id = aws_key
, aws_secret_access_key=aws_secret_key
)

def s3_data_load():
    try:
        
        files = os.listdir('data/')
        
        # collating all files in directory
        file_list = [os.path.join('data/', file) for file in files if file.endswith('.csv')]

        num_files = len(file_list)
        # check that there is file        
        if num_files > 0:

            # uploading and removing file
            for file in file_list:
                s3_filename= 'python-import/' + re.sub(r'data/', '', file)
                # for splitting out events and list data
                s3_client.upload_file(file, bucket, s3_filename)
                #os.remove(file)

            print(f'Successfully loaded {num_files} file(s) to S3 bucket')
        
        else: 
            print('No files found')

    except Exception as e:
        print(f'Error occured: {e}')
        raise e