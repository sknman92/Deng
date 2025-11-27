# Amplitude and Mailchimp ELT Project  
This project extract, loads, and transforms data from the Amplitude and Mailchimp APIs. The end goal is to use datasets from both to analyze 
user engagement with The Information Lab's website and email campaigns.

## Extract
### Amplitude
1. Connect to the Amplitude Export and Dashboard API. 
2. Download event data for a given time range as a `.zip` file.
3. Extract `.gz` JSON files from the zip.
4. Retry API calls in case of transient errors (status codes 408 or 500).

### Mailchimp
1. Connect to the Mailchimp API using an API key.
2. Download campaign or list data for a given list_id or campaign_id.
3. Handle paginated responses to collect all members or click details.
4. Transform API JSON responses into a structured format (e.g., pandas DataFrame).
5. Retry API calls in case of transient errors (e.g., network issues or rate limits).
6. Save processed data locally or to a storage location as CSV files.
   
## Load  
1. Upload local JSON files (e.g., from `data/` folder) into an Amazon S3 bucket under folders `python-import/events/` and `python-import/list/`.  
2. List existing event files in S3 to determine which hourly time-slots are *already* present.  
3. Build a scaffold of hourly timestamps between the earliest and latest present hours, then identifying **missing hours**.  
4. Convert those missing hours into **consecutive retry ranges** (each range capped at 24 hours, and formatted like `YYYYMMDDTHH`).  
5. Feed those missing-ranges into downstream API calls or back-fill logic.

## Key Features  
- Module-level S3 client initialization (so you don’t recreate the client in every function).  
- File system operations: scanning `data/`, filtering `.json`, uploading & deleting.  
- Regex-based timestamp extraction from filenames (e.g., `…_2025-11-04_11#0.json.gz.json`).  
- Efficient gap detection by converting filenames → datetime objects → full hourly scaffold → missing hours set.  
- Formatting of start/end ranges for missing hours in the standardized string format, e.g., `20251104T12` → `20251105T08`.  
- Extensibility: you can plug in your API call logic using the resulting `ranges` list.

<img width="2648" height="2368" alt="image" src="https://github.com/user-attachments/assets/2426a60e-13e8-483e-9f23-0e05e05a4f1a" />
<img width="2648" height="2368" alt="image" src="https://github.com/user-attachments/assets/e8a00dbf-fb1c-4dfd-a587-2b6d2b28f8ac" />
<img width="2684" height="2444" alt="image" src="https://github.com/user-attachments/assets/6c9a181b-6403-4685-876a-dd94e3282623" />


## Why S3 -> Snowflake

1. Data Consolidation: the staging layer allows the collection of data from multiple source systems regardless of data types and formats
2. Data Quality Enhancement: data cleaning, standardisation, and quality enrichment can be applied at the staging layer
3. Schema Alignment: the staging layer allows for necessary transformations to align data schemas from different sources

## Security Overview

The ETL pipeline handles sensitive data and leverages AWS and Snowflake security features to ensure **data confidentiality, integrity, and controlled access**.

### Key Security Components

- **Least Privilege Access**
  - Users, services, and scripts are granted **only the permissions they need**.
  - Minimizes risk if credentials are compromised.

- **Data Encryption**
  - **At rest:** All data stored in S3 or Snowflake is encrypted using **KMS-managed keys**.
  - **In transit:** All network communication (API calls, uploads, downloads) uses **TLS/SSL encryption**.

- **AWS KMS Keys**
  - **Customer-managed KMS keys** are used to encrypt/decrypt S3 objects.
  - Ensures that only authorized users or roles can access encryption keys.

- **IAM Policies**
  - Define **who can access what resources** (S3 buckets, KMS keys, Snowflake storage integration).
  - Provides fine-grained control over read, write, and manage permissions.

- **Roles and Policy Attachments**
  - IAM **roles** are assigned to scripts or services.
  - Roles have attached policies granting temporary credentials for secure, auditable access.
  - Supports cross-account access and integration with Snowflake storage.

- **Snowflake Storage Integration**
  - Uses IAM roles and policies to allow Snowflake to securely access S3 objects.
  - Only the defined storage integration can read the bucket contents.
  - Ensures secure, automated ingestion of S3-staged files into Snowflake tables.

### How These Components Work Together

- Data is **encrypted at rest** in S3 using KMS keys and **encrypted in transit** via TLS/SSL.
- **IAM roles with least privilege** enforce access control for both S3 and KMS keys.
- **Snowflake storage integration** leverages these roles to securely ingest only authorized data.
- The combination of encryption, access policies, and role-based permissions ensures **confidentiality, integrity, and controlled access** from the API through S3 staging into Snowflake.

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd <repo-directory>

2. **Create a Python virtual environment**
   ```bash
   python -m venv .amplitude/venv
   
3. ***Activate the virtual environment***
   ```bash
   Windows: venv\Scripts\activate
   Linux/macOS: source venv/bin/activate

4. ***Install dependencies***
   ```bash
   pip install -r requirements.txt

5. Create a .env file in the project root with your credentials
