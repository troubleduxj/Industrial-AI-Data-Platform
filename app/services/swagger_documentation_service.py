"""
Swagger文档自动生成服务
实现V2 API的Swagger文档自动生成机制，按功能模块组织API文档结构
"""
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute

from app.models.admin import SysApiGroup, SysApiEndpoint
from app.core.response_formatter_v2 import ResponseFormatterV2


class SwaggerDocumentationService:
    """Swagger文档服务"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.base_path = "docs/api-v2"
        self.ensure_docs_directory()
    
    def ensure_docs_directory(self):
        """确保文档目录存在"""
        os.makedirs(self.base_path, exist_ok=True)
        os.makedirs(f"{self.base_path}/modules", exist_ok=True)
        os.makedirs(f"{self.base_path}/schemas", exist_ok=True)
    
    async def generate_v2_documentation(self) -> Dict[str, Any]:
        """生成V2 API完整文档"""
        # 获取基础OpenAPI文档
        base_openapi = get_openapi(
            title="系统管理API v2",
            version="2.0.0",
            description=self._get_api_description(),
            routes=self.app.routes,
            servers=[
                {"url": "http://localhost:8000", "description": "开发环境"},
                {"url": "https://api.devicemonitor.com", "description": "生产环境"}
            ]
        )
        
        # 按功能模块组织API
        organized_docs = await self._organize_by_modules(base_openapi)
        
        # 添加增强的元数据
        organized_docs.update({
            "info": {
                **base_openapi["info"],
                "contact": {
                    "name": "DeviceMonitor API Support",
                    "email": "support@devicemonitor.com"
                },
                "license": {
                    "name": "MIT License",
                    "url": "https://opensource.org/licenses/MIT"
                }
            },
            "externalDocs": {
                "description": "完整API文档",
                "url": "/docs"
            }
        })
        
        return organized_docs
    
    def _get_api_description(self) -> str:
        """获取API描述"""
        return """系统管理API v2

提供完整的系统管理功能，包括用户管理、角色管理、菜单管理、部门管理等核心功能。

## 特性

• 标准化响应格式: 所有API使用统一的v2响应格式  
• 增强错误处理: 详细的错误信息和错误码  
• 批量操作支持: 支持批量创建、更新、删除操作  
• 权限控制: 基于RBAC的细粒度权限控制  
• 分页查询: 支持灵活的分页、搜索、排序功能  
• HATEOAS支持: 提供相关资源链接  

## 认证方式

API使用JWT Bearer Token认证:
Authorization: Bearer <your-jwt-token>

## 响应格式

### 成功响应
{
  "success": true,
  "code": 200,
  "message": "操作成功",
  "data": {...},
  "timestamp": "2025-01-06T00:00:00Z",
  "request_id": "uuid-string"
}

### 错误响应
{
  "success": false,
  "code": 400,
  "message": "请求参数错误",
  "errors": [
    {
      "field": "username",
      "message": "用户名不能为空",
      "code": "REQUIRED_FIELD"
    }
  ],
  "timestamp": "2025-01-06T00:00:00Z",
  "request_id": "uuid-string"
}

