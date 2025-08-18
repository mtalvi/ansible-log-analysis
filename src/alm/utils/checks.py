import re


def check_if_ansible_log_should_be_ignored(log: str) -> bool:
    """Check if the log should be ignored."""

    if _is_include_fatal_error(log):
        return False

    return True


def _is_include_fatal_error(log: str) -> bool:
    """Check if the log include a fatal error using regex."""

    fatal_error_regex = r"fatal: \[.*?\]"
    return re.search(fatal_error_regex, log) is not None
