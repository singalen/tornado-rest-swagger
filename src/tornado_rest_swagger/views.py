#!/usr/bin/python
# -*- coding: utf-8 -*-
import inspect
import urlparse
import json

import tornado.web
import tornado.template
import tornado_rest_swagger.models.plain_swagger
import tornado_rest_swagger.models.sqlalchemy_swagger

from tornado_rest_swagger.settings import SWAGGER_VERSION, URL_SWAGGER_API_LIST
from tornado_rest_swagger.declare import discover_rest_apis, find_rest_api

__author__ = 'flier'


def json_dumps(obj, pretty=False):
    return json.dumps(obj, sort_keys=True, indent=4, separators=(',', ': ')) if pretty else json.dumps(obj)


class SwaggerUIHandler(tornado.web.RequestHandler):
    def initialize(self, assets_path, **kwds):
        self.assets_path = assets_path

    def get_template_path(self):
        return self.assets_path

    def get(self):
        discovery_url = urlparse.urljoin(self.request.full_url(), self.reverse_url(URL_SWAGGER_API_LIST))

        self.render('index.html', discovery_url=discovery_url)


class SwaggerResourcesHandler(tornado.web.RequestHandler):
    """
    Swagger Resource Listing

    https://github.com/wordnik/swagger-core/wiki/Resource-Listing
    """

    def initialize(self, api_version, exclude_namespaces, **kwds):
        self.api_version = api_version
        self.exclude_namespaces = exclude_namespaces

    def get(self):
        self.set_header('content-type', 'application/json')

        apis = [{
            'path': path,
            'description': desc
        } for path, desc in discover_rest_apis(self.application.handlers)]

        u = urlparse.urlparse(self.request.full_url())

        resources = {
            'apiVersion': self.api_version,
            'swaggerVersion': SWAGGER_VERSION,
            'basePath': '%s://%s%s' % (u.scheme, u.netloc, u.path),
            'apis': apis
        }

        self.finish(json_dumps(resources, self.get_arguments('pretty')))


class SwaggerApiHandler(tornado.web.RequestHandler):
    """
    Swagger API Declaration

    https://github.com/wordnik/swagger-core/wiki/API-Declaration
    """

    def initialize(self, api_version, base_url, **kwds):
        self.api_version = api_version
        self.base_url = base_url

    def get_structure_reader(self, clazz):
        if any(n.__module__.startswith('sqlalchemy') for n in inspect.getmro(clazz)):
            return tornado_rest_swagger.models.sqlalchemy_swagger.SqlAlchemyModelReader()
        return tornado_rest_swagger.models.plain_swagger.PlainModelReader()

    def read_class_structure(self, class_name):
        clazz = self.get_class(class_name)
        return self.get_structure_reader(clazz).read(clazz)

    def get(self, path):
        result = find_rest_api(self.application.handlers, path)

        if result is None:
            raise tornado.web.HTTPError(404)

        spec, apis = result

        u = urlparse.urlparse(self.request.full_url())

        response_classes = set([api.responseClass for api in apis]) - {None, 'str', 'unicode', 'int'}

        spec = {
            'apiVersion': self.api_version,
            'swaggerVersion': SWAGGER_VERSION,
            'basePath': urlparse.urljoin(self.request.full_url(), self.base_url),
            'apis': [{
                'path': '/' + path,
                'description': spec.handler_class.__doc__,
                'operations': [{
                    'httpMethod': api.func.__name__.upper(),
                    'nickname': api.name,
                    'parameters': api.params.values(),
                    'summary': api.summary,
                    'notes': api.notes,
                    'responseClass': api.responseClass,
                    'errorResponses': api.errors,
                } for api in apis]
            }],
            'models': {c: self.read_class_structure(c) for c in response_classes}
        }

        self.set_header('content-type', 'application/json')

        self.finish(json_dumps(spec, self.get_arguments('pretty')))

    @staticmethod
    def get_class(clazz):
        parts = clazz.split('.')
        module = ".".join(parts[:-1])
        m = __import__(module)
        for comp in parts[1:]:
            m = getattr(m, comp)
        return m
