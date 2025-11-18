import datetime
from datetime import timedelta
import facebook as fb
from typing import Optional
from sqlalchemy.sql import select
from typing import Annotated, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status


from eApp.models import User,SocialMediaToken
from eApp.database import asyncSession
from eApp.passHasing import get_current_user
from eApp.services.social_media_service import SocialMediaService
from eApp.schemas import (
    TokenCreate, TokenUpdate, TokenResponse, 
    FacebookTextPost, FacebookPhotoPost, FacebookVideoPost
)

router = APIRouter(tags=["Social Media"])

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with asyncSession() as session:
        try: 
            yield session
        finally:
            await session.close()
        

# ================================ Helper Functions ========================================
def create_facebook_graph_object(access_token: str):
    """Create Facebook Graph API object"""
    return fb.GraphAPI(access_token=access_token)

async def get_specific_token(user_id: int, platform: str) -> Optional[str]:
    """Legacy function - use SocialMediaService.get_user_token instead"""
    return await SocialMediaService.get_user_token(user_id, platform)




# ============================ Get All Tokens ============================
@router.get("/get/tokens", response_model=TokenResponse)
async def get_social_media_tokens(
    user: Annotated[User, Depends(get_current_user)],db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        result = await db.execute(
            select(SocialMediaToken).where(SocialMediaToken.user_id == user.id)
        )
        tokens = result.scalar_one_or_none()
        print(user.id)
        if not tokens:
            return TokenResponse(
                id=None,
                facebook=None,
                instagram=None,
                linkedin=None,
                expires_at=None,
                created_at=datetime.datetime.now(datetime.timezone.utc)
            )
        
        return tokens
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving tokens: {str(e)}"
        )



# =========================== create/Update Tokens ===========================
@router.post("/create/tokens", response_model=TokenResponse)
async def save_social_media_tokens(
    token_data: TokenCreate, user: Annotated[User, Depends(get_current_user)],db: Annotated[AsyncSession, Depends(get_db)]):

    try:
        result = await db.execute(
            select(SocialMediaToken).where(SocialMediaToken.user_id == user.id)
        )
        token_record = result.scalar_one_or_none()
        expires_in_one_hour = datetime.datetime.now(datetime.timezone.utc) + timedelta(hours=1)
        # if token exist: Update existing tokens
        if token_record:
            if token_data.facebook is not None:
                token_record.facebook = token_data.facebook
            if token_data.instagram is not None:
                token_record.instragram = token_data.instagram  
            if token_data.linkedin is not None:
                token_record.linkedin = token_data.linkedin
            if token_data.expires_at is not None:
                token_record.expires_at = token_data.expires_at + timedelta(hours=1)
            token_record.expires_at = expires_in_one_hour
        else:
            # Create new token record
            token_record = SocialMediaToken(
                user_id=user.id,
                facebook=token_data.facebook,
                instragram=token_data.instagram,
                linkedin=token_data.linkedin,
                expires_at=expires_in_one_hour
            )
            db.add(token_record)
        
        await db.commit()
        return token_record
            
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving tokens: {str(e)}"
        )
        
        
        

# ========================================== Update Specific Tokens==========================================
@router.patch("/update/tokens", response_model=TokenResponse)
async def update_social_media_tokens(
    token_data: TokenUpdate,user: Annotated[User, Depends(get_current_user)],db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        # Check if token record exists
        result = await db.execute(
            select(SocialMediaToken).where(SocialMediaToken.user_id == user.id)
        )
        token_record = result.scalar_one_or_none()
        
        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No tokens found for user. Please save tokens first."
            )
        # Update only provided fields
        if token_data.facebook is not None:
            token_record.facebook = token_data.facebook
        if token_data.instagram is not None:
            token_record.instragram = token_data.instagram  
        if token_data.linkedin is not None:
            token_record.linkedin = token_data.linkedin
        if token_data.expires_at is not None:
            token_record.expires_at = token_data.expires_at
        await db.commit()
        return token_record
            
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating tokens: {str(e)}"
        )


