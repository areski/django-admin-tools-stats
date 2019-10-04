
from django import template
from django.template.loader import render_to_string
from django.conf import settings

from ..modules import get_active_graph


register = template.Library()


@register.simple_tag(takes_context=True)
def chart_containers(context):
    if 'admin_tools.dashboard' not in settings.INSTALLED_APPS:
        context['charts'] = get_active_graph()
        return render_to_string("admin_tools_stats/chart_containers.html", context.flatten())
