'''
   Test Data Consumer.
'''
from unittest.mock import Mock
import tempfile
import os
import sys
import pylint.lint

from pvapy.hpc.dataConsumer import DataConsumer

def testLint(monkeypatch):
    ''' Test for linting errors '''
    monkeypatch.setattr(sys, 'exit', Mock())
    pylint_opts = ['pvapy.hpc.dataConsumer', '--disable=all', '--enable=E,F', '--generated-members="pva.*"']
    pylint.lint.Run(pylint_opts)
    sys.exit.assert_called_once_with(0)
