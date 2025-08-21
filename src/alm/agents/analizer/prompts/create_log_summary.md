# Ansible Error Log Summarization Prompt

You are an expert at analyzing Ansible error logs and providing concise, actionable summaries. Given an Ansible error log, extract the key information and provide a brief summary that identifies:

1. What failed (the component/resource)
2. The root cause of the failure
3. The context or operation being performed

Format your response as a single line summary that captures the essential problem.

## Examples:

Ansible Log Error:
```
failed: [bastion.ml2lq.internal] (item=certificate-ingress.yaml.j2) => {"ansible_loop_var": "item", "changed": false, "item": "certificate-ingress.yaml.j2", "msg": "Failed to create object: b'{\"kind\":\"Status\",\"apiVersion\":\"v1\",\"metadata\":{},\"status\":\"Failure\",\"message\":\"Internal error occurred: failed calling webhook \\\"webhook.cert-manager.io\\\": failed to call webhook: Post \\\"https://cert-manager-webhook.cert-manager.svc:443/validate?timeout=30s\\\": no endpoints available for service \\\"cert-manager-webhook\\\"\",\"reason\":\"InternalError\",\"details\":{\"causes\":[{\"message\":\"failed calling webhook \\\"webhook.cert-manager.io\\\": failed to call webhook: Post \\\"https://cert-manager-webhook.cert-manager.svc:443/validate?timeout=30s\\\": no endpoints available for service \\\"cert-manager-webhook\\\"\"}]},\"code\":500}\\n'", "reason": "Internal Server Error"}
```

summary of the log:

Ingress certificate creation failed - cert-manager webhook service endpoints unavailable when creating ingress certificate.

---

Ansible Log Error:
```
FAILED! => {"ansible_facts": {"pkg_mgr": "dnf"}, "changed": false, "failures": [], "msg": "Depsolve Error occurred: \\\\n Problem: conflicting requests\\\\n  - nothing provides system-release >= 9 needed by packages-microsoft-prod-1.1-2.noarch", "rc": 1, "results": []}
```

summary of the log:

Package installation failed - unable to install 'packages-microsoft-prod' due to missing dependency 'system-release >= 9' when trying to install packages using dnf.

---

Ansible Log Error:

```
FAILED! => {"msg": "The task includes an option with an undefined variable.. No first item, sequence was empty.\\\\n\\\\nThe error appears to be in \'/runner/project/ansible/roles-infra/infra-ec2-create-inventory/tasks/main.yml\': line 37, column 3, but may\\\\nbe elsewhere in the file depending on the exact syntax problem.\\\\n\\\\nThe offending line appears to be:\\\\n\\\\n\\\\n- name: Find the bastion in this batch of hosts\\\\n  ^ here\\\\n"}
```

summary of the log:

Undefined variable in sequence when trying to find the bastion host in an EC2 inventory creation task.


## Instructions:

Now analyze the following Ansible error log and provide a concise summary following the same format above:

Ansible Log Error:

```
{error_log}
```

summary of the log:

