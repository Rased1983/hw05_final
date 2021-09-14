from django.conf import settings
from django.core.paginator import Paginator


def paginator_func(request, posts):
    paginator = Paginator(posts, settings.PAGINATOR_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
