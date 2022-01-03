from django import template
from django.conf import settings
from django.template.loader import render_to_string
from django.templatetags.static import static

from ..models import DashboardStats


register = template.Library()


def static_or_path(url: str):
    if url.startswith("http"):
        return url
    return static(url)


@register.simple_tag(takes_context=True)
def chart_containers(context):
    if "admin_tools.dashboard" not in settings.INSTALLED_APPS:
        context["charts"] = DashboardStats.get_active_graph()
        return render_to_string("admin_tools_stats/chart_containers.html", context.flatten())


@register.simple_tag
def set_nvd3_css_path(val=None):
    return static_or_path(
        getattr(
            settings,
            "ADMIN_CHARTS_NVD3_CSS_PATH",
            "https://unpkg.com/nvd3@1.8.6/build/nv.d3.min.css",
        ),
    )


@register.simple_tag
def set_nvd3_js_path(val=None):
    return static_or_path(
        getattr(
            settings,
            "ADMIN_CHARTS_NVD3_JS_PATH",
            "https://unpkg.com/nvd3@1.8.6/build/nv.d3.min.js",
        ),
    )


@register.simple_tag
def set_d3_js_path(val=None):
    return static_or_path(
        getattr(settings, "ADMIN_CHARTS_D3_JS_PATH", "https://unpkg.com/d3@3.3.13/d3.min.js"),
    )


@register.simple_tag
def get_control_form(chart, user):
    return chart.get_control_form_raw(user=user)
