
from django import template
from django.conf import settings
from django.template.loader import render_to_string

from ..models import DashboardStats

register = template.Library()


@register.simple_tag(takes_context=True)
def chart_containers(context):
    if 'admin_tools.dashboard' not in settings.INSTALLED_APPS:
        context['charts'] = DashboardStats.get_active_graph()
        return render_to_string("admin_tools_stats/chart_containers.html", context.flatten())


@register.simple_tag
def set_nvd3_css_path(val=None):
    return getattr(settings, 'ADMIN_CHARTS_NVD3_CSS_PATH', None)


@register.simple_tag
def set_nvd3_js_path(val=None):
    return getattr(settings, 'ADMIN_CHARTS_NVD3_JS_PATH', None)


@register.simple_tag
def set_d3_js_path(val=None):
    return getattr(settings, 'ADMIN_CHARTS_D3_JS_PATH', None)
