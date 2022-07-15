#!/usr/bin/env python

import time
import pvaccess as pva
from ..utility.loggingManager import LoggingManager

class DataConsumer:

    PROVIDER_TYPE_MAP = { 'pva' : pva.PVA, 'ca' : pva.CA }

    def __init__(self, consumerId, channelName, providerType=pva.PVA, serverQueueSize=0, distributorPluginName='pydistributor', distributorGroupId=None, distributorSetId=None, distributorTriggerFieldName=None, distributorUpdates=None, distributorUpdateMode=None, pvObjectQueue=None, dataProcessor=None):
        self.logger = LoggingManager.getLogger('consumer-{}'.format(consumerId))
        self.consumerId = consumerId
        providerType = self.PROVIDER_TYPE_MAP.get(providerType.lower(), pva.PVA)
        self.logger.debug(f'Channel {channelName} provider type: {providerType}')
        self.channel = pva.Channel(channelName, providerType)
        self.serverQueueSize = serverQueueSize
        self.logger.debug(f'Server queue size: {serverQueueSize}')
        self.distributorPluginName = distributorPluginName
        self.distributorGroupId = distributorGroupId 
        self.distributorSetId = distributorSetId 
        self.distributorTriggerFieldName = distributorTriggerFieldName
        self.distributorUpdates = distributorUpdates 
        self.distributorUpdateMode = distributorUpdateMode
        self.pvObjectQueue = pvObjectQueue
        if pvObjectQueue is not None:
            self.logger.debug(f'Using PvObjectQueue of size: {pvObjectQueue.maxLength}')
        self.dataProcessor = dataProcessor
        self.startTime = None
        self.endTime = None

        # If first object is ignored, stats will be adjusted
        self.nReceivedOffset = 0
        if self.dataProcessor and hasattr(self.dataProcessor, 'ignoreFirstObject') and self.dataProcessor.ignoreFirstObject:
            self.nReceivedOffset = 1

        self.logger.debug(f'Created data consumer {consumerId}')

    def getPvMonitorRequest(self):
        recordStr = ''
        if self.serverQueueSize > 0:
            recordStr = f'record[queueSize={self.serverQueueSize}]'
        distributorStr = ''
        if self.distributorGroupId \
                or self.distributorSetId \
                or self.distributorTriggerFieldName \
                or self.distributorUpdates \
                or self.distributorUpdateMode:
            distributorStr = f'_[{self.distributorPluginName}='
        if self.distributorGroupId:
            distributorStr += f'group:{self.distributorGroupId};'
        if self.distributorSetId:
            distributorStr += f'set:{self.distributorSetId};'
        if self.distributorTriggerFieldName:
            distributorStr += f'trigger:{self.distributorTriggerFieldName};'
        if self.distributorUpdates:
            distributorStr += f'updates:{self.distributorUpdates};'
        if self.distributorUpdateMode:
            distributorStr += f'mode:{self.distributorUpdateMode};'

        request = f'{recordStr}field()'
        if distributorStr:
            # Strip last ';' character
            distributorStr = distributorStr[0:-1] + ']'
            request = f'{recordStr}field({distributorStr})'
        return request

    def process(self, pv):
        try:
            if self.dataProcessor:
                self.dataProcessor.process(pv)
        except Exception as ex:
            self.logger.error(f'Processing error: {ex}')

    # Return true if object was processed, False otherwise
    def processFromQueue(self, waitTime):
        if self.pvObjectQueue is not None:
            try:
                pvObject = self.pvObjectQueue.get(waitTime)
                self.process(pvObject)
                return True
            except pva.QueueEmpty as ex:
                # Ignore empty queue
                pass
        return False

    def getMonitorStats(self):
        return self.channel.getMonitorCounters()
        
    def getQueueStats(self):
        if self.pvObjectQueue is not None:
            return self.pvObjectQueue.getCounters()
        return {}
        
    def getProcessorStats(self):
        if self.dataProcessor:
            return self.dataProcessor.getStats()
        return {}

    def getStats(self):
        monitorStats = self.getMonitorStats()
        queueStats = self.getQueueStats()
        processorStats = self.getProcessorStats()
        receivedRate = 0
        receivingTime = processorStats.get('receivingTime', 0)
        nReceived = monitorStats.get('nReceived', 0)-self.nReceivedOffset
        if receivingTime > 0 and nReceived >= 0:
            receivedRate = nReceived/receivingTime
        monitorStats['receivedRate'] = receivedRate
        return {'monitorStats' : monitorStats, 'queueStats' : queueStats, 'processorStats' : processorStats}

    def getConsumerId(self):
        return self.consumerId
 
    def start(self):
        request = self.getPvMonitorRequest()
        self.logger.debug(f'Using request string {request}')
        if self.pvObjectQueue is not None and isinstance(self.pvObjectQueue, pva.PvObjectQueue):
            self.logger.debug('Starting queue monitor')
            self.channel.qMonitor(self.pvObjectQueue, request)
        else:
            self.logger.debug('Starting process monitor')
            self.channel.monitor(self.process, request)
        if self.dataProcessor:
            self.dataProcessor.start()
        self.startTime = time.time()

    def stop(self):
        self.channel.stopMonitor()
        if self.dataProcessor:
            self.dataProcessor.stop()
        self.endTime = time.time()

