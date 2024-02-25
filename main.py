import os
from dotenv import load_dotenv
from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import purchase_record

load_dotenv()

# 根据环境变量来设置文档的 URL，如果环境变量设置为生产环境，则禁用文档
DOCS_URL = None if os.getenv("ENVIRONMENT") == "production" else "/docs"
REDOC_URL = None if os.getenv("ENVIRONMENT") == "production" else "/redoc"

app = FastAPI(docs_url=DOCS_URL, redoc_url=REDOC_URL)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有域的跨域请求，您可以根据需要更改为特定的域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法（GET, POST, PUT, DELETE 等）
    allow_headers=["*"],  # 允许所有头部
)



register_tortoise(
    app,
    db_url='mysql://root:123456@localhost:3306/sip_twocards_bmp',
    modules={"models": ["models.models"]}, 
    generate_schemas=True,
    add_exception_handlers=True,
)
app.include_router(purchase_record.routers, tags=["Purchase Records"], prefix="/api/v1")