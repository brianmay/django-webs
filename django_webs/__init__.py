# django-webs - high level web layer for django
# Copyright (C) 2008-2011 Brian May
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

from django.core.urlresolvers import reverse
from django.db import models as m
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.template import RequestContext, loader
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponseForbidden, Http404
from django.utils.translation import ugettext as _

class breadcrumb(object):
    def __init__(self, url, name):
        self.url = url
        self.name = name

types = { }

def get_web_from_object(self):
    type_name = type(self).__name__
    return types[type_name]()

class web_metaclass(type):
    def __new__(cls, name, bases, attrs):
        result = type.__new__(cls, name, bases, attrs)
        if "web_id" in attrs:
            web_id = attrs["web_id"]
            types[web_id] = result
        return result

################
# BASE METHODS #
################
class web(object):
    __metaclass__ = web_metaclass
    app_label = None

    def assert_instance_type(self, instance):
        type_name = type(instance).__name__
        expected_type = self.web_id

        if type_name != expected_type:
            raise RuntimeError("Expected type %s but got '%s'"%(expected_type,type_name))

    @property
    def verbose_name(self):
        web_id = self.web_id
        return web_id.replace("_", " ")

    @property
    def verbose_name_plural(self):
        return self.verbose_name + 's'

    @property
    def perm_id(self):
        return self.web_id

    @property
    def url_prefix(self):
        return self.web_id

    @property
    def template_prefix(self):
        return self.web_id

    def has_name_perms(self, user, name):
        if user.is_authenticated() and user.has_perm('%s.%s_%s'%(self.app_label, name, self.perm_id)):
            return True
        else:
            return False

    def get_breadcrumbs(self):
        breadcrumbs = []
        breadcrumbs.append(breadcrumb(reverse("root"), _("Home")))
        return breadcrumbs

    def get_instance(self):
        return self.model()

    def pre_save(self, instance, form):
        self.assert_instance_type(instance)
        return True

    ###############
    # LIST ACTION #
    ###############

    def has_list_perms(self, user):
        return True

    @m.permalink
    def get_list_url(self):
        return(self.url_prefix+'_list',)

    def get_list_breadcrumbs(self):
        breadcrumbs = self.get_breadcrumbs()
        breadcrumbs.append(breadcrumb(reverse(self.url_prefix+"_list"), self.verbose_name_plural))
        return breadcrumbs

    def get_list_buttons(self, user):
        buttons = []

        if self.has_add_perms(user):
            buttons.append({
                'class': 'addlink',
                'text': 'Add %s'%(self.verbose_name),
                'url': self.get_add_url(),
            })

        return buttons

    ###############
    # VIEW ACTION #
    ###############

    def has_view_perms(self, user):
        return True

    # get the URL to display this object
    # note this may not always make sense
    @m.permalink
    def get_view_url(self, instance):
        self.assert_instance_type(instance)
        return(self.url_prefix+'_detail', [ str(instance.pk) ])

    # get the breadcrumbs to show while displaying this object
    def get_view_breadcrumbs(self, instance):
        self.assert_instance_type(instance)
        breadcrumbs = self.get_list_breadcrumbs()
        breadcrumbs.append(breadcrumb(self.get_view_url(instance), instance))
        return breadcrumbs

    def get_view_buttons(self, user, instance):
        self.assert_instance_type(instance)
        buttons = []

        if self.has_edit_perms(user):
            buttons.append({
                'class': 'changelink',
                'text': 'Edit',
                'url': self.get_edit_url(instance),
            })

        if self.has_delete_perms(user):
            buttons.append({
                'class': 'deletelink',
                'text': 'Delete',
                'url': self.get_delete_url(instance),
            })

        return buttons

    ##############
    # ADD ACTION #
    ##############

    def has_add_perms(self, user):
        return self.has_name_perms(user, "add")

    @m.permalink
    def get_add_url(self):
        return(self.url_prefix+"_add",)

    def get_add_breadcrumbs(self, **kwargs):
        breadcrumbs = self.get_list_breadcrumbs()
        breadcrumbs.append(breadcrumb(self.get_add_url(**kwargs), "add"))
        return breadcrumbs

    ###############
    # EDIT ACTION #
    ###############

    def has_edit_perms(self, user):
        return self.has_name_perms(user, "edit")

    # get the URL to edit this object
    @m.permalink
    def get_edit_url(self, instance):
        self.assert_instance_type(instance)
        return(self.url_prefix+'_edit', [ str(instance.pk) ])

    # find url we should go to after editing this object
    def get_edit_finished_url(self, instance):
        self.assert_instance_type(instance)
        return self.get_view_url(instance)

    # get breadcrumbs to show while editing this object
    def get_edit_breadcrumbs(self, instance):
        self.assert_instance_type(instance)
        breadcrumbs = self.get_view_breadcrumbs(instance)
        breadcrumbs.append(breadcrumb(self.get_edit_url(instance), "edit"))
        return breadcrumbs

    #################
    # DELETE ACTION #
    #################

    def has_delete_perms(self, user):
        return self.has_name_perms(user, "delete")

    # get the URL to delete this object
    @m.permalink
    def get_delete_url(self, instance):
        self.assert_instance_type(instance)
        return(self.url_prefix+'_delete', [ str(instance.pk) ])

    # find url we should go to after deleting object
    @m.permalink
    def get_delete_finished_url(self, instance):
        self.assert_instance_type(instance)
        return(self.url_prefix+"_list",)

    # get breadcrumbs to show while deleting this object
    def get_delete_breadcrumbs(self, instance):
        self.assert_instance_type(instance)
        breadcrumbs = self.get_view_breadcrumbs(instance)
        breadcrumbs.append(breadcrumb(self.get_delete_url(instance), "delete"))
        return breadcrumbs

    #####################
    # PERMISSION CHECKS #
    #####################

    def permission_denied_response(self, request, breadcrumbs, error_list):
        t = loader.get_template('%s/error.html'%"django_webs")
        c = RequestContext(request, {
                'title': 'Access denied',
                'error_list': error_list,
                'breadcrumbs': breadcrumbs
        })
        return HttpResponseForbidden(t.render(c))

    def check_list_perms(self, request, breadcrumbs):
        error_list = []
        if not self.has_list_perms(request.user):
            error_list.append("You cannot list %s objects"%(self.verbose_name))

        if len(error_list) > 0:
            return self.permission_denied_response(request, breadcrumbs, error_list)
        else:
            return None

    def check_view_perms(self, request, breadcrumbs):
        error_list = []
        if not self.has_view_perms(request.user):
            error_list.append("You cannot view a %s object"%(self.verbose_name))

        if len(error_list) > 0:
            return self.permission_denied_response(request, breadcrumbs, error_list)
        else:
            return None

    def check_add_perms(self, request, breadcrumbs):
        error_list = []
        if not self.has_add_perms(request.user):
            error_list.append("You cannot add a %s object"%(self.verbose_name))

        if len(error_list) > 0:
            return self.permission_denied_response(request, breadcrumbs, error_list)
        else:
            return None

    def check_edit_perms(self, request, breadcrumbs):
        error_list = []
        if not self.has_edit_perms(request.user):
            error_list.append("You cannot edit a %s object"%(self.verbose_name))

        if len(error_list) > 0:
            return self.permission_denied_response(request, breadcrumbs, error_list)
        else:
            return None

    def check_delete_perms(self, request, breadcrumbs):
        error_list = []
        if not self.has_delete_perms(request.user):
            error_list.append("You cannot delete a %s object"%(self.verbose_name))

        if len(error_list) > 0:
            return self.permission_denied_response(request, breadcrumbs, error_list)
        else:
            return None

    #####################
    # GENERIC FUNCTIONS #
    #####################

    def object_list(self, request, form, table, template=None, kwargs={}, context={}):
        breadcrumbs = self.get_list_breadcrumbs(**kwargs)

        error = self.check_list_perms(request, breadcrumbs)
        if error is not None:
            return error

        if template is None:
            template='%s/object_list.html'%"django_webs"

        paginator = Paginator(table.rows, 50) # Show 50 objects per page

        # Make sure page request is an int. If not, deliver first page.
        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1

        # If page request (9999) is out of range, deliver last page of results.
        try:
            page_obj = paginator.page(page)
        except (EmptyPage, InvalidPage):
            page_obj = paginator.page(paginator.num_pages)

        defaults = {
                'web': self,
                'table': table,
                'page_obj': page_obj,
                'breadcrumbs': breadcrumbs,
        }

        if form is not None:
            defaults['form'] = form
            defaults['media'] = form.media

        defaults.update(context)
        return render_to_response(template, defaults,
                context_instance=RequestContext(request))

    def object_view(self, request, instance, template=None):
        self.assert_instance_type(instance)
        breadcrumbs = self.get_view_breadcrumbs(instance)

        error = self.check_view_perms(request, breadcrumbs)
        if error is not None:
            return error

        if template is None:
            template='%s/%s_detail.html'%(self.app_label,self.template_prefix)
        return render_to_response(template, {
                'object': instance,
                'web': self,
                'breadcrumbs': breadcrumbs,
                },context_instance=RequestContext(request))

    def object_add(self, request, template=None, kwargs={}):
        breadcrumbs = self.get_add_breadcrumbs(**kwargs)

        if template is None:
            template='%s/object_edit.html'%"django_webs"

        error = self.check_add_perms(request, breadcrumbs)
        if error is not None:
            return error

        if request.method == 'POST':
            form = self.form(request.POST, request.FILES)

            if form.is_valid():
                valid = True
                instance = form.save(commit=False)
                valid = self.pre_save(instance=instance, form=form)

                if valid:
                    instance.save()
                    url = self.get_edit_finished_url(instance)
                    url = request.GET.get("next",url)
                    return HttpResponseRedirect(url)
        else:
            instance = self.get_instance(**kwargs)
            self.assert_instance_type(instance)
            form = self.form(instance=instance)

        return render_to_response(template, {
                'object': None, 'web': self,
                'breadcrumbs': breadcrumbs,
                'form' : form,
                'media' : form.media,
                },context_instance=RequestContext(request))

    def object_edit(self, request, instance, template=None):
        self.assert_instance_type(instance)
        breadcrumbs = self.get_edit_breadcrumbs(instance)

        if template is None:
            template='%s/object_edit.html'%"django_webs"

        error = self.check_edit_perms(request, breadcrumbs)
        if error is not None:
            return error

        if request.method == 'POST':
            form = self.form(request.POST, request.FILES, instance=instance)
            if form.is_valid():
                valid = True
                instance = form.save(commit=False)
                valid = self.pre_save(instance=instance, form=form)

                if valid:
                    url = self.get_edit_finished_url(instance)
                    url = request.GET.get("next",url)
                    instance.save()
                    return HttpResponseRedirect(url)
        else:
            form = self.form(instance=instance)

        return render_to_response(template, {
                'object': instance,
                'web': self,
                'breadcrumbs': breadcrumbs,
                'form' : form,
                'media' : form.media,
                },context_instance=RequestContext(request))

    def object_delete(self, request, instance, template=None):
        self.assert_instance_type(instance)
        breadcrumbs = self.get_delete_breadcrumbs(instance)

        if template is None:
            template='%s/object_confirm_delete.html'%"django_webs"

        error = self.check_delete_perms(request, breadcrumbs)
        if error is not None:
            return error

        errorlist = []
        if request.method == 'POST':
            errorlist = instance.check_delete()
            if len(errorlist) == 0:
                url = self.get_delete_finished_url(instance)
                url = request.GET.get("next",url)
                instance.delete()
                return HttpResponseRedirect(url)

        return render_to_response(template, {
                'object': instance,
                'breadcrumbs': breadcrumbs,
                'errorlist': errorlist,
                },context_instance=RequestContext(request))


