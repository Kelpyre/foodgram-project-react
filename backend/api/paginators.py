from rest_framework.pagination import PageNumberPagination


class MyPaginationClass(PageNumberPagination):
    """Кастомный класс пагинации."""
    page_size_query_param = 'limit'
