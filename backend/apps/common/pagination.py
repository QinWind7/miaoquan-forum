"""统一分页：前端通过 page / page_size 控制，响应保持 DRF 标准结构
{count, next, previous, results}。"""
from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50
    page_query_param = "page"
