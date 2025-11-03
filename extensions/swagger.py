"""
OpenAPI/Swagger documentation blueprint.
Provides interactive API documentation using Swagger UI.
"""
from flask import Blueprint, jsonify, render_template_string
import json

swagger_bp = Blueprint('swagger', __name__)


def get_openapi_spec():
    """
    Generate OpenAPI 3.0 specification.

    Returns:
        dict: OpenAPI specification
    """
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Cisco Configuration Generator API",
            "version": "1.0.0",
            "description": "Enterprise-grade API for generating Cisco device configurations with CCIE-level protocol support",
            "contact": {
                "name": "API Support",
                "email": "support@example.com"
            },
            "license": {
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            }
        },
        "servers": [
            {
                "url": "http://localhost:5000",
                "description": "Development server"
            },
            {
                "url": "https://api.example.com",
                "description": "Production server"
            }
        ],
        "tags": [
            {
                "name": "Configuration",
                "description": "Configuration generation endpoints"
            },
            {
                "name": "Authentication",
                "description": "User authentication and authorization"
            },
            {
                "name": "API Keys",
                "description": "API key management"
            },
            {
                "name": "History",
                "description": "Configuration history management"
            },
            {
                "name": "System",
                "description": "System information and health"
            }
        ],
        "paths": {
            "/health": {
                "get": {
                    "summary": "Health check",
                    "description": "Check if the API is running and healthy",
                    "tags": ["System"],
                    "responses": {
                        "200": {
                            "description": "Service is healthy",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string", "example": "healthy"},
                                            "service": {"type": "string", "example": "Cisco Configuration Generator"},
                                            "version": {"type": "string", "example": "1.0.0"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/v1/generate": {
                "post": {
                    "summary": "Generate configuration",
                    "description": "Generate Cisco device configuration based on provided parameters",
                    "tags": ["Configuration"],
                    "security": [{"BearerAuth": []}, {"ApiKeyAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ConfigRequest"
                                },
                                "examples": {
                                    "basic": {
                                        "summary": "Basic router configuration",
                                        "value": {
                                            "platform": "ios",
                                            "hostname": "router01",
                                            "domain_name": "example.com",
                                            "interfaces": [
                                                {
                                                    "name": "GigabitEthernet0/0",
                                                    "ip_address": "192.168.1.1",
                                                    "subnet_mask": "255.255.255.0",
                                                    "description": "LAN Interface"
                                                }
                                            ],
                                            "output_format": "cli"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Configuration generated successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/ConfigResponse"
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Validation error"
                        },
                        "401": {
                            "description": "Unauthorized"
                        }
                    }
                }
            },
            "/api/v1/platforms": {
                "get": {
                    "summary": "List supported platforms",
                    "description": "Get list of supported Cisco platforms",
                    "tags": ["Configuration"],
                    "responses": {
                        "200": {
                            "description": "List of platforms",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "platforms": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                                "example": ["ios", "nxos", "asa", "iosxr"]
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/auth/register": {
                "post": {
                    "summary": "Register new user",
                    "description": "Create a new user account",
                    "tags": ["Authentication"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/RegisterRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "User created successfully"
                        },
                        "400": {
                            "description": "Invalid input"
                        }
                    }
                }
            },
            "/auth/login": {
                "post": {
                    "summary": "User login",
                    "description": "Authenticate and receive JWT tokens",
                    "tags": ["Authentication"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/LoginRequest"
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Login successful",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/TokenResponse"
                                    }
                                }
                            }
                        },
                        "401": {
                            "description": "Invalid credentials"
                        }
                    }
                }
            },
            "/history/list": {
                "get": {
                    "summary": "List configuration history",
                    "description": "Get paginated list of generated configurations",
                    "tags": ["History"],
                    "security": [{"BearerAuth": []}],
                    "parameters": [
                        {
                            "name": "page",
                            "in": "query",
                            "schema": {"type": "integer", "default": 1}
                        },
                        {
                            "name": "per_page",
                            "in": "query",
                            "schema": {"type": "integer", "default": 20}
                        },
                        {
                            "name": "platform",
                            "in": "query",
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "History list retrieved successfully"
                        },
                        "401": {
                            "description": "Unauthorized"
                        }
                    }
                }
            }
        },
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "JWT token obtained from /auth/login"
                },
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                    "description": "API key for programmatic access"
                }
            },
            "schemas": {
                "ConfigRequest": {
                    "type": "object",
                    "required": ["platform", "hostname"],
                    "properties": {
                        "platform": {
                            "type": "string",
                            "enum": ["ios", "nxos", "asa", "iosxr"],
                            "description": "Target platform"
                        },
                        "hostname": {
                            "type": "string",
                            "description": "Device hostname"
                        },
                        "domain_name": {
                            "type": "string",
                            "description": "Domain name"
                        },
                        "interfaces": {
                            "type": "array",
                            "items": {
                                "$ref": "#/components/schemas/Interface"
                            }
                        },
                        "vlans": {
                            "type": "array",
                            "items": {
                                "$ref": "#/components/schemas/VLAN"
                            }
                        },
                        "output_format": {
                            "type": "string",
                            "enum": ["cli", "json", "yaml"],
                            "default": "cli"
                        }
                    }
                },
                "Interface": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "ip_address": {"type": "string"},
                        "subnet_mask": {"type": "string"},
                        "description": {"type": "string"}
                    }
                },
                "VLAN": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"}
                    }
                },
                "ConfigResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "configuration": {"type": "string"},
                        "platform": {"type": "string"},
                        "format": {"type": "string"}
                    }
                },
                "RegisterRequest": {
                    "type": "object",
                    "required": ["username", "email", "password"],
                    "properties": {
                        "username": {"type": "string"},
                        "email": {"type": "string", "format": "email"},
                        "password": {"type": "string", "minLength": 8}
                    }
                },
                "LoginRequest": {
                    "type": "object",
                    "required": ["username", "password"],
                    "properties": {
                        "username": {"type": "string"},
                        "password": {"type": "string"}
                    }
                },
                "TokenResponse": {
                    "type": "object",
                    "properties": {
                        "access_token": {"type": "string"},
                        "refresh_token": {"type": "string"},
                        "token_type": {"type": "string", "example": "Bearer"},
                        "expires_in": {"type": "integer"}
                    }
                }
            }
        }
    }


