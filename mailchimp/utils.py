import pandas as pd
import requests
import os
from dotenv import load_dotenv
import re
import logging
import time

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
API_KEY = os.getenv('MC_API_KEY')
aws_key = os.getenv('MC_AWS_ACCESS_KEY')
aws_secret_key = os.getenv('MC_AWS_SECRET_KEY')
bucket=os.getenv('MC_AWS_BUCKET_NAME')

########### retry decorator ###########
def retry(retries = 3, sleep = 5):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(1, retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f'Retry {i} failed')
                    # raising last exception captured
                    exception = e
                    time.sleep(sleep)
            raise exception
        return wrapper
    return decorator

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

########### getting campaign reprots ###########
def get_campaign_reports(extract_time, days_since = 180):
    try:
        client = MailchimpMarketing.Client()
        client.set_config({
            "api_key": API_KEY
        })

        since_send_time = (datetime.utcnow() - timedelta(days=days_since)).isoformat()
        response = client.reports.get_all_campaign_reports(since_send_time=since_send_time, count=1000)

        campaigns_list = []
        for m in response['reports']:
            row = {
                'campaign_id' : m.get('id'),
                'campaign_title': m.get('campaign_title'),
                'emails_sent': m.get('emails_sent'),
                'unsubscribed': m.get('unsubscribed'),
                'abuse_reports': m.get('abuse_reports'),
                'bounces': m.get('bounces'),
                'forwards': m.get('forwards'),
                'opens': m.get('opens', {}).get('opens_total'),
                'clicks': m.get('clicks', {}).get('clicks_total'),
                'last_open': m.get('opens', {}).get('last_open'),
                'last_click': m.get('clicks', {}).get('last_click'),
                'extract_time': extract_time
            }
            campaigns_list.append(row)
        
        df_campaigns = pd.DataFrame(campaigns_list)
        total_items = len(campaigns_list)
        logger.info(f'Successfully retrieved {total_items} campaign reports')
        print(f'Successfully retrieved {total_items} campaign reports')
        return df_campaigns
    
    except ApiClientError as error:
        print("Error: {}".format(error.text))
        logger.error(f'Error retrieving campaign reports: {error.text}')

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
def get_campaign_click_info(campaign_id, extract_time):
    url = f'https://us2.api.mailchimp.com/3.0/reports/{campaign_id}/click-details'
    offset = 0
    count = 1000 # max Mailchimp allows

    # number of urls
    response = requests.get(
        url,
        auth=("anystring", API_KEY),
        params={"count": count, "offset": 0}
    )
    data = response.json()
    total_items = data.get('total_items', 0) # number of urls

    print(f'Total urls in campaign {campaign_id}: {total_items}')
    logger.info(f'Total urls in campaign {campaign_id}: {total_items}')

    # geting url links sent in campaign
    rows = []
    
    for urls_clicked in data['urls_clicked']:
        row = {
            'Campaign_ID' : urls_clicked['campaign_id'],
            'url_link' : urls_clicked['url'],
            'url_id' : urls_clicked['id'],
            'total_clicks' : urls_clicked['total_clicks'],
            'unique_clicks' : urls_clicked['unique_clicks'],
            'url_members' : [u['href'] for u in urls_clicked['_links'] if u['rel'] == 'members'][0]
            }
        rows.append(row)
    
    df_urls_clicked = pd.DataFrame(rows)

    # getting members who clicked on each link per campaign
    members_list = []
    for index, row in df_urls_clicked.iterrows():
        offset = 0
        link_id = row['url_id']
        url_temp = f'https://us2.api.mailchimp.com/3.0/reports/{campaign_id}/click-details/{link_id}'
        response = requests.get(url = url_temp, auth=("anystring", API_KEY), params={"count": count, "offset": offset})
        data_link = response.json()        
        id = data_link['id']
        url_members_endpoint = f'https://us2.api.mailchimp.com/3.0/reports/{campaign_id}/click-details/{id}/members'
        response_members = requests.get(
            url = url_members_endpoint,
            auth=("anystring", API_KEY),
            params={"count": 1, "offset": offset}
        )
        data_members = response_members.json()
        total_clicks = data_members['total_items']

        # paginating through members who clicked on the link
        while True:
            response_members = requests.get(
            url = url_members_endpoint,
            auth=("anystring", API_KEY),
            params={"count": count, "offset": offset}
        )
            data_members = response_members.json()
            
            for m in data_members.get('members'):
                member = {
                'url_link' : row['url_link'],
                'url_id' : row['url_id'],
                'campaign_id' : row['Campaign_ID'],
                'email_id' : m.get('email_id'),
                'email_address': m.get('email_address'),
                'clicks': m.get('clicks'),
                'extract_time': extract_time
            }
                members_list.append(member)

            offset += count

            if offset >= total_clicks:
                break

    df_members_clicked = pd.DataFrame(members_list)

    if df_members_clicked.empty:
        total_clicks = 0
        total_members = 0
    else:
        total_clicks = df_members_clicked['clicks'].sum()
        total_members = df_members_clicked['email_id'].nunique()

    print(f'Retrieved {total_members} members who clicked links {total_clicks} times in campaign {campaign_id}')
    logger.info(f'Retrieved {total_members} members who clicked links {total_clicks} times in campaign {campaign_id}')  

    return df_members_clicked

