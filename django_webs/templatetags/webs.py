# django-webs - high level web layer for django
# Copyright (C) 2008-2009 Brian May
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django import template
from django.utils.safestring import mark_safe
from django.utils.http import urlquote
from django.utils.html import conditional_escape
from django.contrib.contenttypes.models import ContentType

from django_webs import get_web_from_object

from django.db.models import Q

register = template.Library()

@register.simple_tag
def get_view_url(instance):
    web = get_web_from_object(instance)
    return mark_safe(web.get_view_url(instance))

@register.simple_tag
def get_edit_url(instance):
    web = get_web_from_object(instance)
    return mark_safe(web.get_edit_url(instance))

@register.simple_tag
def get_delete_url(instance):
    web = get_web_from_object(instance)
    return mark_safe(web.get_delete_url(instance))

def defaults(context):
    return {
        'user': context['user'],
        'perms': context['perms'],
        'request': context['request'],
        'MEDIA_URL': context['MEDIA_URL'],
    }

@register.inclusion_tag('django_webs/show_error_list.html')
def show_error_list(error_list):
    return {
        'error_list': error_list,
    };

@register.inclusion_tag('django_webs/show_object_list.html', takes_context=True)
def show_list(context, table, rows, web, sort="sort"):
    dict = defaults(context)
    dict['table'] = table
    dict['web'] = web
    dict['rows'] = rows
    dict['sort'] = sort
    return dict

@register.inclusion_tag('django_webs/show_breadcrumbs.html')
def show_breadcrumbs(breadcrumbs):
        return {'breadcrumbs': breadcrumbs[:-1], 'object': breadcrumbs[-1] };


DOT='.'

@register.inclusion_tag('django_webs/pagination.html', takes_context=True)
def pagination(context, page_obj):
    paginator, page_num = page_obj.paginator, page_obj.number

    if paginator.num_pages <= 1:
        pagination_required = False
        page_range = []
    else:
        pagination_required = True
        ON_EACH_SIDE = 3
        ON_ENDS = 2

        # If there are 10 or fewer pages, display links to every page.
        # Otherwise, do some fancy
        if paginator.num_pages <= 10:
            page_range = range(1,paginator.num_pages+1)
        else:
            # Insert "smart" pagination links, so that there are always ON_ENDS
            # links at either end of the list of pages, and there are always
            # ON_EACH_SIDE links at either end of the "current page" link.
            page_range = []
            if page_num > (ON_EACH_SIDE + ON_ENDS + 1):
                page_range.extend(range(1, ON_ENDS+1))
                page_range.append(DOT)
                page_range.extend(range(page_num - ON_EACH_SIDE, page_num))
            else:
                page_range.extend(range(1, page_num))

            if page_num < (paginator.num_pages - ON_EACH_SIDE - ON_ENDS):
                page_range.extend(range(page_num, page_num + ON_EACH_SIDE + 1))
                page_range.append(DOT)
                page_range.extend(range(paginator.num_pages - ON_ENDS + 1, paginator.num_pages + 1))
            else:
                page_range.extend(range(page_num, paginator.num_pages + 1))

    if page_obj.number <= 1:
        page_prev = None
    else:
        page_prev = page_obj.number-1

    if page_obj.number >= page_obj.paginator.num_pages:
        page_next = None
    else:
        page_next = page_obj.number+1

    return {
        'pagination_required': pagination_required,
        'page_prev': page_prev,
        'page_next': page_next,
        'page_obj': page_obj,
        'page_range': page_range,
        'request': context['request'],
    }

class url_with_param_node(template.Node):
    def __init__(self, changes):
        self.changes = []
        for key, newvalue in changes:
            newvalue = template.Variable(newvalue)
            self.changes.append( (key,newvalue,) )

    def render(self, context):
        if 'request' not in context:
            raise template.TemplateSyntaxError, "request not in context"

        request = context['request']

        result = {}
        for key, newvalue in request.GET.items():
            result[key] = newvalue

        for key, newvalue in self.changes:
            newvalue = newvalue.resolve(context)
            result[key] = newvalue

        quoted = []
        for key, newvalue in result.items():
            quoted.append("%s=%s"%(urlquote(key),urlquote(newvalue)))

        return conditional_escape('?'+"&".join(quoted))

@register.tag
def url_with_param(parser, token):
    bits = token.split_contents()
    qschanges = []
    for i in bits[1:]:
        try:
            key, newvalue = i.split('=', 1);
            qschanges.append( (key,newvalue,) )
        except ValueError:
            raise template.TemplateSyntaxError, "Argument syntax wrong: should be key=value"
    return url_with_param_node(qschanges)

@register.inclusion_tag('django_webs/show_buttons.html', takes_context=True)
def show_list_buttons(context, web, user):
    dict = defaults(context)
    dict['buttons'] = web.get_list_buttons(user)
    return dict

@register.inclusion_tag('django_webs/show_buttons.html', takes_context=True)
def show_view_buttons(context, web, user, subject):
    dict = defaults(context)
    dict['buttons'] = web.get_view_buttons(user, subject)
    return dict
