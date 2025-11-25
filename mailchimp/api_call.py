from utils import list_campaigns, get_campaign_info, get_campaign_recipients, saving_file, s3_data_load

import importlib
import utils
importlib.reload(utils)

########### execution ###########

if __name__ == "__main__":
    
    # retrieve all campaigns
    campaigns, total_items = list_campaigns()

    # retrieve list IDs for each campaign
    list_ids = []
    for c in campaigns:
        list_id = get_campaign_info(c)
        list_ids.append(list_id)

    # deduping list IDs
    list_ids = list(set(list_ids))

    # retrieve all recipients for each list ID
    members_list = []
    extract_time = pd.Timestamp.now()
    for l in list_ids:
        members, extract_time = get_campaign_recipients(l, extract_time)
        members_list.append(members)

    # combining all members dataframes
    df_members = pd.concat(members_list, ignore_index=True)

    # saving results to local directory
    saving_file(df_members, extract_time)

    # uploading to s3
    s3_data_load()
    
