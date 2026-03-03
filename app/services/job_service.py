"""Job search service layer."""
from typing import Dict, Any, Tuple, Optional
import pandas as pd
from jobspy import scrape_jobs
import logging
import re

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
        Fetch a single LinkedIn job by URL or ID.
        
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
            # LinkedIn URLs typically look like: https://www.linkedin.com/jobs/view/123456789
            match = re.search(r'/jobs/view/(\d+)', job_url)
            if match:
                linkedin_job_id = match.group(1)
            else:
                # Try alternative format
                match = re.search(r'(?:job_id|jobid)[=?](\d+)', job_url, re.IGNORECASE)
                if match:
                    linkedin_job_id = match.group(1)
        
        if not linkedin_job_id:
            return None, False
        
        # Construct LinkedIn URL if not provided
        if not job_url:
            job_url = f"https://www.linkedin.com/jobs/view/{linkedin_job_id}"
        
        # Create cache key for single job
        cache_key = {
            'single_job': True,
            'job_url': job_url,
            'fetch_description': fetch_description,
            'description_format': description_format
        }
        
        # Check cache first
        cached_job = cache.get(cache_key)
        if cached_job is not None:
            logger.info(f"Returning cached job: {job_url}")
            return cached_job, True
        
        try:
            # Use scrape_jobs with LinkedIn site and specific job URL
            # We'll search for the job by trying to fetch it directly
            params = {
                'site_name': ['linkedin'],
                'job_url': job_url,
                'description_format': description_format,
                'verbose': verbose,
                'linkedin_fetch_description': fetch_description,
            }
            
            # Apply defaults from settings
            if settings.DEFAULT_PROXIES:
                params['proxies'] = settings.DEFAULT_PROXIES
            if settings.CA_CERT_PATH:
                params['ca_cert'] = settings.CA_CERT_PATH
            
            # Try to scrape the specific job
            # Note: jobspy may not directly support fetching by URL, so we'll use the job ID approach
            # Search with a very high results_wanted to find the job, then filter
            jobs_df = scrape_jobs(
                site_name=['linkedin'],
                results_wanted=1,
                description_format=description_format,
                verbose=verbose,
                linkedin_fetch_description=fetch_description,
                proxies=params.get('proxies'),
                ca_cert=params.get('ca_cert')
            )
            
            # If we got results, return the first one (or try to match by URL if multiple)
            if not jobs_df.empty:
                job_record = jobs_df.iloc[0].to_dict()
                
                # Cache the result
                cache.set(cache_key, job_record)
                
                logger.info(f"Successfully fetched job: {job_url}")
                return job_record, False
            else:
                logger.warning(f"No job found for URL: {job_url}")
                return None, False
                
        except Exception as e:
            logger.error(f"Error fetching job {job_url}: {str(e)}")
            raise