import json
import os

def handler(request):
    path = request.path
    method = request.method
    
    # Simple test endpoint
    if path == '/api/health':
        return {"statusCode": 200, "body": json.dumps({"status": "healthy"})}
    
    if path == '/api/test':
        return {"statusCode": 200, "body": json.dumps({
            "env": os.environ.get('DATABASE_URL', 'NOT SET'),
            "python_version": os.popen('python --version').read() if os.name != 'nt' else 'Windows'
        })}
    
    # SPA fallback
    html = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LedgerPro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container py-5 text-center">
        <h1>LedgerPro</h1>
        <p class="lead">Double Entry Accounting System</p>
        <div class="alert alert-info">
            <strong>API Status:</strong> Running<br>
            Database: """ + ("Configured" if os.environ.get('DATABASE_URL') else "NOT CONFIGURED") + """
        </div>
        <div class="text-start">
            <h5>Available Endpoints:</h5>
            <ul class="list-group">
                <li class="list-group-item"><code>GET /api/health</code> - Health check</li>
                <li class="list-group-item"><code>GET /api/test</code> - Environment test</li>
            </ul>
        </div>
    </div>
</body>
</html>"""
    return {"statusCode": 200, "headers": {"Content-Type": "text/html"}, "body": html}
