import httpx
from typing import Dict, Any, Optional
from app.log import logger
from app.controllers.system import config_controller  # 导入config_controller


class ExternalApiService:
    def __init__(self):
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=10.0)  # 设置一个合理的超时时间
        return self._http_client

    async def _close_http_client(self):
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def trigger_node_red_flow(self, flow_path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        触发Node-RED中的某个流程。
        :param flow_path: Node-RED中API的路径，例如 "/flow_trigger_device_reboot"
        :param payload: 发送到Node-RED流程的JSON数据
        :return: Node-RED API的响应
        """
        node_red_base_url = config_controller.get_cached_config("NODE_RED_API_BASE_URL")
        if not node_red_base_url:
            logger.error("NODE_RED_API_BASE_URL not configured in system settings.")
            raise ValueError("Node-RED API基础URL未配置")

        url = f"{node_red_base_url}{flow_path}"
        http_client = await self._get_http_client()

        try:
            logger.info(f"Triggering Node-RED flow: {url} with payload: {payload}")
            response = await http_client.post(url, json=payload)
            response.raise_for_status()  # 抛出 HTTPStatusError 如果状态码是 4xx 或 5xx
            logger.info(f"Node-RED flow triggered successfully. Response: {response.json()}")
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Error connecting to Node-RED at {e.request.url!r}: {e}")
            raise HTTPException(status_code=500, detail=f"无法连接到Node-RED服务: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Node-RED returned error {e.response.status_code} for {e.request.url!r}: {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail=f"Node-RED服务错误: {e.response.text}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while triggering Node-RED flow: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"触发Node-RED流程时发生未知错误: {e}")


external_api_service = ExternalApiService()


# 在应用关闭时关闭 httpx 客户端
async def shutdown_external_api_service():
    await external_api_service._close_http_client()
