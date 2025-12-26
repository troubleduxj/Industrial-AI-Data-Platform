from fastapi.routing import APIRoute

from app.core.crud import CRUDBase
from app.log import logger
from app.models.admin import SysApiEndpoint as Api
from app.schemas.apis import ApiCreate, ApiUpdate
from app.core.permission_decorators import api_permission_change_event


class ApiController(CRUDBase[Api, ApiCreate, ApiUpdate]):
    def __init__(self):
        super().__init__(model=Api)

    @api_permission_change_event
    async def refresh_api(self):
        from app import app

        # 删除废弃API数据
        all_api_list = []
        for route in app.routes:
            # 只更新有鉴权的API
            if isinstance(route, APIRoute) and len(route.dependencies) > 0:
                all_api_list.append((list(route.methods)[0], route.path_format))
        delete_api = []
        for api in await Api.all():
            if (api.http_method, api.api_path) not in all_api_list:
                delete_api.append((api.http_method, api.api_path))
        for item in delete_api:
            method, path = item
            logger.debug(f"API Deleted {method} {path}")
            await Api.filter(http_method=method, api_path=path).delete()

        for route in app.routes:
            if isinstance(route, APIRoute) and len(route.dependencies) > 0:
                method = list(route.methods)[0]
                path = route.path_format
                summary = route.summary
                tags = list(route.tags)[0] if route.tags else "未分类"
                api_obj = await Api.filter(http_method=method, api_path=path).first()
                if api_obj:
                    await api_obj.update_from_dict(dict(http_method=method, api_path=path, summary=summary, tags=tags)).save()
                else:
                    logger.debug(f"API Created {method} {path}")
                    await Api.create(http_method=method, api_path=path, summary=summary, tags=tags)


api_controller = ApiController()
