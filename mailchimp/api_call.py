from utils import list_campaigns, get_campaign_info, get_campaign_recipients, get_campaign_click_info, get_campaign_email_info, get_campaign_reports, saving_file, s3_data_load, retry
import pandas as pd

import importlib
import utils
importlib.reload(utils)

########### getting members and member activity per campaign ###########

@retry(retries=2, sleep = 10)
def fecth_mailchimp_data():
    extract_time = pd.Timestamp.now()
    # retrieve all campaigns
    campaigns, total_items = list_campaigns()

    # retrieving campaign reports
    df_campaigns = get_campaign_reports(extract_time)

    # retrieve list IDs for each campaign
    list_ids = []
    for c in campaigns:
        list_id = get_campaign_info(c)
        list_ids.append(list_id)

    # deduping list IDs
    list_ids = list(set(list_ids))

    # retrieve all recipients for each list ID
    members_list = []
    for l in list_ids:
        members, extract_time = get_campaign_recipients(l, extract_time)
        members_list.append(members)

    df_members = pd.concat(members_list, ignore_index=True)

    # retrieving click activity for members for each campaign
    clicks_list = []
    for c in campaigns:
        df_temp = get_campaign_click_info(c, extract_time)
        clicks_list.append(df_temp)

    df_clicks = pd.concat(clicks_list, ignore_index=True)

    # retrieving email activity for members for each campaign
    email_list = []
    for c in campaigns:
        df_temp = get_campaign_email_info(c, extract_time)
        email_list.append(df_temp)

    df_email_activity = pd.concat(email_list, ignore_index=True)

    # saving results to local directory
    saving_file(df_members, extract_time, 'data/members/')
    saving_file(df_clicks, extract_time, 'data/clicks/') 
    saving_file(df_email_activity, extract_time, 'data/email_activity/')
    saving_file(df_campaigns, extract_time, 'data/campaigns/')

    # uploading to s3
    s3_data_load()

if __name__ == "__main__":
    fecth_mailchimp_data()




