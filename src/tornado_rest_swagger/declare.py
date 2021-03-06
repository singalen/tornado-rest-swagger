#!/usr/bin/python
# -*- coding: utf-8 -*-
import inspect
import re
from functools import wraps
import epydoc.markup

__author__ = 'flier'


class rest_api(object):
    def __init__(self, func_or_name, summary=None, notes=None, responseClass=None, errors=None, **kwds):
        self.summary = summary
        self.notes = notes
        self.responseClass = responseClass
        self.errors = errors or []

        self.kwds = kwds

        if inspect.isfunction(func_or_name) or inspect.ismethod(func_or_name):
            self.__bind__(func_or_name)
            self.rest_api = self
            self.name = func_or_name.__name__
        elif isinstance(func_or_name, basestring):
            self.func = None
            self.name = func_or_name
        #elif isinstance(func_or_name, RequestHandler): TODO: implement @rest_api for RequestHandler classes.
        #    methods = [method for method in {'get', 'put', 'delete', 'post'}.intersection(dir(object)) if callable(getattr(object, method))]
        #    for m in methods:
        #        dummy = rest_api(m)

    def __bind__(self, func):
        self.func = func

        self.__name__ = func.__name__
        self.func_args, self.func_varargs, self.func_keywords, self.func_defaults = inspect.getargspec(func)
        self.func_args = self.func_args

        if len(self.func_args) > 0 and self.func_args[0] == 'self':
            self.func_args = self.func_args[1:]

        self.params = dict([
            (arg, {
                'name': arg,
                'required': True,
                'paramType': 'path',
                'dataType': 'string'
            })
            for arg in self.func_args
        ])

        self.raises = dict()

        doc = self.parse_docstring(inspect.getdoc(self.func) or '')

        if self.summary is None:
            self.summary = doc.summary()[0].to_plaintext(None)

        if self.summary:
            self.summary = self.summary.strip()

        if self.notes is None:
            self.notes = doc.to_plaintext(None)

        # TODO: There's apparently no way to get ALL the epydoc EXCEPT for a fields list.
        # So currently notes hold some garbage.
        if self.notes:
            self.notes = self.notes.strip()

    def __call__(self, *args, **kwds):
        if self.func:
            return self.func(*args, **kwds)

        func = args[0]

        self.__bind__(func)

        @wraps(func)
        def __wrapper__(*args, **kwds):
            return self.func(*args, **kwds)

        __wrapper__.rest_api = self

        return __wrapper__

    def parse_docstring(self, text):
        errors = []

        doc = epydoc.markup.parse(text, markup='epytext', errors=errors)

        _, fields = doc.split_fields(errors)

        for field in fields:
            tag = field.tag()
            arg = field.arg()
            body = field.body().to_plaintext(None).strip()

            if tag == 'param':
                self.params.setdefault(arg, {}).update({
                    'name': arg,
                    'description': body
                })

                if 'paramType' not in self.params[arg]:
                    self.params[arg]['paramType'] = 'query'
            elif tag == 'type':
                self.params.setdefault(arg, {}).update({
                    'name': arg,
                    'dataType': body
                })
            elif tag == 'paramtype':
                self.params.setdefault(arg, {}).update({
                    'paramType': body,
                })
            elif tag == 'rtype':
                self.responseClass = arg or body
            elif tag == 'raisetype':
                self.raises[arg] = body
            elif tag == 'raise':
                self.errors.append({
                    'code': arg,
                    'message': body,
                    'responseModel': self.raises[arg] if arg in self.raises else '',
                })
            elif tag == 'note':
                self.notes = body or arg
            elif tag == 'summary':
                self.summary = body or arg

        return doc


def __spec_path_regex_to_path(path_regex):
    """
    The smallest thing that could possibly work.
    """
    # path = path_regex.replace('%s', 'SOMETHING')
    return re.sub('.\?', '', path_regex)


def discover_rest_apis(host_handlers):
    for host, handlers in host_handlers:
        for spec in handlers:
            for (name, member) in inspect.getmembers(spec.handler_class):
                if callable(member) and hasattr(member, 'rest_api'):
                    # FIXME: Commented out due to crash.
                    #yield spec._path % tuple(['{%s}' % arg for arg in member.rest_api.func_args]), inspect.getdoc(spec.handler_class)
                    yield __spec_path_regex_to_path(spec._path), inspect.getdoc(spec.handler_class)

                    break


def find_rest_api(host_handlers, path):
    for host, handlers in host_handlers:
        for spec in handlers:
            for (name, member) in inspect.getmembers(spec.handler_class):
                if callable(member) and hasattr(member, 'rest_api'):
                    # FIXME: Commented out due to crash.
                    spec_path = spec._path #% tuple(['{%s}' % arg for arg in member.rest_api.func_args])

                    # TODO: tornado.Application.__call__() matches requests in a different way.
                    # Looks like we need to rework this, starting with urls.handle_apidoc_urls().
                    if re.match(spec_path[1:], path):
                        operations = [member.rest_api for (name, member) in inspect.getmembers(spec.handler_class) if hasattr(member, 'rest_api')]

                        return spec, operations

                    continue
