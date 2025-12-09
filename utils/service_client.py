import logging
import httpx
from typing import Optional, Dict, Any, List
from uuid import UUID
from fastapi import HTTPException, status
from config.settings import settings

logger = logging.getLogger(__name__)


class ServiceClient:
    """HTTP client for making requests to atomic microservices"""
    
    def __init__(self, base_url: str, service_name: str):
        self.base_url = base_url.rstrip("/")
        self.service_name = service_name
        self.timeout = settings.REQUEST_TIMEOUT
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to atomic service"""
        # Ensure endpoint has trailing slash for collection endpoints to avoid 307 redirects
        if endpoint in ["/connections", "/messages", "/syncs"] and not endpoint.endswith("/"):
            endpoint = endpoint + "/"
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
                
                response.raise_for_status()
                
                if response.status_code == 204:  # No content
                    return {}
                
                return response.json()
                
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
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error from {self.service_name}: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"[{self.service_name}] Unexpected error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error communicating with {self.service_name}: {str(e)}"
            )
    
    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """GET request"""
        return await self._make_request("GET", endpoint, params=params)
    
    async def post(
        self, 
        endpoint: str, 
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """POST request"""
        return await self._make_request("POST", endpoint, json_data=json_data, params=params)
    
    async def put(
        self,
        endpoint: str,
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """PUT request"""
        return await self._make_request("PUT", endpoint, json_data=json_data)
    
    async def patch(
        self,
        endpoint: str,
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """PATCH request"""
        return await self._make_request("PATCH", endpoint, json_data=json_data)
    
    async def delete(
        self, 
        endpoint: str,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """DELETE request"""
        return await self._make_request("DELETE", endpoint, params=params)


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

