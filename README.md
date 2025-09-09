# Ansible Log Analysis Architecture

Written by Itay Katav, note that everything isn't fully defined yet.   
I have a couple of assumptions that we need to clarify.

## Problem definition

Given a live stream of Ansible logs, our goal is to:

* Analyze the logs and detect errors.  
* Classify the error for the authenticated user.  
* Given the error log, suggest a step-by-step solution.

## How is this process done currently?

A human analyst is:

* Searching for error logs.  
* Talk with the person who is authorized with the credentials to solve the problem:  
  * Examples:   
    AWS provisioning failed requires talking with the AWS person who is authorized.  
    Bug in the playbook source code \- talk with the programmer.  
* The authenticated person needs to **understand how to solve the problem**.  
* Solve the problem.

## Our Solution Stack

* Loki \- as a log database.  
* Alloy/Promtail \- log ingestion and label definer.  
* OpenShiftAI \- model serving, data science pipeline, notebooks.  
* Backend:  
  * FASTAPI \- for api endpoints.  
  * Langchain.  
  * LangGraph \- for building the agentic workflow.  
  * PostgreSQL.  
  * Sentence Transformers \- generating embeddings.  
* UI:  
  * Gradio (for now)  
* Annotation interface: an interface that is used for evaluation and workflow improvement  
  * Gradio

## High-Level Solution

1. Data is being **ingested** from the Red Hat Ansible Automation Platform (AAP) clusters, using Alloy or Promtail, into Loki (a time series database designed for logs).  
2. An **error log is alerted** using a Grafana alert and sent into the agentic workflow.  
3. The **agentic workflow** processes the log and stores the processed data into a PostgreSQL database.  
4. The log analyst using the **UI** interacts with the logs and gets suggestions on how to solve the error, depending on their authorization. 

<img src="figures/high_level_architecture.png" alt="high_level_architecture" style="width:65%;">

### Ingestion \- using Alloy/Promtail

Using Loki/Promtail, we will process every Ansible log once with a predefined regex to generate labels using regex groups:

* Timestamp.  
* Log\_cluster\_source.  
* Log\_file\_source.  
* Log\_level.  
* Log\_message.

Labels will help us search for specific related logs at inference time or query by the labels.

## Agentic Workflow:

<img src="figures/workflow.png" alt="Workflow" style="width:65%;">

### Step 1: Embedding and Clustering

Many logs are generated from the same log template. To group them, we embed a subset of each log, then cluster all the embeddings into groups. Each group represents a log template. For example, let’s look at the following three logs:

```
1. error: user id 10 already exits.
2. error: user id 15 already exits.
3. error: password of user itayk is wrong.
```

As we can see here, logs 1 and 2 are from the same template, and we want to group them together.

Then the user will be able to filter by templates.

### Step 2: Summary and Expert Classification per Log Template

For each log template, create a summary of the log and classify it by authorization.  
For example, an analyst who has AWS authentication will filter by their authorization and will see only relevant error summaries in the UI.

### Step 3: Creating a step-by-step solution 

We will have a router that will determine if we need more context to solve the problem or if the log error alone is sufficient to generate the step-by-step solution.  
If we need more context, we will spin up an agent that will accumulate context as needed by using the following:

* **Loki MCP**, which is able to query the log database for additional log context.  
* **RAG** for retrieving an error cheat sheet of already solved questions.  
* **Ansible MCP** for obtaining code source data to suggest a better solution.

### Step 4: Store the data

* Store a payload of the generated values for each log in a PostgreSQL database.

### Training and Inference stages

Currently, the **only difference** between the training and inference stages is the clustering algorithm.

#### Training

Train the clustering algorithm to cluster the logs by log-template.

#### Inference 

Load the trained clustering model.

## UI

* Each expert selects their rule, dependent on their authorization. Current rules are:  
  * Kubernetes / OpenShift Cluster Admins  
  * DevOps / CI/CD Engineers (Ansible \+ Automation Platform)  
  * Networking / Security Engineers  
  * System Administrators / OS Engineers  
  * Application Developers / GitOps / Platform Engineers  
  * Identity & Access Management (IAM) Engineers  
  * Other / Miscellaneous  
* Each expert can filter by labels (cluster\_name, log\_file\_name, …)  
* A summary of each log is listed to the expert, the expert can click on the log summary and view the whole log, and a step-by-step solution, timestamp, and labels

<img src="figures/experts_option.png" alt="Experts Option" style="width:40%;">

After selecting the authorization class "expert":

<img src="figures/ui_view.png" alt="UI View" style="width:65%;">

<img src="figures/step-by-step.png" alt="Step-by-step Solution" style="width:65%;">

## Annotation interface

For improving our agentic workflow, context PDFs, and other context we need to understand the errors. To do so, we have a data annotation interface for annotating Ansible error log pipeline outputs,  
Where we see the agentic workflow:

* **Input** of the left (error log)  
* **Outputs** in the center (summary, and step-by-step solution)  
* **Annotation window** on the right.

See the interface below:

<img src="figures/anotation_interface.png" alt="Annotation Interface" style="width:65%;">


## Deploy

The Ansible Log Monitor can be deployed in multiple environments depending on your needs. Choose the deployment method that best fits your requirements:

### Quick Start - Local Development

For development and testing, you can run all services locally using the provided Makefile:

#### Prerequisites
- Docker and Docker Compose
- Python 3.8+ with `uv` package manager
- Make

#### Deploy Locally
```bash
# Clone the repository
git clone <repository-url>
cd ansible-logs
uv sync

# Start all services (PostgreSQL, Backend API, UI, Annotation Interface)
make local/start

# Check service status
make local/status

# Stop all services
make local/stop
```

### Deploy on the Cluster

For production environments, deploy using Helm charts to OpenShift:

#### Prerequisites
- OpenShift cluster
- Helm 3.x
- oc configured for your cluster

#### Quick Deploy to OpenShift
```bash
# Deploy to specific namespace
make helm/deploy NAMESPACE=alm-prod

```

#### Production Configuration
```bash
# Deploy with production settings
helm upgrade --install alm ./deploy/helm/ansible-log-monitor \
  --set backend.replicas=3 \
  --set backend.ingress.enabled=true \
  --set backend.ingress.hosts[0].host=alm.yourdomain.com \
  --set postgres.persistence.size=50Gi
```

#### OpenShift Management Commands
```bash
make helm/help                    # Show all helm commands
make helm/status                  # Check deployment status
make helm/logs-backend           # View backend application logs
make helm/port-forward-backend   # Port forward to access backend locally
make helm/uninstall             # Remove the deployment
```
