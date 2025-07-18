import logging


class DataUserWorkflow(object):
    """
    """

    @staticmethod
    def globalinit(config):
        DataUserWorkflow.config = config
        DataUserWorkflow.workflowManager = config.workflowManager

    def __init__(self):
        self.logger = logging.getLogger("CRABLogger.DataUserWorkflow")
        mod = __import__('CRABInterface.%s' % self.workflowManager, fromlist=self.workflowManager)
        self.workflow = getattr(mod, self.workflowManager)(DataUserWorkflow.config)

    def getLatests(self, username, timestamp):
        """Retrives the latest workflows for the user

           :arg str user: a valid user hn login name
           :arg int limit: the maximum number of workflows to return
                          (this should probably have a default!)
           :arg int limit: limit on the workflow age
           :return: a list of workflows"""
        return self.workflow.getLatests(username, timestamp)

    def errors(self, workflow, shortformat):
        """Retrieves the sets of errors for a specific workflow

           :arg str workflow: a workflow name
           :arg int shortformat: a flag indicating if the user is asking for detailed
                                 information about sites and list of errors
           :return: a list of errors grouped by exit code, error reason, site"""
        raise NotImplementedError

    def report(self, workflow, userdn, usedbs):
        """Retrieves the quality of the workflow in term of what has been processed
           (eg: good lumis). This can call a different function depending on the jobtype.

           :arg str workflow: a workflow name
           :return: what?"""
        return self.workflow.report(workflow, userdn)

    def report2(self, workflow, userdn, usedbs):
        return self.workflow.report2(workflow, userdn)

    def logs(self, workflow, howmany, exitcode, jobids, userdn):
        """Returns the workflow logs PFN. It takes care of the LFN - PFN conversion too.

           :arg str workflow: a workflow name
           :arg int howmany: the limit on the number of PFN to return
           :arg int exitcode: the log has to be of a job ended with this exit_code
           :return: a generator of list of logs pfns"""
        return self.workflow.logs(workflow, howmany, exitcode, jobids, userdn)

    def logs2(self, workflow, howmany, jobids):
        """Returns information about the workflow log files.
           The client uses this information to get the pfn and initiate the download.

           :arg str workflow: a workflow name
           :arg int howmany: the limit on the number of PFN to return
           :arg int exitcode: the log has to be of a job ended with this exit_code
           :return: a generator of list of logs pfns"""
        return self.workflow.logs2(workflow, howmany, jobids)

    def output(self, workflow, howmany, jobids, userdn):
        """Returns the workflow output PFN. It takes care of the LFN - PFN conversion too.

           :arg str list workflow: a workflow name
           :arg int howmany: the limit on the number of PFN to return
           :return: a generator of list of output pfns"""
        return self.workflow.output(workflow, howmany, jobids, userdn)

    def output2(self, workflow, howmany, jobids):
        """Returns information about the workflow output files.
           The client uses this information to get the pfn and initiate the download.

           :arg str list workflow: a workflow name
           :arg int howmany: the limit on the number of PFN to return
           :return: a generator of output file info lists - site, lfn, ... for each file"""
        return self.workflow.output2(workflow, howmany, jobids)

    def taskads(self, workflow):
        """Calls the getRootTasks method to query condor and return a list of predefined attributes.

           :arg str workflow: a workflow name
           :return: a dict of attributes returned by the getRootTasks method
        """
        return self.workflow.taskads(workflow)

    def submit(self, *args, **kwargs):
        """Perform the workflow injection

           :arg str workflow: workflow name;
           :arg str activity: workflow activity type, usually analysis;
           :arg str jobtype: job type of the workflow, usually Analysis;
           :arg str jobsw: software requirement;
           :arg str jobarch: software architecture (=SCRAM_ARCH);
           :arg str jobminuarch: minimum required microarchitecture (=SCRAM_MIN_SUPPORTED_MICROARCH);
           :arg str inputdata: input dataset;
           :arg str primarydataset: primary dataset;
           :arg str nonvaliddata: allow invalid input dataset;
           :arg int use_parent: add the parent dataset as secondary input;
           :arg str secondarydata: secondary input dataset
           :arg str generator: event generator for MC production;
           :arg int events_per_lumi: events to generate per lumi;
           :arg str list siteblacklist: black list of sites, with CMS name;
           :arg str list sitewhitelist: white list of sites, with CMS name;
           :arg str splitalgo: algorithm to be used for the workflow splitting;
           :arg str algoargs: argument to be used by the splitting algorithm;
           :arg str cachefilename: name of the file inside the cache
           :arg str cacheurl: URL of the cache
           :arg str list addoutputfiles: list of additional output files;
           :arg str userdn: DN of user doing the request;
           :arg str username: username of the user doing the request;
           :arg int savelogsflag: archive the log files? 0 no, everything else yes;
           :arg int publication: flag enabling or disabling data publication;
           :arg str publishname: name to use for data publication;
           :arg str asyncdest: CMS site name for storage destination of the output files;
           :arg str dbsurl: dbs url where the input dataset is published;
           :arg str publishdbsurl: dbs url where the output data has to be published;
           :arg str vorole: user vo role
           :arg str vogroup: user vo group
           :arg str tfileoutfiles: list of t-output files
           :arg str edmoutfiles: list of edm output files
           :arg str list runs: list of run numbers
           :arg str list lumis: list of lumi section numbers
           :arg int totalunits: number of MC event to be generated
           :arg str list adduserfiles: list of additional user input files
           :arg int oneEventMode: enables oneEventMode
           :arg int maxjobruntime: max job runtime, in minutes
           :arg int numcores: number of CPU cores required by job
           :arg int maxmemory: maximum amount of RAM required, in MB
           :arg int priority: priority of this task
           :arg str lfn: lfn used to store output files.
           :arg int saveoutput: whether to perform ASO on job output.
           :arg int faillimit: the maximum number of failed jobs allowed before workflow is aborted
           :arg int ignorelocality: ignore data locality.
           :arg str list userfiles: The files to process instead of a DBS-based dataset.
           :arg str scheddname: Schedd name used for debugging.
           :arg str collector: Collector name used for debugging.
           :arg int dryrun: enable dry run mode (initialize but do not submit request).
           :arg str ignoreglobalblacklist: flag to ignore site blacklist from SiteSupport
           :arg dict userconfig: a dictionary of config.params which do not have a separate DB column
           :returns: a dict which contaians details of the request"""

        return self.workflow.submit(*args, **kwargs)

    def resubmit(self, workflow, publication, jobids, force, siteblacklist, sitewhitelist, maxjobruntime, maxmemory, priority, userdn):
        """Request to Resubmit a workflow.

           :arg str workflow: a workflow name"""
        return self.workflow.resubmit(workflow, publication, jobids, force, siteblacklist, sitewhitelist, maxjobruntime, maxmemory, priority, userdn)

    def resubmit2(self, workflow, publication, jobids, siteblacklist, sitewhitelist, maxjobruntime, maxmemory, priority):
        """Request to Resubmit a workflow.

           :arg str workflow: a workflow name"""
        return self.workflow.resubmit2(workflow, publication, jobids, siteblacklist, sitewhitelist, maxjobruntime, maxmemory, priority)

    def status(self, workflow, userdn, verbose=False):
        """Retrieve the status of the workflow

           :arg str workflow: a valid workflow name
           :arg str userdn: the user dn makind the request
           :return: a generator of workflow states
        """
        return self.workflow.status(workflow, userdn)

    def kill(self, workflow, killwarning=''):
        """Request to Abort a workflow.

           :arg str workflow: a workflow name
           :arg str force: a flag to know if kill should be brutal
           :arg int force: force to delete the workflows in any case; 0 no, everything else yes"""
        return self.workflow.kill(workflow, killwarning)

    def proceed(self, workflow):
        """Continue a task initialized with 'crab submit --dryrun'.

           :arg str workflow: a workflow name
        """
        return self.workflow.proceed(workflow)

    def publicationStatus(self, workflow, username):
        """Retrieve the status of the publication, used by status2 when displaying publication information

           :arg str workflow: a workflow name
           :yield:  dictionary with the number of jobs in certain publication state and failure reasons
        """
        yield self.workflow.publicationStatus(workflow, username)
