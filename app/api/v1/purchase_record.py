from collections import defaultdict
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from tortoise.exceptions import DoesNotExist
from tortoise.functions import Sum, Count
from models.models import MDBMPPurchaseRecord
from typing import List, Dict

routers = APIRouter()

class PurchaseRecordResponseItem(BaseModel):
    type: str
    par_value: float
    count: int
    amount: float

    class Config:
        orm_mode = True

class SourceResponseItem(BaseModel):
    source: str
    total_cards: int
    total_amount: float
    categories: List[PurchaseRecordResponseItem]

    class Config:
        orm_mode = True

class PurchaserResponseItem(BaseModel):
    purchaser_name: str
    sources: str
    type:str
    par_value:float
    total_price:float
    purchaser_name_abbr:str
    

    class Config:
        orm_mode = True

@routers.get("/purchase-records/{purchase_date}")
async def get_purchase_records(purchase_date: date):
    start_datetime = datetime.combine(purchase_date, datetime.min.time())
    end_datetime = datetime.combine(purchase_date, datetime.max.time())

    purchase_records = await MDBMPPurchaseRecord.filter(
        purchase_time__gte=start_datetime, 
        purchase_time__lte=end_datetime
    ).all()

    if not purchase_records:
        raise HTTPException(status_code=404, detail="No purchase records found for this date")
    # 步骤2: 数据处理与汇总
    aggregated_data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for record in purchase_records:
        # 按purchaser_name, source, type进行分组，并汇总数据
        entry = {
            'total_price': record.total_price,
            'count': 1  # 假设每条记录代表一张卡
        }
        aggregated_data[record.purchaser_name][record.source][record.type].append(entry)
    # 步骤3: 构造响应数据
    response_data = []
    for purchaser, sources in aggregated_data.items():
        purchaser_info = {
            'purchaser_name': purchaser,
            'sources': []
        }
        for source, types in sources.items():
            source_info = {
                'source': source,
                'categories': []
            }
            for type, entries in types.items():
                total_count = sum(entry['count'] for entry in entries)
                total_amount = sum(entry['total_price'] for entry in entries)
                category_info = {
                    'type': type,
                    'total_count': total_count,
                    'total_amount': total_amount
                }
                source_info['categories'].append(category_info)
            purchaser_info['sources'].append(source_info)
        response_data.append(purchaser_info)
    
    return response_data

@routers.get('/check')
async def check_data(purchaser_name: str, source: str, purchase_date: date = date(2024, 2, 21)):
    # 将日期转换为当天的开始和结束时间
    start_datetime = datetime.combine(purchase_date, datetime.min.time())
    end_datetime = datetime.combine(purchase_date, datetime.max.time())

    # 构造查询以获取指定采购员和来源下每个类别的总数和总金额
    categories = await MDBMPPurchaseRecord.filter(
        purchaser_name=purchaser_name, 
        source=source,
        purchase_time__gte=start_datetime,  # 添加时间限制
        purchase_time__lte=end_datetime  # 添加时间限制
    ).annotate(
        total_count=Count('id'), 
        total_amount=Sum('total_price')
    ).group_by('type').values('type', 'total_count', 'total_amount')

    # 核对数据
    for category in categories:
        print(f"Type: {category['type']}, Total Count: {category['total_count']}, Total Amount: {category['total_amount']}")
