class ProxyModuleBase(object):
    """ Doc """

    proxy_object = None
    proxy_request_object = None
    proxy_respone_object = None
    current_context = None

    def __init__(self, run_contexts=[], context=None,
                    request_object=None, response_object=None):
        """ Doc """
        self.run_contexts = run_contexts
        self.context = context
        self.request_object = request_object
        self.response_object = response_object

    def onRequest(self, **keywords):
        """ Doc """
        print "Request: %s" % keywords

    def onResponse(self, **keywords):
        """ Doc """
        print "Response: %s" % keywords

    def run(self, **keywords):
        """ Doc """
        options =   {
                    'request' : self.onRequest,
                    'response' : self.onResponse,
                    }
        if self.context in self.run_contexts:
            options[self.context](**keywords)
        else:
            print "not my turn yet"


