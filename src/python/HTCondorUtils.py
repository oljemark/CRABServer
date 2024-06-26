""" this file can entirely go away once we cleanup and use modern classad bindings """

import os

import classad
import htcondor

# This is part of the classad module as of HTCondor 8.1.2
def quote(value):
    ad = classad.ClassAd()
    ad["foo"] = str(value)
    return ad.lookup("foo").__str__()
try:
    quote = classad.quote
except Exception:  # pylint: disable=broad-except
    pass
def unquote(value):
    return classad.ExprTree(value).eval()
try:
    unquote = classad.unquote
except Exception:  # pylint: disable=broad-except
    pass

readEvents = getattr(htcondor, 'readEvents', htcondor.read_events)

class OutputObj:
    """ Class used when AuthenticatedSubprocess is created with pickleOut
        Contains additional information to be used for debug purposes, like environment
    """
    def __init__(self, outputMessage, outputObj):
        self.outputMessage = outputMessage
        self.outputObj = outputObj
        self.environmentStr = ""
        for key, val in os.environ.items():
            self.environmentStr += "%s=%s\n" % (key, val)


class AuthenticatedSubprocess(object):
    """
    We do not use this anymore since of April 2024 since we moved to using
    a single token for all interactions with HTCondor.
    Moreaover, htcondor.SecmMan is being removed from HTC bindings
    Keep the code here for a while in case we overlooked some important
    functionality and want to revive with some different implementation

    import time
    import pickle
    import signal
    import logging
    import traceback
    def __init__(self, proxy, tokenDir=None, pickleOut=False, outputObj=None, logger=logging):
        self.proxy = proxy
        self.pickleOut = pickleOut
        self.outputObj = outputObj
        self.timedout = False
        self.logger = logger
        self.tokenDir = tokenDir

    def __enter__(self):
        self.r, self.w = os.pipe()
        if self.pickleOut:
            self.rpipe = os.fdopen(self.r, 'rb')
            self.wpipe = os.fdopen(self.w, 'wb')
        else:
            self.rpipe = os.fdopen(self.r, 'r')
            self.wpipe = os.fdopen(self.w, 'w')
        self.pid = os.fork()
        if self.pid == 0:
            htcondor.SecMan().invalidateAllSessions()
            if self.tokenDir:
                htcondor.param['SEC_TOKEN_DIRECTORY'] = self.tokenDir
                htcondor.param['SEC_CLIENT_AUTHENTICATION_METHODS'] = 'IDTOKENS,FS,GSI'
            else:
                htcondor.param['SEC_CLIENT_AUTHENTICATION_METHODS'] = 'FS,GSI'
            htcondor.param['DELEGATE_FULL_JOB_GSI_CREDENTIALS'] = 'true'
            htcondor.param['DELEGATE_JOB_GSI_CREDENTIALS_LIFETIME'] = '0'
            os.environ['X509_USER_PROXY'] = self.proxy
            self.rpipe.close()
        else:
            self.wpipe.close()
        return self.pid, self.rpipe

    def __exit__(self, a, b, c):
        if self.pid == 0:
            if (a == None and b == None and c == None):
                if self.pickleOut:
                    oo = OutputObj("OK", self.outputObj)
                    self.wpipe.write(pickle.dumps(oo))
                else:
                    self.wpipe.write("OK")
                self.wpipe.close()
                os._exit(0)
            else:
                tracebackString = str('\n'.join(traceback.format_tb(c)))
                msg = "Trapped exception in Dagman.Fork: %s %s %s \n%s" % \
                                (a, b, c, tracebackString)
                if self.pickleOut:
                    oo = OutputObj(msg, self.outputObj)
                    self.wpipe.write(pickle.dumps(oo))
                else:
                    self.wpipe.write(msg)
                self.wpipe.close()
                os._exit(1)
        else:
            timestart = time.time()
            self.timedout = True
            while (time.time() - timestart) < 60:
                res = os.waitpid(self.pid, os.WNOHANG)
                if res != (0,0):
                    self.timedout = False
                    break
                time.sleep(0.100)
            if self.timedout:
                self.logger.warning("Subprocess with PID %s (executed in AuthenticatedSubprocess) timed out. Killing it." % self.pid)
                os.kill(self.pid, signal.SIGTERM)
                #we should probably wait again and send SIGKILL is the kill does not work

    """
