import unittest

from streamsx.topology.topology import *
from streamsx.topology.tester import Tester
import streamsx.spl.op as op
import streamsx.spl.toolkit as tk
import os
import streamsx.rest as sr
from streamsx.topology import context

class TestCloud(unittest.TestCase):
    """ Test invocations of composite operators in Streaming Analytics Service """

    @classmethod
    def setUpClass(self):
        self.service_name = os.environ.get('STREAMING_ANALYTICS_SERVICE_NAME')
        # start streams service
        connection = sr.StreamingAnalyticsConnection()
        service = connection.get_streaming_analytics()
        result = service.start_instance()

    def setUp(self):
        Tester.setup_streaming_analytics(self, force_remote_build=False)

    def _add_toolkits(self, topo):
        tk.add_toolkit(topo, './test_monitoring')
        tk.add_toolkit(topo, '../../com.ibm.streamsx.monitoring')

    def _build_launch_validate(self, name, composite_name):
        topo = Topology(name)
        self._add_toolkits(topo)

        params = {}
	
        # Call the test composite
        test_op = op.Source(topo, composite_name, 'tuple<rstring result>', params=params)

        tester = Tester(topo)
        tester.tuple_count(test_op.stream, 1, exact=True)
        tester.contents(test_op.stream, [{'result':'TEST_RESULT_PASS'}] )

        tester.test(self.test_ctxtype, self.test_config)

    def _launch_sample_job(self):
        # this job is monitored by test.jobs::TestJobStatusSource application
        # PE crash is forced by this application in order to trigger a notification
        topo = Topology("SampleCrashApp")
        self._add_toolkits(topo)
        # Call the crash composite
        test_op = op.Source(topo, "test.jobs::SampleCrashSource", 'tuple<boolean dummy>')
        # prepare config and submit the job to Streaming Analytics service
        config={}
        sc = sr.StreamingAnalyticsConnection()
        config[context.ConfigParams.STREAMS_CONNECTION] = sc
        context.submit(context.ContextTypes.STREAMING_ANALYTICS_SERVICE, topo, config=config)


    def test_metrics_monitor(self):
        self._build_launch_validate("test_metrics_monitor", "test.metrics::TestMetricsSource")

    def test_logs_monitor(self):
        self._build_launch_validate("test_logs_monitor", "test.system::TestLogsSource")

    def test_jobs_status_monitor(self):
        self._launch_sample_job()
        self._build_launch_validate("test_jobs_status_monitor", "test.jobs::TestJobStatusSource")


