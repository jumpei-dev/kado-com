from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path

# Import core modules
from scout_ui.core.config import Settings
from scout_ui.core.database import init_db, check_db_connection
from scout_ui.core.auth import get_current_user, get_current_user_optional, cleanup_expired_sessions

# Import API routers
from scout_ui.api.auth import router as auth_router
from scout_ui.api.dashboard import router as dashboard_router
from scout_ui.api.stores import router as stores_router

# Initialize settings
settings = Settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Scout UI application...")
    
    try:
        # Initialize database
        init_db()
        logger.info("Database initialized successfully")
        
        # Check database connection
        if check_db_connection():
            logger.info("Database connection verified")
        else:
            logger.error("Database connection failed")
            raise Exception("Database connection failed")
            
        # Cleanup expired sessions on startup
        cleanup_expired_sessions()
        logger.info("Expired sessions cleaned up")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Scout UI application...")
    cleanup_expired_sessions()
    logger.info("Application shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="Scout UI",
    description="店舗管理システム - 店舗の稼働状況とキャスト情報を管理",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Add middleware
# Session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key="your-secret-key-here-change-in-production"
)

if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[settings.HOST, "localhost", "127.0.0.1"]
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else [f"http://{settings.HOST}:{settings.PORT}"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Setup static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include API routers
app.include_router(auth_router, prefix="/api/auth", tags=["認証"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["ダッシュボード"])
app.include_router(stores_router, prefix="/api/stores", tags=["店舗管理"])

# Root redirect
@app.get("/")
async def root():
    """Root endpoint - redirect to dashboard"""
    return RedirectResponse(url="/dashboard", status_code=302)

# Dashboard page
@app.get("/dashboard")
async def dashboard_page(
    request: Request,
    current_user: dict = Depends(get_current_user_optional)
):
    """Dashboard page"""
    try:
        # Get initial data for dashboard
        from scout_ui.utils.filters import get_filter_options
        from scout_ui.core.database import get_db_session
        
        # Default filters
        current_filters = {
            'page': 1,
            'area': '',
            'business_type': '',
            'date_from': '',
            'date_to': '',
            'sort_by': 'working_rate',
            'sort_order': 'desc',
            'view_type': 'weekly'
        }
        
        # Get filter options from database
        db = get_db_session()
        filter_options = get_filter_options(db)
        
        # Get basic stats (placeholder)
        stats = {
            'total_stores': 0,
            'active_stores': 0,
            'avg_working_rate': 0.0
        }
        
        return templates.TemplateResponse(
            "dashboard/index.html",
            {
                "request": request,
                "current_user": current_user,
                "current_filters": current_filters,
                "filter_options": filter_options,
                "stats": stats
            }
        )
        
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        raise HTTPException(status_code=500, detail="ダッシュボードの読み込みに失敗しました")

# Stores list page
@app.get("/stores")
async def stores_page(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Stores list page"""
    try:
        # Get initial data for stores page
        from scout_ui.utils.filters import get_filter_options
        from scout_ui.core.database import get_db_session
        
        # Default filters
        current_filters = {
            'page': 1,
            'page_size': 20,
            'area': '',
            'business_type': '',
            'date_from': '',
            'date_to': '',
            'min_working_rate': '',
            'max_working_rate': '',
            'sort_by': 'working_rate',
            'sort_order': 'desc',
            'view_type': 'grid'
        }
        
        # Get filter options with database session
        db = get_db_session()
        filter_options = get_filter_options(db=db)
        
        return templates.TemplateResponse(
            "stores/list.html",
            {
                "request": request,
                "current_user": current_user,
                "current_filters": current_filters,
                "filter_options": filter_options
            }
        )
        
    except Exception as e:
        logger.error(f"Error loading stores page: {e}")
        raise HTTPException(status_code=500, detail="店舗一覧の読み込みに失敗しました")

# Login page
@app.get("/login")
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db_status = await check_db_connection()
        
        return {
            "status": "healthy" if db_status else "unhealthy",
            "database": "connected" if db_status else "disconnected",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "error",
            "version": "1.0.0",
            "error": str(e)
        }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """404 error handler"""
    return templates.TemplateResponse(
        "errors/404.html",
        {"request": request},
        status_code=404
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    """500 error handler"""
    logger.error(f"Internal server error: {exc}")
    return templates.TemplateResponse(
        "errors/500.html",
        {"request": request},
        status_code=500
    )

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    uvicorn.run(
        "scout_ui.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )