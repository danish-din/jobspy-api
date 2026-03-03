from fastapi import APIRouter, Depends, Query, HTTPException, Request
from typing import List, Optional, Union
import logging
import time
import uuid
import traceback

from app.models import JobSearchParams, JobResponse, PaginatedJobResponse, SingleJobRequest, SingleJobResponse
from app.config import settings
from app.middleware.api_key_auth import get_api_key
from app.services.job_service import JobService
from app.utils.validation_helpers import VALID_PARAMETERS, get_parameter_suggestion, generate_error_suggestions

router = APIRouter()
logger = logging.getLogger(__name__)

SUPPORTED_COUNTRIES_INDEED = {
    "Argentina", "Australia", "Austria", "Bahrain", "Belgium", "Brazil", "Canada", "Chile", "China", "Colombia",
    "Costa Rica", "Czech Republic", "Denmark", "Ecuador", "Egypt", "Finland", "France", "Germany", "Greece",
    "Hong Kong", "Hungary", "India", "Indonesia", "Ireland", "Israel", "Italy", "Japan", "Kuwait", "Luxembourg",
    "Malaysia", "Mexico", "Morocco", "Netherlands", "New Zealand", "Nigeria", "Norway", "Oman", "Pakistan",
    "Panama", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Saudi Arabia", "Singapore",
    "South Africa", "South Korea", "Spain", "Sweden", "Switzerland", "Taiwan", "Thailand", "Turkey", "Ukraine",
    "United Arab Emirates", "UK", "USA", "Uruguay", "Venezuela", "Vietnam"
}

def validate_job_search_params(
    site_name,
    country_indeed,
    hours_old,
    job_type,
    is_remote,
    easy_apply,
    description_format=None,
    verbose=None,
    page=None,
    page_size=None,
    paginate=None,
    endpoint="search_jobs"
):
    # Normalize site names
    snames = [s.lower() for s in site_name] if site_name else []
    # Supported country validation for Indeed/Glassdoor
    if ("indeed" in snames or "glassdoor" in snames):
        if not country_indeed:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Missing required parameter",
                    "parameter": "country_indeed",
                    "message": "country_indeed is required when searching Indeed or Glassdoor.",
                    "suggestion": "Specify a supported country using the country_indeed parameter. See documentation for valid values."
                }
            )
        if country_indeed not in SUPPORTED_COUNTRIES_INDEED:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid country_indeed value",
                    "invalid_value": country_indeed,
                    "valid_countries": sorted(SUPPORTED_COUNTRIES_INDEED),
                    "suggestion": "Use one of the supported country names exactly as listed in the documentation."
                }
            )
    # Parameter conflict logic for Indeed
    if "indeed" in snames:
        conflict_params = []
        if hours_old is not None:
            if (job_type is not None or is_remote is not None) or (easy_apply is not None):
                conflict_params = ["hours_old", "job_type/is_remote", "easy_apply"]
        elif (job_type is not None or is_remote is not None) and easy_apply is not None:
            conflict_params = ["job_type/is_remote", "easy_apply"]
        if conflict_params:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Parameter conflict for Indeed",
                    "conflicting_parameters": conflict_params,
                    "message": (
                        "Indeed searches only support one of the following at a time: "
                        "hours_old, (job_type & is_remote), or easy_apply."
                    ),
                    "suggestion": (
                        "Remove one or more of these parameters so that only one group is used per search. "
                        "See documentation for details."
                    )
                }
            )
    # Parameter conflict logic for LinkedIn
    if "linkedin" in snames:
        if hours_old is not None and easy_apply is not None:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Parameter conflict for LinkedIn",
                    "conflicting_parameters": ["hours_old", "easy_apply"],
                    "message": (
                        "LinkedIn searches only support one of the following at a time: hours_old or easy_apply."
                    ),
                    "suggestion": (
                        "Remove either hours_old or easy_apply from your search parameters."
                    )
                }
            )

    # --- General parameter validation ---
    errors = []
    # site_name
    if site_name:
        for s in site_name:
            if s not in VALID_PARAMETERS["site_name"]:
                errors.append(get_parameter_suggestion("site_name", s))
    # job_type
    if job_type and job_type not in VALID_PARAMETERS["job_type"]:
        errors.append(get_parameter_suggestion("job_type", job_type))
    # description_format
    if description_format and description_format not in VALID_PARAMETERS["description_format"]:
        errors.append(get_parameter_suggestion("description_format", description_format))
    # verbose
    if verbose is not None and verbose not in VALID_PARAMETERS["verbose"]:
        errors.append(get_parameter_suggestion("verbose", verbose))
    # page_size
    if page_size is not None and (page_size < 1 or page_size > 100):
        errors.append(get_parameter_suggestion("page_size", page_size))
    # paginate
    if paginate is not None and paginate not in [True, False, 0, 1]:
        errors.append(get_parameter_suggestion("paginate", paginate))
    # page
    if page is not None and page < 1:
        errors.append(get_parameter_suggestion("page", page))
    # If any errors, raise with all suggestions
    if errors:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid parameter(s)",
                "suggestions": errors,
            }
        )

