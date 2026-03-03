import requests
import json
import pandas as pd

# Base URL for the API
BASE_URL = "http://localhost:8000"

def search_jobs_simple():
    """
    Simple job search using the consolidated GET endpoint
    """
    params = {
        "site_name": ["indeed", "linkedin"],
        "search_term": "software engineer",
        "location": "San Francisco, CA",
        "results_wanted": 5
    }
    
    response = requests.get(f"{BASE_URL}/api/v1/search_jobs", params=params)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Found {data['count']} jobs")
        
        # Convert to pandas DataFrame for easier viewing
        df = pd.DataFrame(data['jobs'])
        print(df.head())
        
        # Save to CSV
        df.to_csv("jobs_simple.csv", index=False)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def search_jobs_advanced():
    """
    Advanced job search using GET endpoint with all parameters
    """
    params = {
        "site_name": ["indeed", "linkedin", "zip_recruiter"],
        "search_term": "data scientist",
        "google_search_term": "data scientist jobs near New York, NY since yesterday",
        "location": "New York, NY",
        "distance": 25,
        "job_type": "fulltime",
        "is_remote": True,
        "results_wanted": 10,
        "hours_old": 48,
        "description_format": "markdown",
        "country_indeed": "USA",
        "enforce_annual_salary": True,
        "linkedin_fetch_description": True
    }
    
    response = requests.get(
        f"{BASE_URL}/api/v1/search_jobs",
        params=params
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Found {data['count']} jobs")
        
        # Convert to pandas DataFrame for easier viewing
        df = pd.DataFrame(data['jobs'])
        print(df.head())
        
        # Save to CSV
        df.to_csv("jobs_advanced.csv", index=False)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def search_jobs_paginated():
    """
    Paginated job search using GET endpoint
    """
    params = {
        "paginate": True,
        "page": 1,
        "page_size": 5,
        "site_name": ["indeed", "linkedin"],
        "search_term": "software engineer",
        "location": "San Francisco, CA",
        "results_wanted": 20
    }
    
    response = requests.get(f"{BASE_URL}/api/v1/search_jobs", params=params)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Found {data['count']} total jobs, showing page {data['current_page']} of {data['total_pages']}")
        print(f"Page size: {data['page_size']}, showing {len(data['jobs'])} jobs")
        
        # Convert to pandas DataFrame for easier viewing
        df = pd.DataFrame(data['jobs'])
        print(df.head())
        
        # Check if there's a next page
        if data['next_page']:
            print(f"Next page URL: {data['next_page']}")
        
        # Save to CSV
        df.to_csv("jobs_paginated.csv", index=False)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    print("Running simple job search...")
    search_jobs_simple()
    
    print("\nRunning advanced job search...")
    search_jobs_advanced()
    
    print("\nRunning paginated job search...")
    search_jobs_paginated()
def fetch_single_job_by_url():
    """
    Fetch a single LinkedIn job by URL using GET endpoint
    """
    # First, search for a job to get a real URL
    search_params = {
        "site_name": ["linkedin"],
        "search_term": "software engineer",
        "location": "San Francisco, CA",
        "results_wanted": 1
    }
    
    search_response = requests.get(f"{BASE_URL}/api/v1/search_jobs", params=search_params)
    
    if search_response.status_code == 200:
        jobs = search_response.json()['jobs']
        if jobs:
            # Get the first job's URL
            job_url = jobs[0].get('LINK') or jobs[0].get('job_url')
            
            # Now fetch that single job with full description
            params = {
                "job_url": job_url,
                "fetch_description": True,
                "description_format": "markdown"
            }
            
            response = requests.get(f"{BASE_URL}/api/v1/fetch_job", params=params)
            
            if response.status_code == 200:
                data = response.json()
                print(f"Successfully fetched job: {data['job'].get('TITLE')} at {data['job'].get('COMPANY')}")
                print(f"Cached: {data['cached']}")
                print(json.dumps(data['job'], indent=2, default=str))
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
        else:
            print("No jobs found in search to test fetch")
    else:
        print(f"Search error: {search_response.status_code}")

def fetch_single_job_by_id():
    """
    Fetch a single LinkedIn job by job ID using GET endpoint
    """
    # LinkedIn job ID example
    job_id = "123456789"  # Replace with a real job ID
    
    params = {
        "job_id": job_id,
        "fetch_description": True,
        "description_format": "markdown"
    }
    
    response = requests.get(f"{BASE_URL}/api/v1/fetch_job", params=params)
    
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            print(f"Successfully fetched job: {data['job'].get('TITLE')} at {data['job'].get('COMPANY')}")
            print(f"Cached: {data['cached']}")
        else:
            print(f"Failed to fetch job: {data['error']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def fetch_single_job_post():
    """
    Fetch a single LinkedIn job using POST endpoint with JSON body
    """
    job_data = {
        "job_id": "123456789",  # Replace with a real job ID
        "fetch_description": True,
        "description_format": "markdown",
        "verbose": 2
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/fetch_job",
        json=job_data
    )
    
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            print(f"Successfully fetched job: {data['job'].get('TITLE')} at {data['job'].get('COMPANY')}")
            print(f"Cached: {data['cached']}")
            print(json.dumps(data['job'], indent=2, default=str))
        else:
            print(f"Failed to fetch job: {data['error']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    print("Running simple job search...")
    search_jobs_simple()
    
    print("\nRunning advanced job search...")
    search_jobs_advanced()
    
    print("\nRunning paginated job search...")
    search_jobs_paginated()
    
    print("\nFetching single job by URL...")
    fetch_single_job_by_url()
    
    print("\nFetching single job by ID...")
    fetch_single_job_by_id()
    
    print("\nFetching single job via POST...")
    fetch_single_job_post()