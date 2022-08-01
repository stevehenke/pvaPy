#!/usr/bin/env python

import time
import numpy as np
import pvaccess as pva

# AD Image Utility class
class AdImageUtility:

    # Area detector color modes values. Source: https://github.com/areaDetector/ADCore/blob/master/ADApp/ADSrc/NDArray.h#L29
    COLOR_MODE_MONO = 0 # [NX, NY]
    COLOR_MODE_RGB1 = 2 # [3, NX, NY]
    COLOR_MODE_RGB2 = 3 # [NX, 3, NY]
    COLOR_MODE_RGB3 = 4 # [NX, NY, 3]

    COLOR_MODES = {
        COLOR_MODE_MONO : "MONO",
        COLOR_MODE_RGB1 : "RGB1",
        COLOR_MODE_RGB2 : "RGB2",
        COLOR_MODE_RGB3 : "RGB3",
    }

    NTNDA_DATA_FIELD_KEY_MAP = {
        np.dtype('uint8')   : 'ubyteValue',
        np.dtype('int8')    : 'byteValue',
        np.dtype('uint16')  : 'ushortValue',
        np.dtype('int16')   : 'shortValue',
        np.dtype('uint32')  : 'uintValue',
        np.dtype('int32')   : 'intValue',
        np.dtype('uint64')  : 'ulongValue',
        np.dtype('int64')   : 'longValue',
        np.dtype('float32') : 'floatValue',
        np.dtype('float64') : 'doubleValue'
    }

    PVA_DATA_TYPE_MAP = {
        np.dtype('uint8')   : [pva.UBYTE],
        np.dtype('int8')    : [pva.BYTE],
        np.dtype('uint16')  : [pva.USHORT],
        np.dtype('int16')   : [pva.SHORT],
        np.dtype('uint32')  : [pva.UINT],
        np.dtype('int32')   : [pva.INT],
        np.dtype('uint64')  : [pva.ULONG],
        np.dtype('int64')   : [pva.LONG],
        np.dtype('float32') : [pva.FLOAT],
        np.dtype('float64') : [pva.DOUBLE]
    }

    @classmethod
    def reshapeNtNdArray(cls, ntnda):
        """ Reshape area detector numpy array. """
        # Get color mode
        imageId = ntnda['uniqueId']
        attributes = ntnda['attribute']
        colorMode = None
        for attribute in attributes:
            if attribute['name'] == 'ColorMode':
                colorMode = attribute['value'][0]['value']
                break

        # Get dimensions
        dims = ntnda['dimension']
        nDims = len(dims)

        if colorMode is None and nDims > 2:
            raise pva.InvalidArgument('NTNDArray does not contain ColorMode attribute.')
        else:
            colorMode = cls.COLOR_MODE_MONO

        if nDims == 0:
            nx = None
            ny = None
            nz = None
            image = None
            colorMode = None
            fieldKey = None
            return (imageId,image,nx,ny,nz,colorMode,fieldKey)
        elif nDims == 2 and colorMode == cls.COLOR_MODE_MONO:
            nx = dims[0]['size']
            ny = dims[1]['size']
            nz = None
        elif nDims == 3 and colorMode == cls.COLOR_MODE_RGB1:
            nx = dims[1]['size']
            ny = dims[2]['size']
            nz = dims[0]['size']
        elif nDims == 3 and colorMode == cls.COLOR_MODE_RGB2:
            nx = dims[0]['size']
            ny = dims[2]['size']
            nz = dims[1]['size']
        elif nDims == 3 and colorMode == cls.COLOR_MODE_RGB3:
            nx = dims[0]['size']
            ny = dims[1]['size']
            nz = dims[2]['size']
        else:
            raise pva.InvalidArgument(f'Invalid dimensions {dims} and color mode {colorMode} combination.')

        # Alternative ways of getting the image array and type
        fieldKey = ntnda.getSelectedUnionFieldName()
        ###fieldKey = next(iter(ntnda['value'][0].keys()))

        #imageUnionField = ntnda.getUnion()
        #image = imageUnionField[fieldKey]
        ##image = ntnda.getUnion()[fieldKey]
        ###image = next(iter(ntnda['value'][0].values()))
        image = ntnda['value'][0][fieldKey]

        if colorMode == cls.COLOR_MODE_MONO:
            image = np.reshape(image, (ny, nx))

        elif colorMode == cls.COLOR_MODE_RGB1:
            image = np.reshape(image, (ny, nx, nz))

        elif colorMode == cls.COLOR_MODE_RGB2:
            image = np.reshape(image, (ny, nz, nx))
            image = np.swapaxes(image, 2, 1)

        elif colorMode == cls.COLOR_MODE_RGB3:
            image = np.reshape(image, (nz, ny, nx))
            image = np.swapaxes(image, 0, 2)
            image = np.swapaxes(image, 0, 1)

        else:
            raise pva.InvalidArgument('Unsupported color mode: {colorMode}')

        return (imageId,image,nx,ny,nz,colorMode,fieldKey)

    @classmethod
    def getNtNdArrayDataFieldKey(cls, image):
        return cls.NTNDA_DATA_FIELD_KEY_MAP.get(image.dtype)

    @classmethod
    def generateNtNdArray2D(cls, imageId, image, extraFieldsPvObject=None):
        if extraFieldsPvObject is None:
            ntnda = pva.NtNdArray()
        else:
            ntnda = pva.NtNdArray(extraFieldsPvObject.getStructureDict())

        dataFieldKey = cls.NTNDA_DATA_FIELD_KEY_MAP.get(image.dtype)
        pvaDataType = cls.PVA_DATA_TYPE_MAP.get(image.dtype)
        ny, nx = image.shape
        data = image.flatten()
        ntnda['uniqueId'] = int(imageId)
        dims = [pva.PvDimension(nx, 0, nx, 1, False), \
                pva.PvDimension(ny, 0, ny, 1, False)]
        ntnda['dimension'] = dims
        size = nx*ny*data.itemsize
        ntnda['compressedSize'] = size
        ntnda['uncompressedSize'] = size
        ts = pva.PvTimeStamp(time.time())
        ntnda['timeStamp'] = ts
        ntnda['dataTimeStamp'] = ts
        ntnda['descriptor'] = 'Image generated by PvaPy'

        pvaTypeKey = cls.NTNDA_DATA_FIELD_KEY_MAP.get(image.dtype)
        # Alternative way of setting data
        #u = pva.PvObject({dataFieldKey : pvaDataType}, {dataFieldKey : data})
        #ntnda.setUnion(u)
        ntnda['value'] = {pvaTypeKey : data}
        attrs = [pva.NtAttribute('ColorMode', pva.PvInt(0))]
        ntnda['attribute'] = attrs
        if extraFieldsPvObject is not None:
            ntnda.set(extraFieldsPvObject)
        return ntnda

    # Assumes new image is of the same data type as the old one
    # and replaces image data, dimensions, etc. in the provided NtNd Array
    @classmethod
    def replaceNtNdArrayImage2D(cls, ntnda, imageId, image, extraFieldsPvObject=None):
        dataFieldKey = cls.NTNDA_DATA_FIELD_KEY_MAP.get(image.dtype)
        pvaDataType = cls.PVA_DATA_TYPE_MAP.get(image.dtype)
        data = image.flatten()
        ntnda['uniqueId'] = int(imageId)

        ny, nx = image.shape
        dims = ntnda['dimension']
        if dims[0]['size'] != nx or dims[1]['size'] != ny:
            dims = [pva.PvDimension(nx, 0, nx, 1, False), \
                    pva.PvDimension(ny, 0, ny, 1, False)]
            ntnda['dimension'] = dims
            size = nx*ny*data.itemsize
            ntnda['compressedSize'] = size
            ntnda['uncompressedSize'] = size
        ts = pva.PvTimeStamp(time.time())
        ntnda['timeStamp'] = ts
        ntnda['dataTimeStamp'] = ts

        u = pva.PvObject({dataFieldKey : pvaDataType}, {dataFieldKey : data})
        ntnda.setUnion(u)
        if extraFieldsPvObject is not None:
            ntnda.set(extraFieldsPvObject)
        return ntnda

