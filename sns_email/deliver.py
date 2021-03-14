#!/usr/bin/env python
import subprocess

import prometheus_client

from sns_email import logger

_logger = logger.getChild('deliver')

_counter_received = prometheus_client.Counter('sns_email_received_total', 'Received total')


class sendmail_deliver:
    def __init__(self, source, recipients, sendmail_path="/usr/bin/sendmail"):
        self.p = subprocess.Popen([sendmail_path, "-r", source, "-i"] + recipients,
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.recipients = recipients

    def __enter__(self):
        return self.p.stdin

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_value:
            _logger.info("exception during delivery, aborting process.")
            try:
                self.p.kill()
            except:
                _logger.warning("failed aborting delivery process.", exc_info=True)
            return
        try:
            outs, errs = self.p.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            self.p.kill()
            outs, errs = self.p.communicate()
        except:
            self.p.kill()
            raise
        if self.p.returncode != 0:
            raise Exception(
                "failed delivery. returncode={}, stdout={}, stderr={}".format(self.p.returncode, outs, errs))
        else:
            _counter_received.inc()
