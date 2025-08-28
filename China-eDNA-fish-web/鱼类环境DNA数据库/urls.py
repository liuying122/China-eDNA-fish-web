# 作者：刘英 (12261077991@qq.com)
# 创建日期：
# 版本：1.0.0
# 描述：
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import TemplateView

urlpatterns = [
    path('', views.首页),  # 根地址
    path('', views.首页视图.as_view()),
    path('search/', views.search_species, name='search_species'),
    path('blast_search/', views.blast_search, name='blast_search'),
    path('搜索/', TemplateView.as_view(template_name='搜索.html'), name='搜索'),
    path('搜索结果/', views.HomeView.as_view(), name='搜索结果'),
    path('分析平台/', TemplateView.as_view(template_name='分析平台.html')),
    path('run_vsearch/', views.run_vsearch, name='run_vsearch'),
    path('run_split_fastq/', views.run_split_fastq, name='run_split_fastq'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
