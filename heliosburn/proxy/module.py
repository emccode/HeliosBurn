import io
import sys
from zope.interface import implements
from zope.interface import Interface
from twisted.internet import defer
from twisted.plugin import IPlugin
from twisted.plugin import getPlugins
from twisted.plugin import pluginPackagePaths
from twisted.python import log
import modules

"""
Simple Interface to handling proxy requests and responses via class instances.
To use, make a new class that inherits ProxyModuleBase. Each context
represents a step in the proxy request or client response process.

"""


class IModule(Interface):
    """
    Module interface defined for proxy modules.

    .run() is called in every (defined) context.

    Currently implemented contexts:
        'request'
        'response'
    """

    def get_name(self):
        """
        Returns the unique name of the module
        @rtype: C{string}
        """

    def handle_request(self, **keywords):
        """
        Called to handle proxy request event
        """

    def handle_status(self, **keywords):
        """
        Called to handle proxy status event
        """

    def handle_response(self, **keywords):
        """
        Called to handle proxy response event
        """

    def handle_header(self, **keywords):
        """
        Called to handle proxy header event
        """

    def reset(self, **keywords):
        """
        If the module maintains state, this method is called to reset
        the current state of the module

        """


class AbstractModule(object):
    implements(IPlugin, IModule)

    """
    Base class used to implement a twisted plugin based IModule interface.

    """

    def __init__(self):
        """
        Initialization of a proxy module instance
        """

        self.name = self.__class__.__name__
        self.log = log

    def get_name(self):
        """
        Returns the unique name of the module
        """
        return self.name

    def set_log(self, log):
        self.log = log

    def log(self):
        return self.log

    def handle_request(self, request, **keywords):
        """
        Called by to handle proxy request event
        """
        self.log.msg("Request: %s" % keywords)
        return request

    def handle_response(self, response,  **keywords):
        """
        Called to handle proxy response event
        """
        self.log.msg("Response: %s" % keywords)
        return response

    def handle_status(self, status, **keywords):
        """
        Called to handle proxy status event
        """
        self.log.msg("Status: %s" % keywords)
        return status

    def handle_header(self, header, **keywords):
        """
        Called to handle proxy header event
        """
        self.log.msg("header: %s" % keywords)
        return header

    def reset(self, **keywords):
        """
        If the module maintains state, this method is called to reset
        the current state of the module
        """
        self.log.msg("Response: %s" % keywords)

    def getProtocol(self):
        if self.context in ['request', 'response']:
            return self.request_object.clientproto
        else:
            raise Exception('Invalid context')

    def setProtocol(self, protocol):
        if self.context in ['request', 'response']:
            self.request_object.clientproto = protocol
        else:
            raise Exception('Invalid context')

    def getMethod(self):
        if self.context in ['request', 'response']:
            return self.request_object.method
        else:
            raise Exception('Invalid context')

    def setMethod(self, method):
        if self.context in ['request']:
            self.request_object.method = method
        else:
            raise Exception('Invalid context')

    def getURI(self):
        if self.context in ['request', 'response']:
            return self.request_object.uri
        else:
            raise Exception('Invalid context')

    def setURI(self, uri):
        if self.context in ['request']:
            self.request_object.uri = uri
        else:
            raise Exception('Invalid context')

    def getStatusCode(self):
        if self.context in ['response']:
            return self.request_object.code
        else:
            raise Exception('Invalid context')

    def setStatusCode(self, status_code):
        if self.context in ['response']:
            self.request_object.code = status_code
        else:
            raise Exception('Invalid context')

    def getStatusDescription(self):
        if self.context in ['response']:
            return self.request_object.code_message
        else:
            raise Exception('Invalid context')

    def setStatusDescription(self, status_description):
        if self.context in ['response']:
            self.request_object.code_message = status_description
        else:
            raise Exception('Invalid context')

    def getAllHeaders(self):
        if self.context == 'request':
            return self.request_object.requestHeaders.getAllRawHeaders()
        elif self.context == 'response':
            return self.request_object.responseHeaders.getAllRawHeaders()
        else:
            raise Exception('Invalid context')

    def hasHeader(self, name):
        if self.context == 'request':
            return self.request_object.requestHeaders.hasHeader(name)
        elif self.context == 'response':
            return self.request_object.responseHeaders.hasHeader(name)
        else:
            raise Exception('Invalid context')

    def getHeader(self, name):
        if self.context == 'request':
            return self.request_object.requestHeaders.getRawHeaders(name)
        elif self.context == 'response':
            return self.request_object.responseHeaders.getRawHeaders(name)
        else:
            raise Exception('Invalid context')

    def removeHeader(self, name):
        if self.context == 'request':
            return self.request_object.requestHeaders.removeHeader(name)
        elif self.context == 'response':
            return self.request_object.responseHeaders.removeHeader(name)
        else:
            raise Exception('Invalid context')

    def setHeader(self, name, value):
        if self.context == 'request':
            return self.request_object.requestHeaders.setRawHeaders(name,
                                                                    [value])
        elif self.context == 'response':
            return self.request_object.responseHeaders.setRawHeaders(name,
                                                                     [value])
        else:
            raise Exception('Invalid context')

    def getContent(self):
        if self.context in ['request', 'response']:
            if self.context == 'request':
                return self.request_object.content.getvalue()
            elif self.context == 'response':
                return self.request_object.response_content.getvalue()
        else:
            raise Exception('Invalid context')

    def setContent(self, content):
        if self.context in ['request', 'response']:
            self.setHeader('Content-Length', str(len(content)))
            self.request_object.content = io.BytesIO(content)
        else:
            raise Exception('Invalid context')


class Registry(object):

    def __init__(self, modules_list):
        self.modules_list = modules_list

        self.request = defer.Deferred()
        self.response = defer.Deferred()
        self.status = defer.Deferred()
        self.header = defer.Deferred()

        self.request.addCallback(self.handle_request)
        self.response.addCallback(self.handle_response)
        self.status.addCallback(self.handle_status)
        self.header.addCallback(self.handle_header)

        plugins = {plugin.get_name(): plugin for plugin in
                   getPlugins(IModule, modules)}

        self.modules = {}
        for module in modules_list['modules']:
            module_name = module['name']
            plugin = plugins[module_name]
            plugin.set_log(self.log)
            self.modules[module_name] = plugin
            self.request.addCallback(plugin.handle_request)
            self.response.addCallback(plugin.handle_response)
            self.status.addCallback(plugin.handle_status)
            self.header.addCallback(plugin.handle_header)

        log.msg("loaded modules: %s" % self.modules)

    def handle_request(self, request):

        """
        Executes the handle_request method of all currently active modules
        """
        log.msg("Started handling of request: %s" % request)

        return request

    def handle_response(self, response):

        """
        Executes the handle_response method of all currently active modules
        """
        log.msg("Started handling of response: %s" % response)

        return response

    def handle_status(self, status):

        """
        Executes the handle_status method of all currently active modules
        """

        log.msg("Started handling of status: %s" % status)

        return status

    def handle_header(self, header):

        """
        Executes the handle_header method of all currently active modules
        """

        log.msg("Started handling of header: %s" % header)
        return header

    def reset(self):

        """
        Executes the reset method of all currently active modules
        """
        for module in self.modules.values():
            module.reset()

