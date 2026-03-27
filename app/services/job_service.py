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
        Fetch a single LinkedIn job by extracting data from LinkedIn's guest job posting API.
        
        Uses the public endpoint: /jobs-guest/jobs/api/jobPosting/{JOB_ID}
        which returns parseable HTML with job details.
        
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
            match = re.search(r'/jobs/view/(\d+)', job_url)
            if match:
                linkedin_job_id = match.group(1)
        
        if not linkedin_job_id:
            return None, False
        
        # Create cache key
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
            # Use LinkedIn's public guest job posting API
            api_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{linkedin_job_id}"
            job_view_url = f"https://www.linkedin.com/jobs/view/{linkedin_job_id}"
            
            logger.info(f"Fetching job {linkedin_job_id} from LinkedIn guest API: {api_url}")
            
            headers = {
                'authority': 'www.linkedin.com',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'accept-language': 'en-US,en;q=0.9',
                'cache-control': 'max-age=0',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
            
            response = requests.get(api_url, headers=headers, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract job title
            title = None
            title_elem = soup.find('h2', class_='top-card-layout__title')
            if title_elem:
                title = title_elem.get_text(strip=True)
            else:
                title_elem = soup.find(class_='topcard__title')
                if title_elem:
                    title = title_elem.get_text(strip=True)
            
            # Extract company name
            company = None
            company_elem = soup.find('a', class_='topcard__org-name-link')
            if company_elem:
                company = company_elem.get_text(strip=True)
            else:
                company_elem = soup.find(class_='topcard__org-name')
                if company_elem:
                    company = company_elem.get_text(strip=True)
            
            # Extract location
            location = None
            location_elem = soup.find('span', class_='topcard__flavor--bullet')
            if location_elem:
                location = location_elem.get_text(strip=True)
            else:
                # Try all topcard__flavor spans
                flavors = soup.find_all('span', class_='topcard__flavor')
                for flavor in flavors:
                    text = flavor.get_text(strip=True)
                    # Location usually contains a comma or known location patterns
                    if ',' in text or any(word in text.lower() for word in ['remote', 'hybrid', 'united', 'london', 'new york']):
                        location = text
                        break
            
            # Extract description
            description = ''
            if fetch_description:
                desc_elem = soup.find('div', class_='show-more-less-html__markup')
                if desc_elem:
                    if description_format == 'html':
                        description = str(desc_elem)
                    else:
                        description = desc_elem.get_text(separator='\n', strip=True)
            
            # Extract job criteria (employment type, seniority, industry, function)
            job_type = None
            seniority_level = None
            industries = None
            job_function = None
            
            criteria_items = soup.find_all('li', class_='description__job-criteria-item')
            for item in criteria_items:
                header = item.find('h3', class_='description__job-criteria-subheader')
                value = item.find('span', class_='description__job-criteria-text')
                if header and value:
                    header_text = header.get_text(strip=True).lower()
                    value_text = value.get_text(strip=True)
                    if 'seniority' in header_text:
                        seniority_level = value_text
                    elif 'employment' in header_text:
                        job_type = value_text
                    elif 'industr' in header_text:
                        industries = value_text
                    elif 'function' in header_text:
                        job_function = value_text
            
            # Extract posted time / number of applicants
            posted_time = None
            num_applicants = None
            flavors = soup.find_all('span', class_='topcard__flavor--metadata')
            for flavor in flavors:
                text = flavor.get_text(strip=True)
                if 'ago' in text.lower() or 'reposted' in text.lower():
                    posted_time = text
                elif 'applicant' in text.lower() or 'click' in text.lower():
                    num_applicants = text
            
            # Extract company logo
            company_logo = None
            logo_elem = soup.find('img', class_='artdeco-entity-image')
            if logo_elem:
                company_logo = logo_elem.get('data-delayed-url') or logo_elem.get('src')
            
            if title or company:
                job_record = {
                    'job_id': linkedin_job_id,
                    'site': 'linkedin',
                    'job_url': job_view_url,
                    'title': title or '',
                    'company': company or '',
                    'location': location or '',
                    'description': description,
                    'job_type': job_type,
                    'seniority_level': seniority_level,
                    'industries': industries,
                    'job_function': job_function,
                    'posted_time': posted_time,
                    'num_applicants': num_applicants,
                    'company_logo': company_logo,
                }
                
                # Remove None values for cleaner output
                job_record = {k: v for k, v in job_record.items() if v is not None}
                
                cache.set(cache_key, job_record)
                logger.info(f"Successfully extracted job {linkedin_job_id}: {title} at {company}")
                return job_record, False
            
            logger.warning(f"Could not extract job data for ID {linkedin_job_id}")
            return None, False
                
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                logger.warning(f"Job {linkedin_job_id} not found on LinkedIn (404)")
            else:
                logger.error(f"HTTP error fetching job {linkedin_job_id}: {str(e)}")
            return None, False
        except Exception as e:
            logger.error(f"Error extracting job {linkedin_job_id}: {str(e)}")
            return None, False