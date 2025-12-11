import logging
import httpx
from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID
from fastapi import HTTPException, status
from config.settings import settings
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ServiceResponse:
    """Response from atomic service including data, status code, and headers"""
    data: Dict[str, Any]
    status_code: int
    headers: Dict[str, str]


class ServiceClient:
    """HTTP client for making requests to atomic microservices"""
    
    def __init__(self, base_url: str, service_name: str):
        self.base_url = base_url.rstrip("/")
        self.service_name = service_name
        self.timeout = settings.REQUEST_TIMEOUT
    
    def _extract_response_headers(self, response: httpx.Response) -> Dict[str, str]:
        """Extract relevant response headers to forward"""
        headers_to_forward = [
            "ETag", "Cache-Control", "Last-Modified", 
            "Content-Type", "Location"
        ]
        extracted = {}
        for header in headers_to_forward:
            if header in response.headers:
                extracted[header] = response.headers[header]
        return extracted
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> ServiceResponse:
        """Make HTTP request to atomic service and return response with headers"""
        url = f"{self.base_url}{endpoint}"
        
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)
        
        try:
            logger.info(f"[{self.service_name}] {method} {url}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers=request_headers
                )
                
                logger.info(
                    f"[{self.service_name}] {method} {url} - "
                    f"Status: {response.status_code}"
                )
                
                # Extract response headers before raising for status
                response_headers = self._extract_response_headers(response)
                
                # Handle 304 Not Modified specially
                if response.status_code == 304:
                    return ServiceResponse(
                        data={},
                        status_code=304,
                        headers=response_headers
                    )
                
                response.raise_for_status()
                
                # Parse response data
                if response.status_code == 204:  # No content
                    response_data = {}
                else:
                    try:
                        response_data = response.json()
                    except Exception:
                        response_data = {}
                
                return ServiceResponse(
                    data=response_data,
                    status_code=response.status_code,
                    headers=response_headers
                )
                
        except httpx.TimeoutException:
            logger.error(f"[{self.service_name}] Request timeout: {method} {url}")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Service {self.service_name} timeout"
            )
        except httpx.HTTPStatusError as e:
            logger.error(
                f"[{self.service_name}] HTTP error {e.response.status_code}: {e.response.text}"
            )
            # Extract headers even from error responses
            response_headers = self._extract_response_headers(e.response)
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error from {self.service_name}: {e.response.text}",
                headers=response_headers
            )
        except Exception as e:
            logger.error(f"[{self.service_name}] Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error communicating with {self.service_name}: {str(e)}"
            )
    
    async def get(
        self, 
        endpoint: str, 
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> ServiceResponse:
        """GET request"""
        return await self._make_request("GET", endpoint, params=params, headers=headers)
    
    async def post(
        self, 
        endpoint: str, 
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> ServiceResponse:
        """POST request"""
        return await self._make_request("POST", endpoint, json_data=json_data, params=params, headers=headers)
    
    async def put(
        self,
        endpoint: str,
        json_data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> ServiceResponse:
        """PUT request"""
        return await self._make_request("PUT", endpoint, json_data=json_data, headers=headers)
    
    async def patch(
        self,
        endpoint: str,
        json_data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> ServiceResponse:
        """PATCH request"""
        return await self._make_request("PATCH", endpoint, json_data=json_data, headers=headers)
    
    async def delete(
        self, 
        endpoint: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> ServiceResponse:
        """DELETE request"""
        return await self._make_request("DELETE", endpoint, params=params, headers=headers)


# Service client instances
integrations_client = ServiceClient(
    settings.INTEGRATIONS_SERVICE_URL,
    "Integrations-Service"
)

actions_client = ServiceClient(
    settings.ACTIONS_SERVICE_URL,
    "Actions-Service"
)

classification_client = ServiceClient(
    settings.CLASSIFICATION_SERVICE_URL,
    "Classification-Service"
)

