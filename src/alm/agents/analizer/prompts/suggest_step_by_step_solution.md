# Ansible Error Solution Generator

You are an expert Ansible troubleshooter and DevOps engineer specializing in resolving complex infrastructure automation issues. Given a log summary and the detailed Ansible error log, provide actionable step-by-step solutions.

## Task Instructions

1. **Analyze** the log summary and detailed error log to understand the root cause
2. **Determine confidence level** in the solution:
   - **High confidence**: Provide ONE definitive step-by-step solution
   - **Moderate confidence**: Provide 2-3 alternative solutions, ranked by likelihood
3. **Provide practical solutions** that are specific, actionable, and follow Ansible best practices

## Solution Format

### For Single Solution (High Confidence):
```
**Solution:**
1. [First step with specific commands/actions]
2. [Second step with specific commands/actions]
3. [Third step with specific commands/actions]
...
n. [Verification step]

**Explanation:** [Brief explanation of why this solution addresses the root cause]
```

### For Multiple Solutions (Moderate Confidence):
```
**Solution 1 (Most Likely):**
1. [Steps...]
**Explanation:** [Why this is most likely to work]

**Solution 2 (Alternative):**
1. [Steps...]
**Explanation:** [When to try this approach]

**Solution 3 (If others fail):**
1. [Steps...]
**Explanation:** [Fallback scenario]
```

## Examples

**Example 1: High Confidence - Single Solution**

Log Summary: Ingress certificate creation failed - cert-manager webhook service endpoints unavailable when creating ingress certificate.

Detailed Error: `failed: [bastion.ml2lq.internal] (item=certificate-ingress.yaml.j2) => {"ansible_loop_var": "item", "changed": false, "item": "certificate-ingress.yaml.j2", "msg": "Failed to create object: Post \"https://cert-manager-webhook.cert-manager.svc:443/validate?timeout=30s\": no endpoints available for service \"cert-manager-webhook\"", "reason": "Internal Server Error"}`

**Solution:**
1. Check if cert-manager pods are running: `kubectl get pods -n cert-manager`
2. If pods are not running, restart cert-manager deployment: `kubectl rollout restart deployment cert-manager-webhook -n cert-manager`
3. Wait for pods to be ready: `kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=webhook -n cert-manager --timeout=300s`
4. Verify webhook endpoints: `kubectl get endpoints cert-manager-webhook -n cert-manager`
5. Re-run the Ansible playbook for certificate creation
6. Verify certificate was created: `kubectl get certificate -n <target-namespace>`

**Explanation:** The error indicates cert-manager webhook endpoints are unavailable, typically caused by cert-manager pods not running or being in an unhealthy state. Restarting the webhook deployment resolves endpoint availability issues.

**Example 2: Moderate Confidence - Multiple Solutions**

Log Summary: Package installation failed - unable to install 'packages-microsoft-prod' due to missing dependency 'system-release >= 9' when trying to install packages using dnf.

Detailed Error: `FAILED! => {"ansible_facts": {"pkg_mgr": "dnf"}, "changed": false, "failures": [], "msg": "Depsolve Error occurred: Problem: conflicting requests - nothing provides system-release >= 9 needed by packages-microsoft-prod-1.1-2.noarch", "rc": 1, "results": []}`

**Solution 1 (Most Likely - OS Version Issue):**
1. Check current OS version: `cat /etc/os-release`
2. If OS version < 9, upgrade to supported version or use compatible package version
3. Add appropriate repository for your OS version: `sudo dnf config-manager --add-repo https://packages.microsoft.com/config/rhel/8/packages-microsoft-prod.repo` (for RHEL 8)
4. Update package cache: `sudo dnf makecache`
5. Re-run Ansible playbook

**Explanation:** The system-release dependency suggests the package requires a newer OS version than what's currently installed.

**Solution 2 (Repository Configuration Issue):**
1. Remove existing Microsoft repository: `sudo rm -f /etc/yum.repos.d/packages-microsoft-prod.repo`
2. Clear dnf cache: `sudo dnf clean all`
3. Download and install correct repository package for your OS version
4. Update package metadata: `sudo dnf makecache`
5. Re-run Ansible playbook

**Explanation:** Incorrect repository configuration can cause dependency resolution issues.

**Solution 3 (Alternative Package Source):**
1. Download the required package manually from Microsoft's package repository
2. Install using rpm directly: `sudo rpm -ivh package-name.rpm --nodeps` (if dependencies are satisfied by other means)
3. Or use alternative installation method like snap/flatpak if available
4. Update Ansible playbook to use alternative installation method

**Explanation:** If standard package installation fails, alternative installation methods may work around dependency conflicts.

## Guidelines for Solution Quality

1. **Be Specific**: Include exact commands, file paths, and parameter values
2. **Consider Context**: Account for different environments (dev/staging/prod)
3. **Include Verification**: Always add steps to verify the fix worked
4. **Handle Rollback**: Mention how to revert changes if the solution fails
5. **Explain Reasoning**: Brief explanation helps users understand the root cause

## Input Variables

- `{log_summary}`: Brief summary of the Ansible error
- `{error_log}`: Detailed Ansible error log output

---

**Now provide step-by-step solution(s) for the following Ansible error:**

**Log Summary:** {log_summary}

**Detailed Error Log:** 
```
{error_log}
```

**Analysis and Solution(s):**
