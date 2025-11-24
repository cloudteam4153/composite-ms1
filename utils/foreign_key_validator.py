import logging
from typing import Optional, Dict, Any
from uuid import UUID
from fastapi import HTTPException, status
from utils.service_client import (
    integrations_client,
    actions_client,
    classification_client
)

logger = logging.getLogger(__name__)


class ForeignKeyValidator:
    """Validates logical foreign key relationships across microservices"""
    
    @staticmethod
    async def validate_user_exists(user_id: UUID) -> bool:
        """Validate that a user exists in the integrations service"""
        try:
            # This would check against the users endpoint in integrations service
            # For now, we'll assume users are validated through session/auth
            return True
        except Exception as e:
            logger.error(f"Failed to validate user {user_id}: {str(e)}")
            return False
    
    @staticmethod
    async def validate_connection_exists(connection_id: UUID, user_id: UUID) -> bool:
        """Validate that a connection exists and belongs to the user"""
        try:
            response = await integrations_client.get(f"/connections/{connection_id}")
            return response.get("user_id") == str(user_id)
        except HTTPException as e:
            if e.status_code == 404:
                return False
            raise
        except Exception as e:
            logger.error(f"Failed to validate connection {connection_id}: {str(e)}")
            return False
    
    @staticmethod
    async def validate_message_exists(message_id: UUID, user_id: UUID) -> bool:
        """Validate that a message exists and belongs to the user"""
        try:
            response = await integrations_client.get(f"/messages/{message_id}")
            return response.get("user_id") == str(user_id)
        except HTTPException as e:
            if e.status_code == 404:
                return False
            raise
        except Exception as e:
            logger.error(f"Failed to validate message {message_id}: {str(e)}")
            return False
    
    @staticmethod
    async def validate_classification_exists(classification_id: UUID) -> bool:
        """Validate that a classification exists"""
        try:
            await classification_client.get(f"/classifications/{classification_id}")
            return True
        except HTTPException as e:
            if e.status_code == 404:
                return False
            raise
        except Exception as e:
            logger.error(f"Failed to validate classification {classification_id}: {str(e)}")
            return False
    
    @staticmethod
    async def validate_task_exists(task_id: int, user_id: Optional[int] = None) -> bool:
        """Validate that a task exists (in either actions or classification service)"""
        try:
            # Check in actions service
            await actions_client.get(f"/tasks/{task_id}")
            return True
        except HTTPException as e:
            if e.status_code == 404:
                # Try classification service
                try:
                    await classification_client.get(f"/tasks/{task_id}")
                    return True
                except HTTPException:
                    return False
            raise
        except Exception as e:
            logger.error(f"Failed to validate task {task_id}: {str(e)}")
            return False
    
    @staticmethod
    async def validate_relationships(
        message_id: Optional[UUID] = None,
        connection_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        classification_id: Optional[UUID] = None
    ) -> None:
        """
        Validate multiple relationships at once
        
        Raises HTTPException if any relationship is invalid
        """
        if connection_id and user_id:
            exists = await ForeignKeyValidator.validate_connection_exists(
                connection_id, user_id
            )
            if not exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Connection {connection_id} not found or does not belong to user"
                )
        
        if message_id and user_id:
            exists = await ForeignKeyValidator.validate_message_exists(
                message_id, user_id
            )
            if not exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Message {message_id} not found or does not belong to user"
                )
        
        if classification_id:
            exists = await ForeignKeyValidator.validate_classification_exists(
                classification_id
            )
            if not exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Classification {classification_id} not found"
                )

