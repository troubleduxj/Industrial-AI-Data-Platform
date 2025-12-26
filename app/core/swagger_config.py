from fastapi import FastAPI
from fastapi.responses import HTMLResponse


def create_offline_docs_html(app: FastAPI) -> str:
    """
    创建离线 Swagger UI HTML
    """
    html_content = '''
<!DOCTYPE html>
<html>
<head>
    <title>''' + app.title + ''' - API Documentation</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: #fafafa;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            color: #1976d2;
            text-align: center;
            margin-bottom: 30px;
        }
        .tag-filter {
            margin: 20px 0;
            text-align: center;
        }
        .tag-button {
            margin: 5px;
            padding: 8px 16px;
            border: 1px solid #ddd;
            background: white;
            cursor: pointer;
            border-radius: 4px;
            transition: all 0.3s;
        }
        .tag-button:hover {
            background: #f5f5f5;
        }
        .tag-button.active {
            background: #1976d2;
            color: white;
            border-color: #1976d2;
        }
        .endpoint {
            margin: 20px 0;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .endpoint-header {
            padding: 15px 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .endpoint-header:hover {
            background: #e9ecef;
        }
        .method {
            padding: 4px 12px;
            border-radius: 4px;
            color: white;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 12px;
            margin-right: 15px;
            min-width: 60px;
            text-align: center;
        }
        .get { background: #61affe; }
        .post { background: #49cc90; }
        .put { background: #fca130; }
        .delete { background: #f93e3e; }
        .patch { background: #50e3c2; }
        .endpoint-content {
            padding: 20px;
            display: none;
        }
        .endpoint-content.show {
            display: block;
        }
        .try-it-out {
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 4px;
        }
        .form-group {
            margin: 10px 0;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        .form-group input, .form-group textarea {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-family: monospace;
        }
        .btn {
            padding: 8px 16px;
            margin: 5px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
        }
        .btn-primary {
            background: #007bff;
            color: white;
        }
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        .response-content {
            margin: 15px 0;
            padding: 15px;
            border-radius: 4px;
            font-family: monospace;
            white-space: pre-wrap;
            max-height: 400px;
            overflow-y: auto;
        }
        .response-success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        .response-error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        .toggle-icon {
            transition: transform 0.3s;
        }
        .toggle-icon.rotated {
            transform: rotate(180deg);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>''' + app.title + '''</h1>
        <div class="tag-filter" id="tag-filter">
            <button class="tag-button active" onclick="filterByTag('all')">All</button>
        </div>
        <div id="api-docs">正在加载...</div>
    </div>
    
    <script>
        let currentSpec = null;
        
        function filterByTag(tag) {
            const buttons = document.querySelectorAll('.tag-button');
            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            const endpoints = document.querySelectorAll('.endpoint');
            endpoints.forEach(endpoint => {
                if (tag === 'all' || endpoint.dataset.tags.includes(tag)) {
                    endpoint.style.display = 'block';
                } else {
                    endpoint.style.display = 'none';
                }
            });
        }
        
        function toggleEndpoint(index) {
            const content = document.getElementById('endpoint-' + index);
            const icon = document.querySelector('[data-endpoint="' + index + '"] .toggle-icon');
            
            if (content.classList.contains('show')) {
                content.classList.remove('show');
                icon.classList.remove('rotated');
            } else {
                content.classList.add('show');
                icon.classList.add('rotated');
            }
        }
        
        function toggleTryItOut(index) {
            const form = document.getElementById('try-form-' + index);
            if (form.style.display === 'none' || !form.style.display) {
                form.style.display = 'block';
            } else {
                form.style.display = 'none';
            }
        }
        
        function clearForm(index) {
            const form = document.getElementById('try-form-' + index);
            const inputs = form.querySelectorAll('input, textarea');
            inputs.forEach(input => input.value = '');
            
            const responseDiv = document.getElementById('response-' + index);
            responseDiv.textContent = '';
            responseDiv.className = 'response-content';
        }
        
        async function executeRequest(index, method, path) {
            const authToken = document.getElementById('auth-' + index).value;
            const responseDiv = document.getElementById('response-' + index);
            
            try {
                const headers = {
                    'Content-Type': 'application/json'
                };
                
                if (authToken) {
                    headers['Authorization'] = 'Bearer ' + authToken;
                }
                
                let requestBody = null;
                const bodyTextarea = document.querySelector('#try-form-' + index + ' textarea[name="body"]');
                if (bodyTextarea && bodyTextarea.value) {
                    try {
                        requestBody = JSON.parse(bodyTextarea.value);
                    } catch (e) {
                        responseDiv.textContent = 'Invalid JSON in request body: ' + e.message;
                        responseDiv.className = 'response-content response-error';
                        return;
                    }
                }
                
                const startTime = Date.now();
                const response = await fetch(path, {
                    method: method.toUpperCase(),
                    headers: headers,
                    body: requestBody ? JSON.stringify(requestBody) : null
                });
                const endTime = Date.now();
                
                const responseData = await response.json();
                
                const formattedResponse = 'Status: ' + response.status + ' ' + response.statusText + '\n' +
                    'Response Time: ' + (endTime - startTime) + 'ms\n\n' +
                    'Response Body:\n' + JSON.stringify(responseData, null, 2);
                
                responseDiv.textContent = formattedResponse;
                responseDiv.className = 'response-content ' + (response.ok ? 'response-success' : 'response-error');
                
            } catch (error) {
                responseDiv.textContent = 'Request failed: ' + error.message;
                responseDiv.className = 'response-content response-error';
            }
        }
        
        // 加载API文档
        fetch('''' + app.openapi_url + '''')
            .then(response => response.json())
            .then(spec => {
                currentSpec = spec;
                const container = document.getElementById('api-docs');
                const tagFilter = document.getElementById('tag-filter');
                let html = '';
                let tags = new Set();
                let endpointIndex = 0;
                
                // 收集所有标签
                for (const [path, methods] of Object.entries(spec.paths)) {
                    for (const [method, details] of Object.entries(methods)) {
                        if (details.tags) {
                            details.tags.forEach(tag => tags.add(tag));
                        }
                    }
                }
                
                // 添加标签按钮
                tags.forEach(tag => {
                    const button = document.createElement('button');
                    button.className = 'tag-button';
                    button.textContent = tag;
                    button.onclick = () => filterByTag(tag);
                    tagFilter.appendChild(button);
                });
                
                // 生成端点HTML
                for (const [path, methods] of Object.entries(spec.paths)) {
                    for (const [method, details] of Object.entries(methods)) {
                        const endpointTags = details.tags ? details.tags.join(' ') : '';
                        
                        html += '<div class="endpoint" data-tags="' + endpointTags + '">';
                        html += '<div class="endpoint-header" onclick="toggleEndpoint(' + endpointIndex + ')" data-endpoint="' + endpointIndex + '">';
                        html += '<div>';
                        html += '<span class="method ' + method + '">' + method.toUpperCase() + '</span>';
                        const displayPath = path.replace(/'/g, "\\'").replace(/"/g, '\\"');
                        html += '<strong>' + displayPath + '</strong>';
                        if (details.summary) {
                            html += ' - ' + details.summary.replace(/'/g, "\\'");
                        }
                        html += '</div>';
                        html += '<span class="toggle-icon">▼</span>';
                        html += '</div>';
                        
                        html += '<div class="endpoint-content" id="endpoint-' + endpointIndex + '">';
                        
                        if (details.description) {
                            html += '<p>' + details.description.replace(/'/g, "\\'") + '</p>';
                        }
                        
                        // Try it out section
                        html += '<div class="try-it-out">';
                        html += '<h4>Try it out</h4>';
                        html += '<div id="try-form-' + endpointIndex + '">';
                        
                        // Auth token input
                        html += '<div class="form-group">';
                        html += '<label>Authorization Token (optional):</label>';
                        html += '<input type="text" id="auth-' + endpointIndex + '" placeholder="Enter your bearer token">';
                        html += '</div>';
                        
                        // Request body for POST/PUT/PATCH
                        if (['post', 'put', 'patch'].includes(method)) {
                            html += '<div class="form-group">';
                            html += '<label>Request Body (JSON):</label>';
                            html += '<textarea name="body" rows="6" placeholder="{\n  \"key\": \"value\"\n}"></textarea>';
                            html += '</div>';
                        }
                        
                        const escapedPath = path.replace(/'/g, "\\'").replace(/"/g, '\\"');
                        html += '<button class="btn btn-primary" onclick="executeRequest(' + endpointIndex + ', \'' + method + '\', \'' + escapedPath + '\')">'
                        html += 'Execute';
                        html += '</button>';
                        html += '<button class="btn btn-secondary" onclick="clearForm(' + endpointIndex + ')">';
                        html += 'Clear';
                        html += '</button>';
                        html += '</div>';
                        
                        html += '<div class="response-content" id="response-' + endpointIndex + '"></div>';
                        html += '</div>';
                        
                        html += '</div>';
                        html += '</div>';
                        
                        endpointIndex++;
                    }
                }
                
                container.innerHTML = html;
            })
            .catch(error => {
                document.getElementById('api-docs').innerHTML = 
                    '<p style="color: red;">Failed to load API documentation: ' + error.message + '</p>';
            });
    </script>
</body>
</html>
    '''
    return html_content