@router.get("/search_jobs", response_model=Union[JobResponse, PaginatedJobResponse], dependencies=[Depends(get_api_key)])
async def search_jobs(
    request: Request,
    # Pagination parameters
    paginate: bool = Query(False, description="Enable pagination"),
    page: int = Query(1, ge=1, description="Page number (if pagination enabled)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page (if pagination enabled)"),
    
    # Basic search parameters
    site_name: List[str] = Query(default=None, description="Job sites to search on"),
    search_term: str = Query(None, description="Job search term"),
    google_search_term: Optional[str] = Query(None, description="Search term for Google jobs"),
    location: str = Query(None, description="Job location"),
    distance: int = Query(None, description="Distance in miles"),
    
    # Job filters
    job_type: Optional[str] = Query(None, description="Job type (fulltime, parttime, internship, contract)"),
    is_remote: Optional[bool] = Query(None, description="Remote job filter"),
    hours_old: Optional[int] = Query(None, description="Filter by hours since posting"),
    easy_apply: Optional[bool] = Query(None, description="Filter for easy apply jobs"),
    
    # Advanced parameters
    results_wanted: int = Query(None, description="Number of results per site"),
    description_format: str = Query(None, description="Format of job description"),
    offset: int = Query(None, description="Offset for pagination"),
    verbose: int = Query(None, description="Controls verbosity (0: errors only, 1: errors+warnings, 2: all logs)"),
    linkedin_fetch_description: bool = Query(None, description="Fetch full LinkedIn descriptions"),
    linkedin_company_ids: Optional[List[int]] = Query(None, description="LinkedIn company IDs to filter by"),
    country_indeed: Optional[str] = Query(None, description="Country filter for Indeed & Glassdoor"),
    enforce_annual_salary: bool = Query(None, description="Convert wages to annual salary"),
):
    """
    Search for jobs across multiple platforms with optional pagination.
    
    If paginate=True, returns paginated results with next/previous page links.
    Otherwise, returns all results in a single response.
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    validate_job_search_params(
        site_name=site_name,
        country_indeed=country_indeed,
        hours_old=hours_old,
        job_type=job_type,
        is_remote=is_remote,
        easy_apply=easy_apply,
        description_format=description_format,
        verbose=verbose,
        page=page,
        page_size=page_size,
        paginate=paginate,
    )
    
    # Validate site_name values
    if site_name:
        invalid_sites = [site for site in site_name if site not in VALID_PARAMETERS["site_name"]]
        if invalid_sites:
            suggestions = [get_parameter_suggestion("site_name", site) for site in invalid_sites]
            raise HTTPException(
                status_code=400, 
                detail={
                    "error": "Invalid job site name(s)",
                    "invalid_values": invalid_sites,
                    "valid_sites": VALID_PARAMETERS["site_name"],
                    "suggestions": suggestions
                }
            )
    
    # Validate job_type
    if job_type and job_type not in VALID_PARAMETERS["job_type"]:
        suggestion = get_parameter_suggestion("job_type", job_type)
        raise HTTPException(
            status_code=400, 
            detail={
                "error": "Invalid job type",
                "invalid_value": job_type,
                "valid_types": VALID_PARAMETERS["job_type"],
                "suggestion": suggestion
            }
        )
    
    # Validate description_format
    if description_format and description_format not in VALID_PARAMETERS["description_format"]:
        suggestion = get_parameter_suggestion("description_format", description_format)
        raise HTTPException(
            status_code=400, 
            detail={
                "error": "Invalid description format",
                "invalid_value": description_format,
                "valid_formats": VALID_PARAMETERS["description_format"],
                "suggestion": suggestion
            }
        )
    
    # Create parameters object with all search parameters
    params = JobSearchParams(
        site_name=site_name if site_name else settings.DEFAULT_SITE_NAMES,
        search_term=search_term,
        google_search_term=google_search_term,
        location=location,
        distance=distance if distance is not None else settings.DEFAULT_DISTANCE,
        job_type=job_type,
        proxies=settings.DEFAULT_PROXIES if settings.DEFAULT_PROXIES else None,
        is_remote=is_remote,
        results_wanted=results_wanted if results_wanted is not None else settings.DEFAULT_RESULTS_WANTED,
        hours_old=hours_old,
        easy_apply=easy_apply,
        description_format=description_format if description_format else settings.DEFAULT_DESCRIPTION_FORMAT,
        offset=offset if offset is not None else 0,
        verbose=verbose if verbose is not None else 2,
        linkedin_fetch_description=linkedin_fetch_description if linkedin_fetch_description is not None else False,
        linkedin_company_ids=linkedin_company_ids,
        country_indeed=country_indeed if country_indeed else settings.DEFAULT_COUNTRY_INDEED,
        enforce_annual_salary=enforce_annual_salary if enforce_annual_salary is not None else False,
        ca_cert=settings.CA_CERT_PATH,
    )
    
    logger.info(f"Request {request_id}: Starting job search with parameters: {params.dict(exclude_none=True)}")
    
    try:
        # Execute the search
        jobs_df, is_cached = JobService.search_jobs(params.dict(exclude_none=True))
        
        # Return results - either paginated or all at once
        if paginate:
            # Calculate pagination
            total_items = len(jobs_df)
            total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 1
            
            # Validate page number
            if page > total_pages and total_pages > 0:
                raise HTTPException(
                    status_code=404, 
                    detail={
                        "error": f"Page {page} not found",
                        "total_pages": total_pages,
                        "suggestion": f"Use a page number between 1 and {total_pages}"
                    }
                )
            
            # Apply pagination
            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, total_items)
            paginated_df = jobs_df.iloc[start_idx:end_idx] if total_items > 0 else jobs_df
            
            # Generate next/previous page URLs
            base_url = str(request.url).split("?")[0]
            query_params = dict(request.query_params)
            
            next_page = None
            if page < total_pages:
                query_params["page"] = str(page + 1)
                next_page = f"{base_url}?{'&'.join([f'{k}={v}' for k, v in query_params.items()])}"
            
            previous_page = None
            if page > 1:
                query_params["page"] = str(page - 1)
                previous_page = f"{base_url}?{'&'.join([f'{k}={v}' for k, v in query_params.items()])}"
            
            # Convert DataFrame to dictionary format
            jobs_list = paginated_df.to_dict('records') if not paginated_df.empty else []
            
            end_time = time.time()
            logger.info(f"Request {request_id}: Completed in {end_time - start_time:.2f} seconds. Found {total_items} jobs, returning page {page}/{total_pages}")
            
            return {
                "count": total_items,
                "total_pages": total_pages,
                "current_page": page,
                "page_size": page_size,
                "jobs": jobs_list,
                "cached": is_cached,
                "next_page": next_page,
                "previous_page": previous_page
            }
        else:
            # Return all results without pagination
            jobs_list = jobs_df.to_dict('records') if not jobs_df.empty else []
            
            end_time = time.time()
            logger.info(f"Request {request_id}: Completed in {end_time - start_time:.2f} seconds. Found {len(jobs_list)} jobs")
            
            return {
                "count": len(jobs_list),
                "jobs": jobs_list,
                "cached": is_cached
            }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        
        logger.error(f"Request {request_id}: Error scraping jobs: {str(e)}")
        logger.debug(traceback.format_exc())
        
        # Provide more helpful error details
        error_message = str(e)
        suggestion = "Try simplifying your search or using fewer job sites"
        
        if "proxy" in error_message.lower():
            suggestion = "Check your proxy configuration or try without a proxy"
        elif "timeout" in error_message.lower():
            suggestion = "The request timed out. Try reducing the number of job sites or results_wanted"
        elif "captcha" in error_message.lower():
            suggestion = "A CAPTCHA was encountered. Try using a different proxy or reduce request frequency"
        
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "Error scraping jobs",
                "message": error_message,
                "suggestion": suggestion
            }
        )


@router.get("/fetch_job", response_model=SingleJobResponse, dependencies=[Depends(get_api_key)])
async def fetch_job(
    request: Request,
    job_url: Optional[str] = Query(None, description="Full URL to the LinkedIn job posting"),
    job_id: Optional[str] = Query(None, description="LinkedIn job ID (e.g., 123456789)"),
    fetch_description: bool = Query(True, description="Fetch full job description"),
    description_format: str = Query("markdown", description="Format of job description (markdown, html)"),
    verbose: int = Query(2, description="Controls verbosity (0: errors only, 1: errors+warnings, 2: all logs)"),
):
    """
    Fetch a single LinkedIn job by URL or job ID.
    
    You can provide either:
    - `job_url`: Full URL to the LinkedIn job (e.g., https://www.linkedin.com/jobs/view/123456789)
    - `job_id`: Just the LinkedIn job ID (e.g., 123456789)
    
    The endpoint returns the job details in the same format as the search endpoint.
    
    Example usage:
    - GET /api/v1/fetch_job?job_id=123456789
    - GET /api/v1/fetch_job?job_url=https://www.linkedin.com/jobs/view/123456789
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Validate that at least one identifier is provided
    if not job_url and not job_id:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Missing required parameter",
                "message": "Either 'job_url' or 'job_id' must be provided",
                "suggestion": "Provide either a full LinkedIn job URL or just the job ID number"
            }
        )
    
    # Validate description_format
    if description_format not in VALID_PARAMETERS.get("description_format", ["markdown", "html"]):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid description format",
                "invalid_value": description_format,
                "valid_formats": VALID_PARAMETERS.get("description_format", ["markdown", "html"]),
                "suggestion": "Use either 'markdown' or 'html' for the description format"
            }
        )
    
    # Validate verbose
    if verbose not in VALID_PARAMETERS.get("verbose", [0, 1, 2]):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid verbose level",
                "invalid_value": verbose,
                "valid_levels": VALID_PARAMETERS.get("verbose", [0, 1, 2]),
                "suggestion": "Use 0 (errors), 1 (warnings), or 2 (all logs)"
            }
        )
    
    try:
        logger.info(f"Request {request_id}: Fetching single job. URL: {job_url}, ID: {job_id}")
        
        # Fetch the single job
        job, is_cached = JobService.fetch_single_job(
            job_url=job_url,
            job_id=job_id,
            fetch_description=fetch_description,
            description_format=description_format,
            verbose=verbose
        )
        
        end_time = time.time()
        
        if job:
            logger.info(f"Request {request_id}: Successfully fetched job in {end_time - start_time:.2f} seconds")
            return {
                "success": True,
                "job": job,
                "cached": is_cached
            }
        else:
            logger.warning(f"Request {request_id}: Job not found for the provided identifier")
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Job not found",
                    "message": "Could not find the LinkedIn job with the provided URL or ID",
                    "suggestion": "Verify that the job URL or ID is correct and the job still exists on LinkedIn"
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Request {request_id}: Error fetching job: {str(e)}")
        logger.debug(traceback.format_exc())
        
        # Provide more helpful error details
        error_message = str(e)
        suggestion = "Check your job URL or ID and try again"
        
        if "proxy" in error_message.lower():
            suggestion = "Check your proxy configuration or try without a proxy"
        elif "timeout" in error_message.lower():
            suggestion = "The request timed out. Try again or check your internet connection"
        elif "captcha" in error_message.lower():
            suggestion = "A CAPTCHA was encountered. Try using a different proxy or wait before retrying"
        elif "not found" in error_message.lower():
            suggestion = "The job posting may no longer exist. Verify the job URL or ID is correct"
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Error fetching job",
                "message": error_message,
                "suggestion": suggestion
            }
        )


