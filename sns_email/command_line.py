import contextlib
import logging
import re

import configargparse

from sns_email import logger
from sns_email.receive import MessageReceiver
from sns_email.sns import SnsServer
from sns_email.sqs import SqsPoller

argument_parser = configargparse.ArgParser(auto_env_var_prefix="SNS_EMAIL_",
                                           args_for_setting_config_path=["-c", "--config-file"],
                                           default_config_files=["/etc/sns-email.conf", "~/.config/sns-email.conf"])

argument_parser.add_argument('--address', dest="address", action="store", default="localhost",
                             help='the IP address for HTTP server')
argument_parser.add_argument('--port', dest="port", action="store", default=10000, type=int,
                             help='the port for HTTP server')

argument_parser.add_argument('--accept-destination', dest="rex", action="store", type=re.compile, default=".*",
                             help='Regex to match destination email addresses')

argument_parser.add_argument('--sqs-queue-url', dest="sqs_queue_url", action="store",
                             help='URL of the SQS Queue where mail notification are delivered')
argument_parser.add_argument('--sqs-region', dest="sqs_region", action="store",
                             help='Region of the SQS Queue where mail notification are delivered')

argument_parser.add_argument('--verbose', '-v',
                             action="count", default=0,
                             help='verbose logging',
                             dest="logging_level")


def main(args=None):
    _args = argument_parser.parse_args(args=args)

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s.%(msecs)03d %(levelname)s [%(name)s] %(message)s',
                        datefmt="%Y-%m-%dT%H:%M:%S")

    if _args.logging_level == 1:
        logging.getLogger(logger.name).setLevel(logging.DEBUG)
    if _args.logging_level >= 2:
        logging.root.setLevel(logging.DEBUG)

    receiver = MessageReceiver(rex=_args.rex)
    with contextlib.ExitStack() as ctx:
        if _args.sqs_queue_url:
            ctx.enter_context(
                SqsPoller(receiver=receiver, queue_url=_args.sqs_queue_url, region=_args.sqs_region))

        httpd = SnsServer(receiver=receiver, server_address=(_args.address, _args.port))
        ctx.enter_context(httpd)

        logger.info("listening on %s", httpd.server_address)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        logger.info("shutting down.")


if __name__ == '__main__':
    main()
