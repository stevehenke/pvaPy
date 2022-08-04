
import time
import numpy as np
import pvaccess as pva
from pvapy.hpc.adImageProcessor import AdImageProcessor
from pvapy.utility.floatWithUnits import FloatWithUnits

# Example for HPC AD Image Processor
class HpcAdImageProcessor(AdImageProcessor):

    def __init__(self, configDict={}):
        AdImageProcessor.__init__(self, configDict)
        self.nProcessed = 0
        self.processingTime = 0
        self.logger.debug('Created HpcAdImageProcessor')

    # Method called at start
    def start(self):
        pass

    # Configure user processor
    def configure(self, kwargs):
        self.logger.debug(f'Configuration update: {kwargs}')

    # Process monitor update
    def process(self, pvObject):
        t0 = time.time()
        (frameId,image,nx,ny,nz,colorMode,fieldKey) = self.reshapeNtNdArray(pvObject)
        if nx is None:
            self.logger.debug(f'Frame id {frameId} contains an empty image.')
            return pvObject
        self.logger.debug(f'Consumer {self.processorId} data sum: {image.sum()} (frame id: {frameId})')
        image2 = np.swapaxes(image, 0, 1)
        # Simply replacing image data is slightly faster than 
        # generating a new one
        #pvObject2 = self.generateNtNdArray2D(frameId, image2)
        pvObject2 = self.replaceNtNdArrayImage2D(pvObject, frameId, image2)
        self.updateOutputChannel(pvObject2)
        t1 = time.time()
        self.nProcessed += 1
        self.processingTime += (t1-t0)
        return pvObject2

    # Method called at shutdown
    def stop(self):
        pass

    # Reset statistics for user processor
    def resetStats(self):
        self.nProcessed = 0
        self.processingTime = 0

    # Retrieve statistics for user processor
    def getStats(self):
        processingRate = 0
        if self.nProcessed > 0:
            processingRate = self.nProcessed/self.processingTime
        return { 
            'nProcessed' : self.nProcessed,
            'processingTime' : FloatWithUnits(self.processingTime, 's'),
            'processingRate' : FloatWithUnits(processingRate, 'fps')
        }

    # Define PVA types for different stats variables
    def getStatsPvaTypes(self):
        return { 
            'nProcessed' : pva.UINT,
            'processingTime' : pva.DOUBLE,
            'processingRate' : pva.DOUBLE
        }

    # Define PVA types for output object
    # This method does not need to be implemented if output
    # object has the same structure as the input object
    def getOutputPvaTypes(self):
        return {}