########### getting email activity for campaigns ###########
def get_campaign_email_info(campaign_id, extract_time):
    url = f'https://us2.api.mailchimp.com/3.0/reports/{campaign_id}/email-activity'
    offset = 0
    count = 1000 # max Mailchimp allows

    # intial call to get total number of items
    response = requests.get(
        url,
        auth=("anystring", API_KEY),
        params={"count": 1, "offset": 0}
    )

    data = response.json()
    total_items = data['total_items']

    # paginating through email activity
    email_activity_list = []
    while True:

        response = requests.get(
        url,
        auth=("anystring", API_KEY),
        params={"count": count, "offset": offset}
    )
        data = response.json()
        for d in data['emails']:
            for a in d.get('activity', {}):
                email_activity = {
                    'campaign_id' : campaign_id,
                    'email_id' : d.get('email_id', ''),
                    'email_address': d.get('email_address', ''),
                    'action': a.get('action', ''),
                    'timestamp': a.get('timestamp', ''),
                    'type': a.get('type', ''),
                    'url': a.get('url', ''),
                    'ip' : a.get('ip', ''),
                    'extract_time': extract_time
                }
                email_activity_list.append(email_activity)
        
        offset += count
        
        if offset >= total_items:
            break   
    
    df_email_activity = pd.DataFrame(email_activity_list)

    return df_email_activity
    
########### getting recipients of campaigns ###########
def get_campaign_recipients(list_id, extract_time):
    url = f'https://us2.api.mailchimp.com/3.0/lists/{list_id}/members'
    members = []
    offset = 0
    count = 1000  # max Mailchimp allows

    # Get total number of members to paginate through
    response = requests.get(
        url,
        auth=("anystring", API_KEY),
        params={"count": 1, "offset": 0}
    )
    data = response.json()
    total_items = data.get('total_items', 0)

    print(f'Total members in list {list_id}: {total_items}')

    # Pagination
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

        # Process page
        for d in page_members:
            members.append({
                'member_id' : d.get('id'),
                'email_address': d.get('email_address'),
                'status': d.get('status'),
                'company' : d.get('merge_fields', {}).get('COMPANY', ''),
                'full_name': d.get('full_name', ''),
                'timestamp_signup': d.get('timestamp_signup'),
                'last_changed': d.get('last_changed'),
                'extract_time': extract_time
            })

        # Increase offset for next page
        offset += count

        # Stop if we’ve fetched all items
        if len(members) == total_items:
            break

    df_members = pd.DataFrame(members)

    print(f'Retrieved {len(members)} of {total_items} members from list {list_id}')
    logger.info(f'Retrieved {len(members)} of {total_items} members from list {list_id}')

    return df_members, extract_time

########### saving results to local directory ###########
def saving_file(df, extract_time, sub_dir='data/members/'):
    # Convert timestamp to string
    extract_time_formatted = extract_time.strftime("%Y-%m-%d_%H-%M-%S")
    sub_dir = sub_dir
    if 'members' in sub_dir:
        file_name = 'members'
    elif 'clicks' in sub_dir:
        file_name = 'clicks'
    elif 'email_activity' in sub_dir:
        file_name = 'email_activity'
    elif 'campaigns' in sub_dir:
        file_name = 'campaigns'

    file_path = f'{sub_dir}/{file_name}_{extract_time_formatted}.csv'

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

        file_list = []

        for root, dirs, files in os.walk("data/"):
            for file in files:
                file_list.append(os.path.join(root, file))

        num_files = len(file_list)
        # check that there is file        
        if num_files > 0:

            # uploading and removing file
            for file in file_list:
                s3_filename= 'python-import/' + re.sub(r'data/', '', file)
                # normalizing slashes for s3
                s3_filename = s3_filename.replace("\\", "/")
                # for splitting out events and list data
                s3_client.upload_file(file, bucket, s3_filename)
                #os.remove(file)

            print(f'Successfully loaded {num_files} file(s) to S3 bucket')
        
        else: 
            print('No files found')

    except Exception as e:
        print(f'Error occured: {e}')
        raise e
