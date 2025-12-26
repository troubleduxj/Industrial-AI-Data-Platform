from fastapi import APIRouter, Query
from fastapi.responses import Response
from app.utils.avatar_generator import generate_avatar_svg

router = APIRouter()


@router.get("/generate/{username}", summary="生成用户头像")
async def generate_user_avatar(
    username: str,
    size: int = Query(100, description="头像尺寸", ge=50, le=500)
):
    """
    根据用户名生成 SVG 头像
    
    Args:
        username: 用户名
        size: 头像尺寸（50-500像素）
        
    Returns:
        SVG 格式的头像
    """
    svg_content = generate_avatar_svg(username, size)
    
    return Response(
        content=svg_content,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "public, max-age=86400",  # 缓存24小时
            "Content-Disposition": f"inline; filename=avatar_{username}.svg"
        }
    )