### 分页响应
{
  "success": true,
  "code": 200,
  "message": "查询成功",
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 100,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false
  },
  "timestamp": "2025-01-06T00:00:00Z"
}"""
    
    async def _organize_by_modules(self, openapi_doc: Dict[str, Any]) -> Dict[str, Any]:
        """按功能模块组织API文档"""
        # 定义系统管理模块映射
        module_mapping = {
            "用户管理": {
                "paths": ["/api/v2/users"],
                "description": "用户信息管理，包括用户创建、更新、删除、角色分配等功能",
                "tags": ["用户管理 v2"]
            },
            "角色管理": {
                "paths": ["/api/v2/roles"],
                "description": "角色和权限管理，包括角色创建、权限分配、用户关联等功能",
                "tags": ["角色管理 v2"]
            },
            "菜单管理": {
                "paths": ["/api/v2/menus"],
                "description": "系统菜单管理，支持树形结构、权限控制和动态路由",
                "tags": ["菜单管理 v2"]
            },
            "部门管理": {
                "paths": ["/api/v2/departments"],
                "description": "组织架构管理，支持部门层级结构和人员分配",
                "tags": ["部门管理 v2"]
            },
            "API管理": {
                "paths": ["/api/v2/apis"],
                "description": "API接口管理，包括接口注册、权限配置和访问控制",
                "tags": ["API管理 v2"]
            },
            "API分组管理": {
                "paths": ["/api/v2/api-groups"],
                "description": "API分组管理，用于组织和分类API接口",
                "tags": ["API分组管理 v2"]
            },
            "字典类型管理": {
                "paths": ["/api/v2/dict-types"],
                "description": "数据字典类型管理，定义系统中使用的字典分类",
                "tags": ["字典类型管理 v2"]
            },
            "字典数据管理": {
                "paths": ["/api/v2/dict-data"],
                "description": "数据字典管理，维护系统中的枚举值和配置项",
                "tags": ["字典数据管理 v2"]
            },
            "系统参数管理": {
                "paths": ["/api/v2/system-params"],
                "description": "系统配置参数管理，包括系统级和用户级配置",
                "tags": ["系统参数管理 v2"]
            },
            "审计日志": {
                "paths": ["/api/v2/audit-logs"],
                "description": "系统操作审计日志查询，提供完整的操作追踪记录",
                "tags": ["审计日志 v2"]
            }
        }
        
        # 重新组织tags
        organized_tags = []
        for module_name, module_info in module_mapping.items():
            organized_tags.append({
                "name": module_info["tags"][0],
                "description": module_info["description"],
                "externalDocs": {
                    "description": f"{module_name}详细文档",
                    "url": f"/docs/modules/{module_name.lower().replace(' ', '-')}"
                }
            })
        
        # 添加通用标签
        organized_tags.extend([
            {
                "name": "认证",
                "description": "用户认证和授权相关接口"
            },
            {
                "name": "健康检查",
                "description": "系统健康状态检查接口"
            }
        ])
        
        openapi_doc["tags"] = organized_tags
        
        # 增强路径文档
        await self._enhance_path_documentation(openapi_doc)
        
        # 添加标准化的组件schemas
        self._add_standard_schemas(openapi_doc)
        
        return openapi_doc
    
    def _add_standard_schemas(self, openapi_doc: Dict[str, Any]):
        """添加标准化的组件schemas"""
        if "components" not in openapi_doc:
            openapi_doc["components"] = {}
        
        if "schemas" not in openapi_doc["components"]:
            openapi_doc["components"]["schemas"] = {}
        
        # 添加标准响应格式schemas
        openapi_doc["components"]["schemas"].update({
            "SuccessResponse": {
                "type": "object",
                "description": "标准成功响应格式",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": True,
                        "description": "操作是否成功"
                    },
                    "code": {
                        "type": "integer",
                        "example": 200,
                        "description": "HTTP状态码"
                    },
                    "message": {
                        "type": "string",
                        "example": "操作成功",
                        "description": "响应消息"
                    },
                    "data": {
                        "description": "响应数据"
                    },
                    "timestamp": {
                        "type": "string",
                        "format": "date-time",
                        "example": "2025-01-06T00:00:00Z",
                        "description": "响应时间戳"
                    },
                    "request_id": {
                        "type": "string",
                        "example": "550e8400-e29b-41d4-a716-446655440000",
                        "description": "请求ID"
                    }
                },
                "required": ["success", "code", "message", "timestamp"]
            },
            "ErrorResponse": {
                "type": "object",
                "description": "标准错误响应格式",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": False,
                        "description": "操作是否成功"
                    },
                    "code": {
                        "type": "integer",
                        "example": 400,
                        "description": "HTTP状态码"
                    },
                    "message": {
                        "type": "string",
                        "example": "请求参数错误",
                        "description": "错误消息"
                    },
                    "errors": {
                        "type": "array",
                        "description": "详细错误信息",
                        "items": {
                            "$ref": "#/components/schemas/ErrorDetail"
                        }
                    },
                    "timestamp": {
                        "type": "string",
                        "format": "date-time",
                        "example": "2025-01-06T00:00:00Z",
                        "description": "响应时间戳"
                    },
                    "request_id": {
                        "type": "string",
                        "example": "550e8400-e29b-41d4-a716-446655440000",
                        "description": "请求ID"
                    }
                },
                "required": ["success", "code", "message", "timestamp"]
            },
            "ErrorDetail": {
                "type": "object",
                "description": "错误详情",
                "properties": {
                    "field": {
                        "type": "string",
                        "example": "username",
                        "description": "错误字段"
                    },
                    "message": {
                        "type": "string",
                        "example": "用户名不能为空",
                        "description": "错误消息"
                    },
                    "code": {
                        "type": "string",
                        "example": "REQUIRED_FIELD",
                        "description": "错误代码"
                    }
                },
                "required": ["message"]
            },
            "PaginationInfo": {
                "type": "object",
                "description": "分页信息",
                "properties": {
                    "page": {
                        "type": "integer",
                        "example": 1,
                        "description": "当前页码"
                    },
                    "page_size": {
                        "type": "integer",
                        "example": 20,
                        "description": "每页数量"
                    },
                    "total": {
                        "type": "integer",
                        "example": 100,
                        "description": "总记录数"
                    },
                    "total_pages": {
                        "type": "integer",
                        "example": 5,
                        "description": "总页数"
                    },
                    "has_next": {
                        "type": "boolean",
                        "example": True,
                        "description": "是否有下一页"
                    },
                    "has_prev": {
                        "type": "boolean",
                        "example": False,
                        "description": "是否有上一页"
                    }
                },
                "required": ["page", "page_size", "total", "total_pages"]
            }
        })
        
        return openapi_doc
    
    async def _enhance_path_documentation(self, openapi_doc: Dict[str, Any]):
        """增强路径文档信息"""
        if "paths" not in openapi_doc:
            return
        
        for path, path_item in openapi_doc["paths"].items():
            for method, operation in path_item.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    # 清理和格式化描述
                    self._format_operation_description(operation)
                    
                    # 添加通用响应示例
                    await self._add_response_examples(operation, path, method)
                    
                    # 添加HATEOAS链接
                    self._add_hateoas_links(operation, path, method)
                    
                    # 添加错误响应
                    self._add_error_responses(operation)
    
    def _format_operation_description(self, operation: Dict[str, Any]):
        """格式化操作描述，确保Swagger UI兼容性"""
        if "description" in operation:
            # 简化Markdown格式，移除复杂的格式
            description = operation["description"]
            
            # 移除多余的空行和缩进
            lines = [line.strip() for line in description.split('\n') if line.strip()]
            
            # 简化格式
            formatted_lines = []
            for line in lines:
                # 简化标题格式
                if line.startswith('###'):
                    formatted_lines.append(line.replace('###', '').strip() + ':')
                elif line.startswith('##'):
                    formatted_lines.append(line.replace('##', '').strip())
                elif line.startswith('- **'):
                    # 简化列表项
                    formatted_lines.append('• ' + line.replace('- **', '').replace('**:', ':'))
                else:
                    formatted_lines.append(line)
            
            operation["description"] = '\n'.join(formatted_lines)
    
    async def _add_response_examples(self, operation: Dict[str, Any], path: str, method: str):
        """添加响应示例"""
        if "responses" not in operation:
            operation["responses"] = {}
        
        # 成功响应示例
        if "200" in operation["responses"]:
            response_200 = operation["responses"]["200"]
            if "content" in response_200 and "application/json" in response_200["content"]:
                json_content = response_200["content"]["application/json"]
                if "examples" not in json_content:
                    json_content["examples"] = {}
                
                # 根据路径和方法生成示例
                example_data = await self._generate_response_example(path, method)
                json_content["examples"]["success"] = {
                    "summary": "成功响应示例",
                    "value": example_data
                }
    
    async def _generate_response_example(self, path: str, method: str) -> Dict[str, Any]:
        """生成响应示例数据"""
        base_response = {
            "success": True,
            "code": 200,
            "message": "操作成功",
            "timestamp": datetime.now().isoformat(),
            "request_id": "550e8400-e29b-41d4-a716-446655440000"
        }
        
        # 根据路径生成示例数据
        if "/users" in path:
            if method.upper() == "GET":
                base_response.update({
                    "data": [
                        {
                            "id": 1,
                            "username": "admin",
                            "email": "admin@example.com",
                            "nick_name": "管理员",
                            "is_active": True,
                            "is_superuser": True,
                            "created_at": "2025-01-06T00:00:00Z",
                            "updated_at": "2025-01-06T00:00:00Z"
                        }
                    ],
                    "pagination": {
                        "page": 1,
                        "page_size": 20,
                        "total": 1,
                        "total_pages": 1,
                        "has_next": False,
                        "has_prev": False
                    }
                })
            elif method.upper() == "POST":
                base_response.update({
                    "code": 201,
                    "message": "用户创建成功",
                    "data": {
                        "id": 2,
                        "username": "newuser",
                        "email": "newuser@example.com",
                        "nick_name": "新用户",
                        "is_active": True,
                        "is_superuser": False,
                        "created_at": "2025-01-06T00:00:00Z",
                        "updated_at": "2025-01-06T00:00:00Z"
                    }
                })
        elif "/roles" in path:
            if method.upper() == "GET":
                base_response.update({
                    "data": [
                        {
                            "id": 1,
                            "role_name": "管理员",
                            "role_code": "admin",
                            "description": "系统管理员角色",
                            "is_active": True,
                            "created_at": "2025-01-06T00:00:00Z"
                        }
                    ]
                })
        
        return base_response
    
    def _add_hateoas_links(self, operation: Dict[str, Any], path: str, method: str):
        """添加HATEOAS链接"""
        if "responses" not in operation:
            return
        
        # 为200响应添加链接
        if "200" in operation["responses"]:
            response_200 = operation["responses"]["200"]
            if "links" not in response_200:
                response_200["links"] = {}
            
            # 根据资源类型添加相关链接
            if "/users" in path:
                if method.upper() == "GET" and path.endswith("/users"):
                    response_200["links"]["create_user"] = {
                        "operationId": "create_user",
                        "description": "创建新用户"
                    }
                elif method.upper() == "POST":
                    response_200["links"]["get_user"] = {
                        "operationId": "get_user_by_id",
                        "parameters": {"user_id": "$response.body#/data/id"},
                        "description": "获取创建的用户详情"
                    }
    
    def _add_error_responses(self, operation: Dict[str, Any]):
        """添加标准错误响应"""
        if "responses" not in operation:
            operation["responses"] = {}
        
        # 标准错误响应
        error_responses = {
            "400": {
                "description": "请求参数错误",
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/ErrorResponse"
                        },
                        "examples": {
                            "validation_error": {
                                "summary": "参数验证错误",
                                "value": {
                                    "success": False,
                                    "code": 400,
                                    "message": "请求参数验证失败",
                                    "errors": [
                                        {
                                            "field": "username",
                                            "message": "用户名不能为空",
                                            "code": "REQUIRED_FIELD"
                                        }
                                    ],
                                    "timestamp": "2025-01-06T00:00:00Z",
                                    "request_id": "550e8400-e29b-41d4-a716-446655440000"
                                }
                            }
                        }
                    }
                }
            },
            "401": {
                "description": "未授权访问",
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/ErrorResponse"
                        },
                        "examples": {
                            "unauthorized": {
                                "summary": "未授权访问",
                                "value": {
                                    "success": False,
                                    "code": 401,
                                    "message": "未授权访问，请先登录",
                                    "timestamp": "2025-01-06T00:00:00Z",
                                    "request_id": "550e8400-e29b-41d4-a716-446655440000"
                                }
                            }
                        }
                    }
                }
            },
            "403": {
                "description": "权限不足",
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/ErrorResponse"
                        }
                    }
                }
            },
            "404": {
                "description": "资源不存在",
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/ErrorResponse"
                        }
                    }
                }
            },
            "422": {
                "description": "数据处理错误",
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/ErrorResponse"
                        }
                    }
                }
            },
            "500": {
                "description": "服务器内部错误",
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/ErrorResponse"
                        }
                    }
                }
            }
        }
        
        # 只添加不存在的错误响应
        for code, response in error_responses.items():
            if code not in operation["responses"]:
                operation["responses"][code] = response
    
    async def generate_module_documentation(self, module_name: str) -> Dict[str, Any]:
        """生成特定模块的文档"""
        full_docs = await self.generate_v2_documentation()
        
        # 过滤出特定模块的路径
        module_paths = {}
        module_tag = f"{module_name} v2"
        
        for path, path_item in full_docs.get("paths", {}).items():
            for method, operation in path_item.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    if "tags" in operation and module_tag in operation["tags"]:
                        if path not in module_paths:
                            module_paths[path] = {}
                        module_paths[path][method] = operation
        
        return {
            "openapi": full_docs["openapi"],
            "info": {
                **full_docs["info"],
                "title": f"{module_name}API文档",
                "description": f"{module_name}相关的API接口文档"
            },
            "paths": module_paths,
            "components": full_docs.get("components", {}),
            "tags": [tag for tag in full_docs.get("tags", []) if tag["name"] == module_tag]
        }
    
    async def save_documentation_files(self):
        """保存文档文件到磁盘"""
        # 生成完整文档
        full_docs = await self.generate_v2_documentation()
        
        # 保存完整文档
        with open(f"{self.base_path}/openapi.json", "w", encoding="utf-8") as f:
            json.dump(full_docs, f, ensure_ascii=False, indent=2)
        
        # 生成并保存各模块文档
        modules = [
            "用户管理", "角色管理", "菜单管理", "部门管理",
            "API管理", "API分组管理", "字典类型管理", "字典数据管理",
            "系统参数管理", "审计日志"
        ]
        
        for module in modules:
            module_docs = await self.generate_module_documentation(module)
            filename = module.lower().replace(" ", "-").replace("管理", "")
            with open(f"{self.base_path}/modules/{filename}.json", "w", encoding="utf-8") as f:
                json.dump(module_docs, f, ensure_ascii=False, indent=2)
        
        # 生成文档索引
        await self._generate_documentation_index()
    
    async def _generate_documentation_index(self):
        """生成文档索引"""
        index = {
            "title": "系统管理API v2文档",
            "version": "2.0.0",
            "generated_at": datetime.now().isoformat(),
            "modules": [
                {
                    "name": "用户管理",
                    "description": "用户信息管理相关接口",
                    "file": "modules/用户.json",
                    "endpoints_count": await self._count_module_endpoints("用户管理")
                },
                {
                    "name": "角色管理", 
                    "description": "角色和权限管理相关接口",
                    "file": "modules/角色.json",
                    "endpoints_count": await self._count_module_endpoints("角色管理")
                },
                {
                    "name": "菜单管理",
                    "description": "系统菜单管理相关接口", 
                    "file": "modules/菜单.json",
                    "endpoints_count": await self._count_module_endpoints("菜单管理")
                },
                {
                    "name": "部门管理",
                    "description": "组织架构管理相关接口",
                    "file": "modules/部门.json", 
                    "endpoints_count": await self._count_module_endpoints("部门管理")
                },
                {
                    "name": "API管理",
                    "description": "API接口管理相关接口",
                    "file": "modules/api.json",
                    "endpoints_count": await self._count_module_endpoints("API管理")
                },
                {
                    "name": "API分组管理",
                    "description": "API分组管理相关接口", 
                    "file": "modules/api分组.json",
                    "endpoints_count": await self._count_module_endpoints("API分组管理")
                },
                {
                    "name": "字典类型管理",
                    "description": "数据字典类型管理相关接口",
                    "file": "modules/字典类型.json",
                    "endpoints_count": await self._count_module_endpoints("字典类型管理")
                },
                {
                    "name": "字典数据管理", 
                    "description": "数据字典管理相关接口",
                    "file": "modules/字典数据.json",
                    "endpoints_count": await self._count_module_endpoints("字典数据管理")
                },
                {
                    "name": "系统参数管理",
                    "description": "系统配置参数管理相关接口",
                    "file": "modules/系统参数.json", 
                    "endpoints_count": await self._count_module_endpoints("系统参数管理")
                },
                {
                    "name": "审计日志",
                    "description": "系统操作审计日志相关接口",
                    "file": "modules/审计日志.json",
                    "endpoints_count": await self._count_module_endpoints("审计日志")
                }
            ],
            "total_endpoints": sum([
                await self._count_module_endpoints(module["name"]) 
                for module in [
                    {"name": "用户管理"}, {"name": "角色管理"}, {"name": "菜单管理"}, 
                    {"name": "部门管理"}, {"name": "API管理"}, {"name": "API分组管理"},
                    {"name": "字典类型管理"}, {"name": "字典数据管理"}, 
                    {"name": "系统参数管理"}, {"name": "审计日志"}
                ]
            ]),
            "documentation_urls": {
                "swagger_ui": "/docs",
                "redoc": "/redoc", 
                "openapi_json": "/openapi.json",
                "v2_docs": "/api/v2/docs"
            }
        }
        
        with open(f"{self.base_path}/index.json", "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    async def _count_module_endpoints(self, module_name: str) -> int:
        """统计模块端点数量"""
        try:
            module_docs = await self.generate_module_documentation(module_name)
            count = 0
            for path_item in module_docs.get("paths", {}).values():
                count += len([m for m in path_item.keys() if m.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]])
            return count
        except:
            return 0


# 全局文档服务实例
swagger_service: Optional[SwaggerDocumentationService] = None


def get_swagger_service() -> Optional[SwaggerDocumentationService]:
    """获取Swagger文档服务实例"""
    return swagger_service


def init_swagger_service(app: FastAPI):
    """初始化Swagger文档服务"""
    global swagger_service
    swagger_service = SwaggerDocumentationService(app)
    return swagger_service