def setup_offline_docs(app: FastAPI):
    """设置离线文档"""
    # 禁用默认的文档路由
    app.openapi_url = "/openapi.json"
    
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return HTMLResponse(content=create_offline_docs_html(app))
    
    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        html_content = '''
<!DOCTYPE html>
<html>
<head>
    <title>''' + app.title + ''' - ReDoc</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 { color: #1976d2; }
        .endpoint {
            margin: 20px 0;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .method {
            padding: 4px 8px;
            border-radius: 3px;
            color: white;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 12px;
            margin-right: 10px;
        }
        .get { background: #4caf50; }
        .post { background: #2196f3; }
        .put { background: #ff9800; }
        .delete { background: #f44336; }
    </style>
</head>
<body>
    <div class="container">
        <h1>''' + app.title + '''</h1>
        <p>API Documentation - Simplified Version</p>
        <div id="api-docs">Loading...</div>
    </div>
    
    <script>
        fetch('''' + app.openapi_url + '''')
            .then(response => response.json())
            .then(spec => {
                const container = document.getElementById('api-docs');
                let html = '';
                
                for (const [path, methods] of Object.entries(spec.paths)) {
                    html += '<div class="endpoint">';
                    html += '<h3>' + path + '</h3>';
                    
                    for (const [method, details] of Object.entries(methods)) {
                        html += '<div style="margin: 10px 0;">';
                        html += '<span class="method ' + method + '">' + method.toUpperCase() + '</span>';
                        html += '<strong>' + (details.summary || '').replace(/'/g, "\\'") + '</strong>';
                        if (details.description) {
                            html += '<p>' + details.description.replace(/'/g, "\\'") + '</p>';
                        }
                        html += '</div>';
                    }
                    
                    html += '</div>';
                }
                
                container.innerHTML = html;
            })
            .catch(error => {
                document.getElementById('api-docs').innerHTML = 
                    '<p style="color: red;">Failed to load API documentation: ' + error.message + '</p>';
            });
    </script>
</body>
</html>
        '''
        return HTMLResponse(content=html_content)