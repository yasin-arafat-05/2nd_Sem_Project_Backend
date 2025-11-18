"""
============================ Facebook Posting Control ===============================
"""
import logging
import datetime
import facebook as fb
from sqlalchemy import select
from eApp.config import CONFIG
from sqlalchemy.pool import NullPool
from typing import Optional, Dict, Any
from eApp.models import SocialMediaToken
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker


logger = logging.getLogger(__name__)


class SocialMediaService:
    @staticmethod
    async def get_user_token(user_id: int, platform: str) -> Optional[str]:
        """
        Args:
            user_id: User ID
            platform: Social media platform (facebook, instagram, linkedin)
        Returns:
            Token string if valid, None if not found/expired
        """
        print("1")
        # Create an event-loop-local engine/session to avoid cross-loop issues in Celery
        engine = create_async_engine(
            CONFIG.DATABASE_URL,
            poolclass=NullPool,
            echo=False,
        )
        print("2")
        session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
        print("3")
        try:
            print("4")
            async with session_maker() as session:
                print("5")
                result = await session.execute(select(SocialMediaToken).where(SocialMediaToken.user_id == user_id))
                print("6")
                token_record = result.scalar_one_or_none()
                print("7")
                if not token_record:
                    print("8")
                    print(f"No token record found for user {user_id}")
                    return None

                print("9")
                # Get platform-specific token
                token = getattr(token_record, platform, None)
                print("10")
                if not token:
                    print("11")
                    print(f"No {platform} token found for user {user_id}")
                    return None

                print("12")
                # Check token expiration
                print(token_record.expires_at)
                print(datetime.datetime.now(datetime.timezone.utc))
                if  token_record.expires_at < datetime.datetime.now(datetime.timezone.utc):
                    print("13")
                    print(f"{platform} token expired for user {user_id}")
                    return None

                print("14")
                logger.info(f"Valid {platform} token found for user {user_id}")
                return token
        except Exception as e:
            print(e)
            logger.error(f"Error getting {platform} token for user {user_id}: {e}")
            return None
        finally:
            # Ensure engine is properly disposed per task
            try:
                await engine.dispose()
            except Exception:
                pass
    
    @staticmethod
    def create_facebook_graph_object(access_token: str) -> fb.GraphAPI:
        """Create Facebook Graph API object with error handling"""
        try:
            return fb.GraphAPI(access_token=access_token)
        except Exception as e:
            logger.error(f"Error creating Facebook Graph object: {e}")
            raise
    
    @staticmethod
    async def post_to_facebook_text(user_id: int, content: str) -> Dict[str, Any]:
        """
        Post text content to Facebook with production-level error handling
        Args:
            user_id: User ID
            content: Text content to post
            
        Returns:
            Dict with status and result information
        """
        try:
            print(f"Starting Facebook text post for user {user_id}")
            
            print("1")
            # Get Facebook token
            access_token = await SocialMediaService.get_user_token(user_id, 'facebook')
            print(access_token)
            print("2")
            if not access_token:
                print("2")
                return {
                    "status": "error",
                    "message": "Facebook token not found or expired. Please update your Facebook token.",
                    "error_code": "TOKEN_NOT_FOUND"
                }
            
            # Create Facebook Graph object
            graph_obj = SocialMediaService.create_facebook_graph_object(access_token)
            
            # Post to Facebook
            result = graph_obj.put_object("me", "feed", message=content)
            
            if result.get("id"):
                logger.info(f"Facebook post successful for user {user_id}, post_id: {result['id']}")
                return {
                    "status": "success",
                    "message": "Post created successfully",
                    "post_id": result["id"],
                    "platform": "facebook"
                }
            else:
                logger.error(f"Facebook post failed for user {user_id}: No post ID returned")
                return {
                    "status": "error",
                    "message": "Failed to create Facebook post - no post ID returned",
                    "error_code": "POST_FAILED"
                }
                
        except fb.GraphAPIError as e:
            error_msg = f"Facebook API error: {str(e)}"
            logger.error(f"Facebook API error for user {user_id}: {error_msg}")
            return {
                "status": "error",
                "message": f"Facebook API error: {str(e)}",
                "error_code": "FACEBOOK_API_ERROR"
            }
        except Exception as e:
            error_msg = f"Unexpected error while posting to Facebook: {str(e)}"
            logger.error(f"Unexpected error for user {user_id}: {error_msg}")
            return {
                "status": "error",
                "message": error_msg,
                "error_code": "UNEXPECTED_ERROR"
            }
    
    @staticmethod
    async def post_to_facebook_photo(user_id: int, content: str, photo_path: str) -> Dict[str, Any]:
        """Post photo with text to Facebook"""
        try:
            logger.info(f"Starting Facebook photo post for user {user_id}")
            
            access_token = await SocialMediaService.get_user_token(user_id, 'facebook')
            if not access_token:
                return {
                    "status": "error",
                    "message": "Facebook token not found or expired",
                    "error_code": "TOKEN_NOT_FOUND"
                }
            
            graph_obj = SocialMediaService.create_facebook_graph_object(access_token)
            
            with open(photo_path, "rb") as photo_file:
                result = graph_obj.put_photo(photo_file, message=content)
            
            if result.get("id"):
                logger.info(f"Facebook photo post successful for user {user_id}")
                return {
                    "status": "success",
                    "message": "Photo post created successfully",
                    "post_id": result["id"],
                    "platform": "facebook"
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to create Facebook photo post",
                    "error_code": "POST_FAILED"
                }
                
        except Exception as e:
            error_msg = f"Error posting photo to Facebook: {str(e)}"
            logger.error(f"Photo post error for user {user_id}: {error_msg}")
            return {
                "status": "error",
                "message": error_msg,
                "error_code": "UNEXPECTED_ERROR"
            }
    
    @staticmethod
    async def post_to_facebook_video(user_id: int, content: str, video_path: str) -> Dict[str, Any]:
        """Post video with text to Facebook"""
        try:
            logger.info(f"Starting Facebook video post for user {user_id}")
            
            access_token = await SocialMediaService.get_user_token(user_id, 'facebook')
            if not access_token:
                return {
                    "status": "error",
                    "message": "Facebook token not found or expired",
                    "error_code": "TOKEN_NOT_FOUND"
                }
            
            graph_obj = SocialMediaService.create_facebook_graph_object(access_token)
            
            with open(video_path, "rb") as video_file:
                result = graph_obj.put_video(video_file, description=content)
            
            if result.get("id"):
                logger.info(f"Facebook video post successful for user {user_id}")
                return {
                    "status": "success",
                    "message": "Video post created successfully",
                    "post_id": result["id"],
                    "platform": "facebook"
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to create Facebook video post",
                    "error_code": "POST_FAILED"
                }
                
        except Exception as e:
            error_msg = f"Error posting video to Facebook: {str(e)}"
            logger.error(f"Video post error for user {user_id}: {error_msg}")
            return {
                "status": "error",
                "message": error_msg,
                "error_code": "UNEXPECTED_ERROR"
            }
    
    @staticmethod
    async def validate_token(user_id: int, platform: str) -> Dict[str, Any]:
        """
        Validate if user has a valid token for the platform
        
        Returns:
            Dict with validation status
        """
        try:
            token = await SocialMediaService.get_user_token(user_id, platform)
            
            if token:
                return {
                    "status": "valid",
                    "message": f"Valid {platform} token found",
                    "has_token": True
                }
            else:
                return {
                    "status": "invalid",
                    "message": f"No valid {platform} token found",
                    "has_token": False
                }
                
        except Exception as e:
            logger.error(f"Error validating {platform} token for user {user_id}: {e}")
            return {
                "status": "error",
                "message": f"Error validating {platform} token",
                "has_token": False
            }
            
            