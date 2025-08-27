"""Regex patterns for AAP datasource."""

AAP_LOG_PATTERN = r"^(?P<log_type>[A-Z ]+)(?: \[(?P<task_name>[^\]]+)\] ?\**$)(?:\n^(?P<timestamp>\w+ \d{2} \w+ \d{4}  \d{2}:\d{2}:\d{2} \+\d{4}).*)?(?:\n^(?P<status>\w+): \[(?P<host>[^\]]+)\])?(?:[\w\W]*?\n\n)"

AAP_LOG_FATAL = r"^(?P<log_type>[A-Z ]+)(?: \[(?P<task_name>[^\]]+)\] ?\**$)(?:\n^(?P<timestamp>\w+ \d{2} \w+ \d{4}  \d{2}:\d{2}:\d{2} \+\d{4}).*)?(?:\n^(?P<status>fatal): \[(?P<host>[^\]]+)\]: )(?P<logmessage>[\w\W]*?)\n\n"

AAP_LOG_ERROR = r"^(?P<log_type>[A-Z ]+)(?: \[(?P<task_name>[^\]]+)\] ?\**$)(?:\n^(?P<timestamp>\w+ \d{2} \w+ \d{4}  \d{2}:\d{2}:\d{2} \+\d{4}).*)?(?:\n^(?P<status>error): \[(?P<host>[^\]]+)\]: )(?P<logmessage>[\w\W]*?)\n\n"

TESTING_LOG_FATAL = r"fatal: \[(?P<host>[^\]]+)\]: [^{]* (?P<logmessage>.*)"

TESTING_LOG_ERROR = r"error: \[(?P<host>[^\]]+)\]: [^{]* (?P<logmessage>.*)"

TESTING_LOG_FAILED = r"failed: \[(?P<host>[^\]]+)\]: [^{]* (?P<logmessage>.*)"
