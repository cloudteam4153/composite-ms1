"""
Helper utilities for handling responses with headers and status codes
"""
from typing import Union
from fastapi import Request, Response, status
from utils.service_client import ServiceResponse


def forward_request_headers(request: Request) -> dict:
    """Extract and forward relevant request headers (e.g., If-None-Match)"""
    headers = {}
    if "if-none-match" in request.headers:
        headers["If-None-Match"] = request.headers["if-none-match"]
    return headers


def forward_response_headers(service_response: ServiceResponse, response: Response):
    """Forward response headers from atomic service to composite response"""
    for header_name, header_value in service_response.headers.items():
        response.headers[header_name] = header_value


def handle_service_response(
    service_response: ServiceResponse,
    response: Response,
    is_post: bool = False,
    is_async: bool = False
) -> Union[dict, Response]:
    """
    Handle service response with proper status codes and headers
    
    Args:
        service_response: Response from atomic service
        response: FastAPI Response object
        is_post: Whether this is a POST operation (returns 201)
        is_async: Whether this is an async operation (returns 202)
    
    Returns:
        Response data
    """
    # Forward response headers
    forward_response_headers(service_response, response)
    
    # Handle 304 Not Modified
    if service_response.status_code == 304:
        return Response(status_code=304, headers=dict(response.headers))
    
    # Set status code
    if is_async and service_response.status_code == 200:
        response.status_code = status.HTTP_202_ACCEPTED
    elif is_post and service_response.status_code == 200:
        response.status_code = status.HTTP_201_CREATED
    else:
        response.status_code = service_response.status_code
    
    return service_response.data

