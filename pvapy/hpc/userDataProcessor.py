#!/usr/bin/env python

import pvaccess as pva
from ..utility.loggingManager import LoggingManager

class UserDataProcessor:
    ''' 
    Class that serves as a base for any user implementation of a processor class
    suitable for usage with the streaming framework. Interface methods
    will be called at different stages of the processing workflow.\n
    The following variables will be set after processor instance is created and before processing starts:\n
    \t\- *logger* (logging.Logger) : logger object\n
    \t\- *processorId* (int)       : processor id\n
    \t\- *inputChannel* (str)      : input channel\n
    \t\- *outputChannel* (str)     : output channel\n
    \t\- *objectIdField* (str)     : name of the object id field\n
    \t\- *pvaServer* (PvaServer)   : PVA Server instance for publishing output objects\n
    \t\- *metadataQueueMap* (dict) : dictionary of available PvObject queues for metadata channels\n
  
    **UserDataProcessor(configDict={})**

    :Parameter: *configDict* (dict) - dictionary containing configuration parameters
    '''

    def __init__(self, configDict={}):
        '''
        Constructor.
        '''
        self.logger = LoggingManager.getLogger(self.__class__.__name__)
        self.checkedUpdate = True

        # The following will be set after processor gets instantiated.
        self.processorId = None
        self.pvaServer = None
        self.inputChannel = None
        self.outputChannel = None
        self.objectIdField = None
        self.metadataQueueMap = {}

    def start(self):
        '''
        Method invoked at processing startup.
        '''
        pass

    def configure(self, configDict):
        ''' 
        Method invoked at user initiated runtime configuration changes.

        :Parameter: *configDict* (dict) - dictionary containing configuration parameters
        '''
        pass

    def process(self, pvObject):
        ''' 
        Method invoked every time input channel updates its PV record.

        :Parameter: *pvObject* (PvObject) - input channel object
        '''
        self.logger.debug(f'Processor {self.processorId} processing object {pvObject[self.objectIdField]}')
        self.updateOutputChannel(pvObject)
        return pvObject

    def stop(self):
        '''
        Method invoked at processing shutdown.
        '''
        pass
    
    def resetStats(self):
        ''' 
        Method invoked at user initiated application statistics reset. 
        '''
        pass

    def getStats(self):
        '''
        Method invoked periodically for generating application statistics.
        
        :Returns: Dictionary containing application statistics parameters
        '''
        return {}

    def getStatsPvaTypes(self):
        '''
        Method invoked at processing startup. It defines user application part
        of the status PvObject published on the status PVA channel.
        
        :Returns: Dictionary containing PVA types for the application statistics parameters
        '''
        return {}

    def getOutputPvObjectType(self, pvObject):
        '''
        Method invoked at processing startup that defines PVA structure for
        the output (processed) PvObject. This method is called immediately after
        receiving the first input channel update. 
        
        There is no need to override this method if the structure of input and
        output objects are the same, or if the application will not publish 
        processing output.
        
        :Parameter: *pvObject* (PvObject) - input channel object
        :Returns: PvObject with the same structure as generated by the process() method
        '''
        return None

    def updateOutputChannel(self, pvObject):
        '''
        Method that can be used for publishing processed object on the 
        output PVA channel. It should be invoked by the user application itself
        as part of the process() method. Typically, there should be no need for
        overriding this method in the derived class.

        :Parameter: *pvObject* (PvObject) - processed object 
        '''
        if not self.outputChannel or not self.pvaServer:
            return
        if self.checkedUpdate:
            self.checkedUpdate = False
            self.pvaServer.update(self.outputChannel, pvObject)
        else:
            self.pvaServer.updateUnchecked(self.outputChannel, pvObject)