@router.post("/fetch_job", response_model=SingleJobResponse, dependencies=[Depends(get_api_key)])
async def fetch_job_post(
    request: Request,
    params: SingleJobRequest,
):
    """
    Fetch a single LinkedIn job by URL or job ID using POST method.
    
    Accepts a JSON body with the following fields:
    - job_url (optional): Full URL to the LinkedIn job
    - job_id (optional): LinkedIn job ID
    - fetch_description (optional, default=true): Whether to fetch full description
    - description_format (optional, default="markdown"): Format of description (markdown, html)
    - verbose (optional, default=2): Verbosity level (0, 1, or 2)
    
    Example body:
    {
        "job_id": "123456789",
        "fetch_description": true,
        "description_format": "markdown"
    }
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Validate that at least one identifier is provided
    if not params.job_url and not params.job_id:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Missing required parameter",
                "message": "Either 'job_url' or 'job_id' must be provided",
                "suggestion": "Provide either a full LinkedIn job URL or just the job ID number"
            }
        )
    
    # Validate description_format
    if params.description_format not in VALID_PARAMETERS.get("description_format", ["markdown", "html"]):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid description format",
                "invalid_value": params.description_format,
                "valid_formats": VALID_PARAMETERS.get("description_format", ["markdown", "html"]),
                "suggestion": "Use either 'markdown' or 'html' for the description format"
            }
        )
    
    # Validate verbose
    if params.verbose and params.verbose not in VALID_PARAMETERS.get("verbose", [0, 1, 2]):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid verbose level",
                "invalid_value": params.verbose,
                "valid_levels": VALID_PARAMETERS.get("verbose", [0, 1, 2]),
                "suggestion": "Use 0 (errors), 1 (warnings), or 2 (all logs)"
            }
        )
    
    try:
        logger.info(f"Request {request_id}: Fetching single job. URL: {params.job_url}, ID: {params.job_id}")
        
        # Fetch the single job
        job, is_cached = JobService.fetch_single_job(
            job_url=params.job_url,
            job_id=params.job_id,
            fetch_description=params.fetch_description,
            description_format=params.description_format,
            verbose=params.verbose if params.verbose else 2
        )
        
        end_time = time.time()
        
        if job:
            logger.info(f"Request {request_id}: Successfully fetched job in {end_time - start_time:.2f} seconds")
            return {
                "success": True,
                "job": job,
                "cached": is_cached
            }
        else:
            logger.warning(f"Request {request_id}: Job not found for the provided identifier")
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Job not found",
                    "message": "Could not find the LinkedIn job with the provided URL or ID",
                    "suggestion": "Verify that the job URL or ID is correct and the job still exists on LinkedIn"
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Request {request_id}: Error fetching job: {str(e)}")
        logger.debug(traceback.format_exc())
        
        # Provide more helpful error details
        error_message = str(e)
        suggestion = "Check your job URL or ID and try again"
        
        if "proxy" in error_message.lower():
            suggestion = "Check your proxy configuration or try without a proxy"
        elif "timeout" in error_message.lower():
            suggestion = "The request timed out. Try again or check your internet connection"
        elif "captcha" in error_message.lower():
            suggestion = "A CAPTCHA was encountered. Try using a different proxy or wait before retrying"
        elif "not found" in error_message.lower():
            suggestion = "The job posting may no longer exist. Verify the job URL or ID is correct"
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Error fetching job",
                "message": error_message,
                "suggestion": suggestion
            }
        )

@router.post("/search_jobs", response_model=Union[JobResponse, PaginatedJobResponse], dependencies=[Depends(get_api_key)])
async def search_jobs_post(
    params: JobSearchParams,
    request: Request,
):
    """
    Search for jobs across multiple platforms using POST method.
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    validate_job_search_params(
        site_name=params.site_name if isinstance(params.site_name, list) else [params.site_name],
        country_indeed=params.country_indeed,
        hours_old=params.hours_old,
        job_type=params.job_type,
        is_remote=params.is_remote,
        easy_apply=params.easy_apply,
        description_format=params.description_format,
        verbose=params.verbose,
        page=getattr(params, "page", None),
        page_size=getattr(params, "page_size", None),
        paginate=getattr(params, "paginate", None),
    )
    
    logger.info(f"Request {request_id}: Starting job search with parameters: {params.dict(exclude_none=True)}")
    
    try:
        # Execute the search
        jobs_df, is_cached = JobService.search_jobs(params.dict(exclude_none=True))
        
        # Return all results without pagination
        jobs_list = jobs_df.to_dict('records') if not jobs_df.empty else []
        
        end_time = time.time()
        logger.info(f"Request {request_id}: Completed in {end_time - start_time:.2f} seconds. Found {len(jobs_list)} jobs")
        
        return {
            "count": len(jobs_list),
            "jobs": jobs_list,
            "cached": is_cached
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        
        logger.error(f"Request {request_id}: Error scraping jobs: {str(e)}")
        logger.debug(traceback.format_exc())
        
        # Provide more helpful error details
        error_message = str(e)
        suggestion = "Try simplifying your search or using fewer job sites"
        
        if "proxy" in error_message.lower():
            suggestion = "Check your proxy configuration or try without a proxy"
        elif "timeout" in error_message.lower():
            suggestion = "The request timed out. Try reducing the number of job sites or results_wanted"
        elif "captcha" in error_message.lower():
            suggestion = "A CAPTCHA was encountered. Try using a different proxy or reduce request frequency"
        
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "Error scraping jobs",
                "message": error_message,
                "suggestion": suggestion
            }
        )