@swagger_bp.route('/openapi.json')
def openapi_json():
    """
    OpenAPI specification endpoint.

    Returns:
        JSON response with OpenAPI spec
    """
    return jsonify(get_openapi_spec())


@swagger_bp.route('/docs')
def swagger_ui():
    """
    Swagger UI documentation page.

    Returns:
        HTML page with Swagger UI
    """
    swagger_ui_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cisco Config Generator - API Documentation</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.10.0/swagger-ui.css">
        <style>
            body { margin: 0; padding: 0; }
            .swagger-ui .topbar { display: none; }
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.10.0/swagger-ui-bundle.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.10.0/swagger-ui-standalone-preset.js"></script>
        <script>
            window.onload = function() {
                const ui = SwaggerUIBundle({
                    url: '/api/openapi.json',
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIStandalonePreset
                    ],
                    plugins: [
                        SwaggerUIBundle.plugins.DownloadUrl
                    ],
                    layout: "StandaloneLayout",
                    persistAuthorization: true,
                    displayRequestDuration: true,
                    filter: true,
                    tryItOutEnabled: true
                });
                window.ui = ui;
            };
        </script>
    </body>
    </html>
    """
    return render_template_string(swagger_ui_html)


@swagger_bp.route('/redoc')
def redoc():
    """
    ReDoc documentation page (alternative to Swagger UI).

    Returns:
        HTML page with ReDoc
    """
    redoc_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cisco Config Generator - API Documentation</title>
        <style>
            body { margin: 0; padding: 0; }
        </style>
    </head>
    <body>
        <redoc spec-url='/api/openapi.json'></redoc>
        <script src="https://cdn.jsdelivr.net/npm/redoc@latest/bundles/redoc.standalone.js"></script>
    </body>
    </html>
    """
    return render_template_string(redoc_html)