# ======================================= Get Specific Platform Token ======================================
@router.get("/tokens/{platform}")
async def get_platform_token(
    platform: str, user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    """Get and validate platform token - Production endpoint"""
    try:
        valid_platforms = ['facebook', 'instagram', 'linkedin']
        if platform not in valid_platforms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid platform. Must be one of: {valid_platforms}"
            )
        
        # Use the service layer for token validation
        result = await SocialMediaService.validate_token(user.id, platform)
        return {
            "status": "success",
            "platform": platform,
            "has_token": result["has_token"],
            "message": result["message"]
        }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving {platform} token: {str(e)}"
        )
        

# <------------------------------ Delete Tokens ------------------------------>
@router.delete("/tokens/{platform}")
async def delete_platform_token(
    platform: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Delete token for specific platform"""
    try:
        valid_platforms = ['facebook', 'instagram', 'linkedin']
        if platform not in valid_platforms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid platform. Must be one of: {valid_platforms}"
            )
        
        result = await db.execute(
            select(SocialMediaToken).where(SocialMediaToken.user_id == user.id)
        )
        token_record = result.scalar_one_or_none()
        
        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No tokens found for user"
            )
        
        # Set the specific platform token to None
        if platform == 'instagram':
            setattr(token_record, 'instragram', None) 
        else:
            setattr(token_record, platform, None)
        await db.commit()
        
        return {
            "status": "success",
            "message": f"{platform.capitalize()} token deleted successfully"
        }
            
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting {platform} token: {str(e)}"
        )
        
        
        

# =================================== Facebook Posting Endpoints =======================================
@router.post("/facebook/post/text")
async def post_facebook_text(post_data: FacebookTextPost):
    """Post only text to Facebook - Production endpoint"""
    user_id = post_data.current_user_id
    print("<---------Facebook Post Only Text Endpoint(1) -------->")
    print("post_data", post_data)
    print("generate content: ", post_data.generate_content)
    print("user_id", user_id)
    print("<---------Facebook Post Only Text Endpoint(2) -------->")
    
    try:
        # Use the service layer for production-level posting
        result = await SocialMediaService.post_to_facebook_text(
            user_id=user_id,
            content=post_data.generate_content
        )
        
        if result["status"] == "success":
            return result
        else:
            # Handle different error types
            if result["error_code"] == "TOKEN_NOT_FOUND":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result["message"]
                )
            elif result["error_code"] == "FACEBOOK_API_ERROR":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result["message"]
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result["message"]
                )
                
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Unexpected error while posting to Facebook: {str(e)}"
        print(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )

@router.post("/facebook/post/photo")
async def post_facebook_photo(
    post_data: FacebookPhotoPost,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Post text with photo to Facebook"""
    try:
        access_token = await get_specific_token(db, user.id, 'facebook')
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Facebook token not found or expired. Please save your Facebook token first."
            )
        
        graph_obj = create_facebook_graph_object(access_token)
        
        result = graph_obj.put_photo(
            open(post_data.photo_url, "rb"),
            message=post_data.text
        )
        
        if result.get("id"):
            return {
                "status": "success",
                "message": "Photo post created successfully",
                "post_id": result["id"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create Facebook photo post"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error while posting photo to Facebook: {str(e)}"
        print(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )

@router.post("/facebook/post/video")
async def post_facebook_video(
    post_data: FacebookVideoPost,user: Annotated[User, Depends(get_current_user)],db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        access_token = await get_specific_token(db, user.id, 'facebook')
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Facebook token not found or expired. Please save your Facebook token first."
            )
        
        graph_obj = create_facebook_graph_object(access_token)
        
        result = graph_obj.put_video(
            open(post_data.video_url, "rb"),
            description=post_data.text
        )
        
        if result.get("id"):
            return {
                "status": "success",
                "message": "Video post created successfully",
                "post_id": result["id"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create Facebook video post"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error while posting video to Facebook: {str(e)}"
        print(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )





        
        