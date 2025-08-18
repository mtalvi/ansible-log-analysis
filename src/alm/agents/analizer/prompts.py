from rich.markdown import Markdown

SYSTEM_PROMPT = Markdown(
    """
You are Ansible expert. You are given a log of an Ansible playbook execution and you need to decide if the error can be solved by modifying the Ansible playbook or can be ignored.
"""
)

USER_PROMPT = Markdown(
    """
Analyze the following Ansible log and decide if the error can be solved by modifying the Ansible playbook or can be ignored.

Anisble log: 
{log}
"""
)
