"""Job search service layer."""
from typing import Dict, Any, Tuple, Optional
import pandas as pd
from jobspy import scrape_jobs
import logging
import re
import json
import requests
from bs4 import BeautifulSoup

from app.config import settings
from app.cache import cache

logger = logging.getLogger(__name__)

class JobService:
    """Service for interacting with JobSpy library."""
    
    @staticmethod
    def search_jobs(params: Dict[str, Any]) -> pd.DataFrame:
        """
        Execute a job search using the JobSpy library.
        
        Args:
            params: Dictionary of search parameters
            
        Returns:
            DataFrame containing job results
        """
        # Apply default proxies from env if none provided
        if params.get('proxies') is None and settings.DEFAULT_PROXIES:
            params['proxies'] = settings.DEFAULT_PROXIES
        
        # Apply default CA cert path if none provided
        if params.get('ca_cert') is None and settings.CA_CERT_PATH:
            params['ca_cert'] = settings.CA_CERT_PATH
            
        # Apply default country_indeed if none provided
        if params.get('country_indeed') is None and settings.DEFAULT_COUNTRY_INDEED:
            params['country_indeed'] = settings.DEFAULT_COUNTRY_INDEED
        
        # Check cache first
        cached_results = cache.get(params)
        if cached_results is not None:
            logger.info(f"Returning cached results with {len(cached_results)} jobs")
            return cached_results, True
        
        # Execute search
        jobs_df = scrape_jobs(**params)
        
        # Cache the results
        cache.set(params, jobs_df)
        
        return jobs_df, False

    @staticmethod
    def filter_jobs(jobs_df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """Filter job results based on criteria."""
        filtered_df = jobs_df.copy()
        
        # Filter by salary range
        if 'min_salary' in filters and filters['min_salary'] is not None:
            # Convert to numeric first to handle comparison properly
            filtered_df = filtered_df[filtered_df['MIN_AMOUNT'].astype(float) >= float(filters['min_salary'])]
            
        if 'max_salary' in filters and filters['max_salary'] is not None:
            filtered_df = filtered_df[filtered_df['MAX_AMOUNT'].astype(float) <= float(filters['max_salary'])]
            
        # Filter by company
        if 'company' in filters and filters['company']:
            filtered_df = filtered_df[filtered_df['COMPANY'].str.contains(filters['company'], case=False, na=False)]
            
        # Filter by job type
        if 'job_type' in filters and filters['job_type']:
            filtered_df = filtered_df[filtered_df['JOB_TYPE'] == filters['job_type']]
            
        # Filter by location
        if 'city' in filters and filters['city']:
            filtered_df = filtered_df[filtered_df['CITY'].str.contains(filters['city'], case=False, na=False)]
            
        if 'state' in filters and filters['state']:
            filtered_df = filtered_df[filtered_df['STATE'].str.contains(filters['state'], case=False, na=False)]
            
        # Filter by keyword in title
        if 'title_keywords' in filters and filters['title_keywords']:
            filtered_df = filtered_df[filtered_df['TITLE'].str.contains(filters['title_keywords'], case=False, na=False)]
            
        return filtered_df
    
    @staticmethod
    def sort_jobs(jobs_df: pd.DataFrame, sort_by: str, sort_order: str = 'desc') -> pd.DataFrame:
        """Sort job results by specified field."""
        if not sort_by or sort_by not in jobs_df.columns:
            return jobs_df
            
        ascending = sort_order.lower() != 'desc'
        return jobs_df.sort_values(by=sort_by, ascending=ascending)
    @staticmethod
    def fetch_single_job(job_url: Optional[str], job_id: Optional[str], fetch_description: bool = True, 
                        description_format: str = "markdown", verbose: int = 2) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Fetch a single LinkedIn job by URL or ID using direct page scraping.
        
        Args:
            job_url: Full URL to the LinkedIn job posting
            job_id: LinkedIn job ID (will construct URL from this)
            fetch_description: Whether to fetch full job description
            description_format: Format of job description (markdown, html)
            verbose: Logging verbosity level
            
        Returns:
            Tuple of (job_dict, is_cached) where job_dict is the job details or None if not found
        """
        # Extract job ID from URL or use provided job_id
        linkedin_job_id = job_id
        
        if job_url:
            # Try to extract job ID from URL
            match = re.search(r'/jobs/view/(\d+)', job_url)
            if match:
                linkedin_job_id = match.group(1)
        
        if not linkedin_job_id:
            return None, False
        
        # Construct LinkedIn URL
        job_url = f"https://www.linkedin.com/jobs/view/{linkedin_job_id}"
        
        # Create cache key for single job
        cache_key = {
            'single_job': True,
            'job_id': linkedin_job_id,
            'fetch_description': fetch_description,
            'description_format': description_format
        }
        
        # Check cache first
        cached_job = cache.get(cache_key)
        if cached_job is not None:
            logger.info(f"Returning cached job for ID {linkedin_job_id}")
            return cached_job, True
        
        try:
            logger.info(f"Fetching job {linkedin_job_id} from LinkedIn")
            
            # Use requests to fetch the LinkedIn job page
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(job_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Parse the HTML to find job details
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # LinkedIn embeds JSON-LD structured data in the page
            script_tags = soup.find_all('script', type='application/ld+json')
            
            job_record = None
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    
                    # Look for JobPosting schema
                    if isinstance(data, dict) and data.get('@type') == 'JobPosting':
                        job_record = {
                            'job_id': linkedin_job_id,
                            'site': 'linkedin',
                            'job_url': job_url,
                            'title': data.get('title', ''),
                            'company': data.get('hiringOrganization', {}).get('name', '') if isinstance(data.get('hiringOrganization'), dict) else '',
                            'location': data.get('jobLocation', {}).get('address', {}).get('addressLocality', '') if isinstance(data.get('jobLocation'), dict) else '',
                            'description': data.get('description', '') if fetch_description else '',
                            'date_posted': data.get('datePosted', ''),
                            'employment_type': data.get('employmentType', ''),
                        }
                        
                        if job_record['company'] and job_record['title']:
                            logger.info(f"Found job posting in JSON-LD: {job_record['title']} at {job_record['company']}")
                            break
                except (json.JSONDecodeError, AttributeError, TypeError):
                    continue
            
            # If we didn't find job data in JSON-LD, try to scrape from the page HTML
            if not job_record:
                logger.info(f"JSON-LD data not found, attempting HTML scraping for job {linkedin_job_id}")
                
                # Try to find job title
                title_elem = soup.find('h1') or soup.find('h2', class_='jobs-details-main-content__job-title')
                title = title_elem.text.strip() if title_elem else ''
                
                # Try to find company name
                company_elem = soup.find('a', {'data-tracking-control-name': 'public_jobs_topcard-org-name'})
                company = company_elem.text.strip() if company_elem else ''
                
                # Try to find location
                location_elem = soup.find('span', class_='job-details-jobs-details-top-card__job-info-item-label')
                location = location_elem.text.strip() if location_elem else ''
                
                # Get description if available
                description_elem = soup.find('div', class_='show-more-less-html__markup')
                description = description_elem.get_text() if description_elem else ''
                
                if title and company:
                    job_record = {
                        'job_id': linkedin_job_id,
                        'site': 'linkedin',
                        'job_url': job_url,
                        'title': title,
                        'company': company,
                        'location': location,
                        'description': description if fetch_description else '',
                    }
            
            if job_record:
                # Cache the result
                cache.set(cache_key, job_record)
                logger.info(f"Successfully fetched job {linkedin_job_id}")
                return job_record, False
            
            logger.warning(f"Could not parse job data for ID {linkedin_job_id}")
            return None, False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error fetching job {linkedin_job_id}: {str(e)}")
            return None, False
        except Exception as e:
            logger.error(f"Error fetching job {linkedin_job_id}: {str(e)}")
            raise