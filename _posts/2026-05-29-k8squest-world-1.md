---
title: "K8squest - World 1 - Core K8s basic"
date: 2026-05-29
categories: [k8s]
---

# Level 1: `CrashLoopBackOff` Challenge

## What Happened:

The `Pod` was crashing because it tried to run a command called `nginxzz` - but that command doesn't exist in the nginx container image.

When you inspected the pod with:
```
kubectl describe pod nginx-broken -n k8squest
```

Error: failed to create `containerd` task: exec: `"nginxzz"`: executable file not found in `$PATH`;

This is `K8s` telling: 
```
"I found the image, pulled it, created a container... but the command you told me to run doesn't exist."
```

## How `K8s` Behaved:

1. Scheduler assigned the pod to a node;
2. `kubelet` pulled the nginx image;
3. `Container runtime` tried to start the container with command `["nginzz"]`;
4. Command failed instantly;
5. `kubelet` tried again (`CrashLoopBackoff`);
6. Exponential backoff kicked in = wait longer between retries;

This is `K8s` doing exactly what you told it to do. It's not smart enough to know `["nginzz"]` is a typo.

## Key Concepts:

1. Pods are ephemeral:
- You can't edit most fields of a running pod;
- When you need changes, delete and recreate;
- This is why `Deployments` exist (they manage this for you);

2. Container images define what can run
- The nginx image has: `nginx`, `bash`, `sh`, etc.;
- It doesn't have `nginzz`;
- The command field overrides the image's default command;

3. `CrashLoopBackOff` is feedback
- Not a scary error; it's information
- Tells you "I keep trying but this keeps failing"
- The Events in `kubectl` describe tell you WHY

## Must Remember:

- Always check `kubectl describe pod <name>` - Events tell the story
- `Pods` can't be edited after creation - delete and recreate
- `CrashLoopBackOff` = container keeps crashing - not a network/scheduling issue
- The command field is dangerous - only use it when you need to override the default

```
# See detailed events and state, show K8s details + events about the object.
kubectl describe pod <name> -n <namespace>
```

```
# See what the container/app printed.
kubectl logs <name> -n <namespace>
```

Takes a **snapshot** of the `Pod's` current configuration and saves it to `/tmp/fix.yaml`
```
kubectl get pod nginx-broken -n k8squest -o yaml > /tmp/fix.yaml
```

 `-f` means file. It tells `kubectl` to read the configuration from a file instead of typing it all out;
 Apply whatever is defined in this file to the cluster;
```
kubectl apply -f /tmp/fix.yaml
```
# Level 2: `Deployment` Zero Replicas

## What Happened:

The `Deployment` was configured with `replicas: 0`, which tells `K8s`: 
```
"I want ZERO instances of this application running."
```

This is technically valid configuration - just not useful for serving traffic.
## How `K8s` Behaved


1. `Deployment` controller read your spec: "replicas: 0";
2. `ReplicaSet` was created with desired count = 0;
3. No pods were created (working as designed!);
4. Deployment status showed: 0/0 ready (which is correct from `K8s` perspective);

`K8s` did exactly what asked - but you probably wanted at least 1 replica running.
## Key Concepts:

1. `Deployments` manage `ReplicaSets`:
- Deployment = desired state (how many pods, which image, etc.);
- `ReplicaSet` = ensures that many pods exist;
- `Pods` = actual running containers;

2. `Replicas` = High Availability:
- `replicas: 0` = nothing running (maintenance mode);
- `replicas: 1` = one pod (no redundancy);
- `replicas: 1` = one pod (no redundancy);

3. `Deployments` are mutable:
- Unlike `Pods`, you CAN edit `Deployments`;
- Changes trigger rolling updates;
- Old `ReplicaSet` scaled down, new one scaled up;

4. Multiple ways to scale

## Must Remember:

- `Deployments` > `Pods` for production workloads
- `replicas: 0` is valid but means "nothing running"

To see the `Deployment` configuration:
```
kubectl get deployment web -n k8squest -o yaml
```

We saw that `spec.replicas: 0`
```
...
    "spec": {
        "progressDeadlineSeconds": 600,
        "replicas": 0,
        "revisionHistoryLimit": 10,
        "selector": {
            "matchLabels": {
                "app": "web"
            }
        },
...
```

We would wanted to scale to `spec.replicas: 0`
```
kubectl scale deployment web -n k8squest --replicas=1
```

View `deployment` status:
```
kubectl describe deployment <name> -n <namespace> 
kubectl describe deployment <name> -n <namespace> -o wide
```

See detailed events:
```
kubectl describe deployment <name> -n <namespace>
```

Scale imperatively:
```
kubectl scale deployment <name> --replicas=N -n <namespace>
```

Edit declaratively:
```
kubectl edit deployment <name> -n <namespace>
```

Watch rollout status (-w flag):
```
kubectl rollout status deployment/<name> -n <namespace>
```

See the `ReplicaSets` created by `deployment`:
```
kubectl get rs -n <namespace>
kubectl get rs -n <namespace> -l app=<deployment-name>
```

See the `Pod` managed by the `deployment`:
```
kubectl get pods -l app=<label> -n <namespace>
```

## Q&A:

Q: "A `deployment` shows 0/3 ready. What could be wrong?"
A: Could be:
1. Image pull errors (wrong image name/tag)
2. `Pods` crashing (bad config, missing env vars)
3. Health checks failing (readiness probe issues)
4. Resource limits (not enough CPU/memory on cluster)

# Level 3: `ImagePullBackOff` Mystery

## What Happened:

The `pod` was stuck in `ImagePullBackOff` status because `K8s` couldn't pull the container image
`nginx:nonexistent-tag-yz-123` from `Docker Hub`. This tag doesn't exist, so the `kubelet` kept trying and backing off between attempts.
Result in a `STATUS` of `ImagePullBackOff`:

```
NAME      READY   STATUS             RESTARTS   AGE
web-app   0/1     ImagePullBackOff   0          5m41s
```
## How `K8s` Behaved

1. `Pending`: `Pod` accepted, waiting to be scheduled
2. `ContainerCreating`: Scheduled, pulling images
3. `Running`: All containers started successfully

The `Pod` got stuck at phase 2. The `kubelet` on the node tried to pull the image, failed, waited a bit (backoff), and tried again. Thus, creating the `ImagePullBackOff` status.
## Image pull process:

`kubectl` apply → `Scheduler` assigns node → `kubelet` pulls image → Creates container → `Pod` runs
                                       ^
			                        Stuck here!

Check the exact image being used:
```
kubectl get pod <name> -n <namespace> -o yaml | grep image:
```

## Prevention Strategies

1. Use specific tags, not latest in production
2. Implement image scanning in CI/CD to verify images exist
3. Set up alerts for `ImagePullBackOff` events
4. Use `admission controllers` to validate image references before deployment
5. Keep a local registry mirror for critical images

## `Pod` failure modes:

• `CrashLoopBackOff`: bad container command
• `ImagePullBackOff`: bad image reference
# Level 4: `Pending` Pod Problem
## What Happened:

The `Pod` was stuck in Pending status because it requested` 999 CPUs` and `999Gi` of memory, far more than any node in the cluster can provide. The `K8s` scheduler couldn't find a node with enough resources, so the pod never started.

```
NAME         READY   STATUS    RESTARTS   AGE
hungry-app   0/1     Pending   0          4m20s
```
## How `K8s` Behaved

1. `Pod` created: `API server` accepts the `pod` manifest  
2. `Scheduler` watches: Sees new unscheduled `pod`  
3. Filtering: Eliminates nodes that don't meet requirements (resources, taints, affinity)  
4. Scoring: Ranks remaining nodes by best fit  
5. Binding: Assigns `pod` to winning `node`

The `pod` failed at step 3; no `nodes` passed the filter because none had `999 CPUs` available.
## Resource Requests vs Limits:

- `Requests`: Guaranteed minimum resources (used for scheduling)
- `Limits`: Maximum resources allowed (enforced at runtime)

```
resources:
  requests:     # "I need at least this much"
    memory: "64Mi"
    cpu: "100m"
  limits:       # "Don't let me use more than this"
    memory: "128Mi"
    cpu: "200m"
```

**`CPU units:`**
- 1 = 1 full CPU core
- 100m = 0.1 CPU (100 `millicores`)
- 1000m = 1 CPU

**`Memory units:`**
- Mi = Mebibytes (1024²)
- Gi = Gibibytes (1024³)
- M = Megabytes (1000²)
- G = Gigabytes (1000³)
## What happens when a node is full:

- `Node` capacity: `4 CPUs`, `8Gi` memory
- Already allocated: `3 CPUs`, `6Gi` memory
- Available: 1 CPU, 2Gi memory

`Pod` requests `2 CPUs` = Can't schedule (insufficient `CPU`)
`Pod` requests `500m CPU`, `1Gi memory` = Can schedule

1. Use specific tags, not latest in production
2. Implement image scanning in CI/CD to verify images exist
3. Set up alerts for `ImagePullBackOff` events
4. Use `admission controllers` to validate image references before deployment
5. Keep a local registry mirror for critical images

## Two `pod` failure modes:

• `CrashLoopBackOff`: bad container command
• `ImagePullBackOff`: bad image reference

## Prevention Strategies:

1. Set reasonable defaults: Use `LimitRanges` to prevent unrealistic requests
2. Monitor utilization: Deploy `metrics-server` and track actual usage
3. Use `VPA` (`Vertical Pod Autoscaler`): Automatically adjust requests based on usage
4. `Cluster` autoscaling: Add `nodes` automatically when `pods` are pending
5. `Admission webhooks`: Validate resource requests before accepting `pods`
6. Resource quotas: Prevent one team from consuming entire `cluster`

| Reason                    | Event Message                                | Solution                                    |
| ------------------------- | -------------------------------------------- | ------------------------------------------- |
| Insufficient CPU          | `Insufficient cpu`                           | Reduce CPU requests or add nodes            |
| Insufficient Memory       | `Insufficient memory`                        | Reduce memory requests or add nodes         |
| No node match selector    | `node(s) didn't match node selector`         | Fix `nodeSelector` labels or add node label |
| Taints prevent scheduling | `node(s) had taint that pod didn't tolerate` | Add tolerations or remove taints            |
| Volume not available      | `persistentvolumeclaim not found`            | Create PVC first                            |

Shows `event messages` in chronological order by `lastTimestamp`:
```
kubectl get events --sort-by='.lastTimestamp'
```

See `node` capacity and allocatable resources:
```
kubectl describe nodes
```

Check actual resource usage (requires `metrics-server`):
```
kubectl top pod <name> -n <namespace>
kubectl top nodes
```

## `Pod` failure modes:

- `CrashLoopBackOff`: bad container command
- `ImagePullBackOff`: bad image reference
- `Pending` (resource constraints)
# Level 5: Lost Connection - `Labels & Selectors`

## What Happened:

The `Service` had a `selector` for `app: frontend`, but the `Pod` had the `label` `app: backend`. Since the `labels` didn't match, the `Service` couldn't find the `Pod` and had no endpoints. Without endpoints, traffic sent to the `Service` had nowhere to go.

```
NAME              ENDPOINTS   AGE
backend-service   <none>      11m
```
## How `K8s` Behaved

`Services` don't directly manage `Pods`. Instead, it uses `label selectors` to dynamically discover which `Pods` should receive traffic.

1. `Service` created with `selector: app: frontend`, `tier: api`  
2. `Service` controller watches all `Pods`  
3. Finds `Pods` matching ALL `selector labels`  
4. Creates `Endpoints` object with matching `Pod` IPs  
5. Routes traffic to those endpoints

The `Service` was looking for `app=frontend`, but the `Pod` was labeled `app=backend`, so step 3 failed; no matches found.
Labels are `key-value` pairs attached to `K8s` objects:
```
metadata:
  labels:
    app: backend
    tier: api
    evironment: prod
    version: v2
```

`Selectors` are queries that filter objects by labels:

```
selector:
  app: backend    # Matches pods with app=backend
  tier: api       # AND tier=api (both must match)
```

## How Services Use `Selectors`:

```
Service selector: {app: backend, tier: api}
                    ↓
Looks for pods with matching labels
                    ↓
Pod 1: {app: backend, tier: api};  Match!
Pod 2: {app: frontend, tier: api}; app doesn't match
Pod 3: {app: backend, tier: db};   tier doesn't match
Pod 4: {app: backend, tier: api, env: prod}; Match! Extra labels OK

This creates Endpoints with IPs of Pod 1 and Pod 4
```

`Important`: All `labels` in the selector must match, but `pods` can have extra `labels`.

## Lesson learned:

1. Never change `pod` labels without updating corresponding `services`
2. Monitor `endpoint` counts (alert if `endpoints = 0`)
3. Use Horizontal Pod Autoscaler (HPA) labels for consistency
4. Consider using consistent naming conventions

Check `service` and its `selector`
```
kubectl get service <name> -n <namespace>
kubectl describe service <name> -n <namespace>
kubectl get service <name> -n <namespace> -o yaml | grep - A
```

Check `endpoints` (The `IPs Service` routes to)
```
kubectl get endpoints <name> -n <namespace>
kubectl describe endpoints <name> -n <namespace>
```

View `Pod` labels:
```
kubectl get pods --show-labels -n <namespace>
kubectl get pod <name> -n <namespace> --show-labels
```

Find `pods` matching a `selector`:
```
kubectl get pods --selector=app=backend -n <namespace>
kubectl get pods -l app=backend,tier=api -n <namespace>
```

Add/modify `labels` on running `pods`:  
```
kubectl label pod <name> app=frontend -n <namespace>  
kubectl label pod <name> app=backend --overwrite -n <namespace>  
```  

Delete `resources`:
```
kubectl delete -f <file>.yaml
```

## Label Best Practices:

1. Use recommended labels (from `K8s` docs):
```
app.kubernetes.io/name: myapp
app.kubernetes.io/instance: myapp-prod
app.kubernetes.io/version: 1.2.3
app.kubernetes.io/component: backend
app.kubernetes.io/part-of: payment-system
```

2. Keep `selectors` simple: 1-3 `labels` max
3. Don't change labels on running `pods` if services depend on them
4. Use consistent values: backend not Backend or back-end
5. Document the `labels`: Maintain a `label` glossary of the cluster

## Understanding Endpoints:

`Endpoints` are the bridge between `Services` and `Pods`:
```
kubectl get endpoints <service-name>

NAME              ENDPOINTS
backend-service   10.244.0.5:5678,10.244.0.6:5678

                  ↑ These are Pod IPs matching the selector
```

If `ENDPOINTS` is empty, then `service` has no backends, which also meant traffic fails.

## Common reasons for empty endpoints:

- `Label` mismatch (what level 5 is about)
- No `pods` exist
- `Pods` exist but not Ready
- `Port` mismatch in `Service`
- `Pods` in different `namespace`

**Notes**: `Labels` are used everywhere in `K8s`:
- `Services` selecting `Pods`
- `Deployments` managing `ReplicaSets`
- `NetworkPolicies` filtering traffic
- `Node` selectors for scheduling
- `Volume` claims selecting storage

# Level 6: `Port` Mismatch Mayhem

## What Happened:

The `Service` was forwarding traffic to `port 8080` on the container, but the `NGINX` container actually listens on `port 80`. 
Result: Every request hit a closed port and failed with "connection refused."
## How `K8s` Behaved

When a request comes to a `Service`:
1. `Client` connects to Service `IP:port` (e.g., 10.96.0.1:80)
2. `Service` forwards to one of its endpoints
3. Traffic sent to `Pod` `IP:targetPort` (e.g., 10.244.0.5:8080)
4. `Container` must be listening on that port

The `service` forwarded to `port 8080`, but `NGINX` was listening on `port 80`. Step 4 failed, no process on `port 8080`.

Three `port` concepts:
```
apiVersion: v1
kind: Service
spec:
  ports:
  - port: 80          # Cluster Internal: other pods/services within the cluster                                             connect to this Service via port 80
    targetPort: 8080  # Internal: what port on the Pod
    nodePort: 30080   # Optional: Port on node for NodePort services
```
`Cluster Internal`: Client send a request to `port 80`, the `Service` forward to corresponding container port, in this case, `targetPort: 8080`;

`Internal`: The `Port` of the corresponding `container` that the `service` wired to;

`nodePort`: `Port` that exposed on the `Node`, request sent to the `Node` with the `port` of `nodePort` (in this case: 30080), would be forwarded to `targetPort: 8080`;

## Matching ports:
```
Container listens on port 8080
containerPort: 8080

Service must forward to the same port
targetPort: 8080
```
## Common patterns:

| Pattern      |         Container | Service Port | Service TargetPort |
| ------------ | ----------------: | -----------: | ------------------ |
| Simple match |                80 |           80 | 80                 |
| Port mapping |              8080 |           80 | 8080               |
| Named port   | 8080 named `http` |           80 | `http`             |
## Real-World Incident Example:

`Company`: `E-commerce` site during `Black Friday`
`Impact`: 30 minutes of checkout failures
`Cost`: $2.1M in lost sales

**What happened:**
A developer changed the application from `port 8080` to `9000` to avoid conflicts in their local environment. They updated the `Dockerfile` and `containerPort` but forgot to update the `Service's targetPort` .
During `deployment`, `pods` started fine. `Service` existed. `Endpoints` looked healthy. But every checkout request got "connection refused."

**Why it was hard to debug:**
- `Service` showed as `"healthy"` (it existed with `endpoints`)
- `Pods` showed as `"Ready"` (readiness probe was on a different `endpoint`)
- `Load balancer` health checks passed (they targeted a health `endpoint` on correct `port`)
- Only actual checkout traffic failed

## Discovery:

Tried to test directly:
```
kubectl port-forward pod/checkout-xz 8080:9000 -n production
```
Port forwarding `localhost:8080` to `pod:9000` directly, bypassing the `Service`. If this works, it mean the `pod` is listening on `9000`; the `Service's targetPort` was probably pointing to the wrong `port`.

```
kubectl describe service checkout -n production
```
`describe`: show details of a resource;
It dumps info like `targetPort`, `endpoints`, `selector`, which needed to identify the mismatch.

```
kubectl get pod checkout-xz -n production -o yaml | grep containerPort
```
`get pod checkout-xz`: fetch the pod spec;
`grep containerPort`  : filter only the `containerPort` line;
Result showed `9000`; confirmed pod listens on `9000`, but `Service` had `targetPort: 8080`, mismatch.

## Best practice:

When changing application `ports`, update EVERYWHERE:
- `Dockerfile`
- `containerPort` in `pod` spec
- `targetPort` in `service` spec
- Health check configurations
- Monitoring configurations

Check container `ports`:
```
kubectl get pod <name> -n <namespace> -o yaml | grep -A 2 ports:
kubectl describe pod <name> -n <namespace> | grep Port
```

Check `service ports`:
```
kubectl get service <name> -n <namespace>
kubectl describe service <name> -n <namespace>
kubectl get service <name> -n <namespace> -o yaml | grep -A 3 ports:
```

Test connectivity directly:
```
kubectl port-forward pod/<name> 8080:80 -n <namespace>
kubectl port-forward service/<name> 8080:80 -n <namespace>
```

Execute commands in `container` to test:
```
kubectl exec -it <pod-name> -n <namespace> -- curl localhost:80
kubectl exec -it <pod-name> -n <namespace> -- netstat -tlnp
```
`exec -it`: open interactive shell inside the `pod`;
`-- curl localhost:80`: run `curl` from inside the `container` to test if `port 80` responds;
`-- netstat -tlnp`: list all `ports` the `container` is actively listening on;

```
containerPort: Documentation only! Doesn't actually open the port.
# This just documents what port the container uses
ports:
- containerPort: 8080

Service port: What clients use to access the service
# Clients connect to service-ip:80
ports:
- port: 80

targetPort: Where service forwards traffic
# Service forwards to pod-ip:8080
ports:
- targetPort: 8080

Named ports (best practice):
# In Pod
ports:
- name: http
  containerPort: 8080
# In Service
ports:
- port: 80
  targetPort: http  # References the name, not number!

Benefits of best practice: Change the port number once (in pod), service automatically uses new value.
```

This level showed `single-container pod` basics. Next level introduces `multi-container` `pods` where a `sidecar container` crashes and affects the whole `pod`.

# Level 7: `Sidecar` Sabotage

## What Happened:

The `pod` had two `containers`: a `main app` and a `log-sidecar`. The `sidecar` tried to `tail -f` a file that didn't exist, causing it to crash immediately. In `K8s`, if any `container` in a `pod` crashes, the entire `pod` is considered unhealthy.
## How `K8s` Behaved

Multi-container `pods` run all containers simultaneously on the same `node` and share certain resources:
- Network: Same `IP address`, can communicate via `localhost`
- Volumes: Can share storage via `volumeMounts`
- Lifecycle: `Pod` is Ready only when ALL containers are `Ready`

## The `pod` lifecycle:

1. Both `containers` started
2. main-app: Started successfully
3. `log-sidecar`: Crashed (file not found)
4. `K8s` restarted `log-sidecar`
5. Crashed again, `CrashLoopBackOff`
6. `Pod` shows `1/2 ready` (one `container` working, one failing)

## Why multi-container `pods`?

Common patterns:

| Pattern    | Main Container | Sidecar Container | Use Case                        |
| ---------- | -------------- | ----------------- | ------------------------------- |
| Sidecar    | Web app        | Log forwarder     | Ship logs to Elasticsearch      |
| Ambassador | App            | Proxy             | Connect to external services    |
| Adapter    | Legacy app     | Format converter  | Convert logs to standard format |
`Pod` as atomic unit:
```
+-----------------------------------------------------------+
|                            Pod                            |
|                                                           |
|  +-----------+              +-----------+                 |
|  |           |   <======>   |           |                 |
|  |   main    |    share     |  sidecar  |                 |
|  |    app    |    volume    |  logging  |                 |
|  |           |              |           |                 |
|  +-----------+              +-----------+                 |
|        |                          |                       |
|        v                          v                       |
|                                                           |
|          Same network namespace                           |
|          Same IP: 10.244.0.5                              |
+-----------------------------------------------------------+
```

## Container states in a `pod`:

- All must be Running:  `Pod` is Running
- Any crashes: `Pod` shows reduced ready count (e.g., 1/2)
- All crash: `Pod` enters `CrashLoopBackOff`

## How to prevent:

1. Monitor `container` readiness, not just pod existence
2. Test sidecar `containers` independently
3. Set `deployment` timeout to fail fast
4. Alert on `pods` with partial ready states

View all containers in a `pod`:
```
kubectl get pod <name> -n <namespace> -o jsonpath='{.spec.containers[*].name}'
```

View `logs` from specific `container`:
```
kubectl logs <pod-name> -c <container-name> -n <namespace>
```

View `logs` with previous `container` instance (if crashed):
```
kubectl logs <pod-name> -c <container-name> --previous -n <namespace>
```

Follow `logs` in real-time:
```
kubectl logs <pod-name> -c <container-name> -f -n <namespace>
```

Execute `command` in specific `container`:
`-i = interactive`
`-t = allocate a terminal / TTY`
`-it = open an interactive shell inside the container`
```
kubectl exec <pod-name> -c <container-name> -it -n <namespace> -- sh
```

Stream `logs` from all `containers`:
`--all-containers=true means get logs from every container in the pod, not just one`
```
kubectl logs <pod-name> --all-containers=true -f -n <namespace>
```

## `Multi-Container` Best Practices:

1. Keep `sidecars` simple: They should be lightweight and focused
2. Handle missing files: Use scripts that create files if they don't exist
3. Set proper restart policies: `RestartPolicy: Always` (default) keeps retrying
4. Resource limits: `Sidecars` need resources too! Don't starve main container
5. Health checks: Implement readiness probes for both `containers`
6. Logging: Ensure both `containers` log to `stdout/stderr` for easy debugging

## Debugging Multi-Container `Pods`:

```
# 1. Check overall pod status
kubectl get pod <name> -n <namespace>
# Look for X/Y in READY column (e.g., 1/2 means one container failed)

# 2. Identify which container is failing
kubectl describe pod <name> -n <namespace>
# Look at "Container Statuses" section

# 3. Check logs of failing container
kubectl logs <pod> -c <failing-container> -n <namespace>

# 4. Check previous logs if container is crash looping
kubectl logs <pod> -c <failing-container> --previous -n <namespace>

# 5. Test interactively if possible
kubectl exec <pod> -c <container> -it -n <namespace> -- sh
# Then manually run the command to see what fails
```

| Issue               | Symptom                   | Solution                              |
| ------------------- | ------------------------- | ------------------------------------- |
| Sidecar crashes     | `1/2` ready               | Check sidecar logs, fix command       |
| Port conflict       | `CrashLoopBackOff`        | Ensure containers use different ports |
| Resource starvation | One container `OOMKilled` | Set proper resource requests/limits   |
| Volume permissions  | `Permission denied`       | Fix volume mount permissions          |
| Startup race        | Init failed               | Use init containers for dependencies  |
# Level 8: `Pod Logs` Mystery:

## What Happened:

The `PostgreSQL container` needed the `POSTGRES_PASSWORD` environment variable to initialize, but it wasn't provided. The `container` started, failed immediately, restarted, and repeated entering `CrashLoopBackOff`. The only way to discover this was by checking the `logs`.

## How `K8s` behaved:

`Logs` are your debugging superpower. Not all failures are visible in `kubectl describe`. Some applications:

- Start successfully, so the `pod` shows `"Running"`
- Fail due to configuration errors
- Exit immediately
- Restart and repeat

`Log` locations in `K8s`:

- Container logs: Captured from `stdout/stderr`
- Access via: `kubectl logs`
- Stored temporarily on `node`
- Rotated when they get too large

View current `logs`:
```
kubectl logs <pod> -n <namespace>
```

View previous `container logs` (after crash):
```
kubectl logs <pod> --previous -n <namespace>
```

Follow `logs` in real-time:
```
kubectl logs <pod> -f -n <namespace>
```

Specific container in `multi-container` `pod`:
```
kubectl logs <pod> -c <container> -n <namespace>
```

Last N lines:
```
kubectl logs <pod> --tail=50 -n <namespace>
```

`Logs` since timestamp:
```
kubectl logs <pod> --since=1h -n <namespace>
```

# Level 9: Init `Container` Gridlock:

## What Happened

The `initContainer` was waiting for a `service` that doesn't exist. `Init containers` must complete before main containers start, so the `pod` was stuck in `Init:0/1` status forever.

## How K8s Behaved

`Init containers` run before app containers and must complete successfully:

1. `Init containers` run sequentially (one after another)
2. Each must exit with status 0 (success)
3. Only after ALL `init containers` complete do app containers start
4. If `init container` fails, pod restarts (subject to `restartPolicy`)

## Lifecycle:

```
+-------------------+      +-------------------+      +------------------------+
|  Init Container 1 | ---> |  Init Container 2 | ---> |  Main Container 1 & 2  |
|   (sequential)    |      |   (sequential)    |      |       (parallel)       |
+-------------------+      +-------------------+      +------------------------+
```
## Common use cases:

- Wait for dependencies (databases, services)
- Clone git repositories
- Generate configuration files
- Set up permissions
- Database schema migrations

```
make service YAML locally
print it as yaml
save it into backend-service.yaml
do not actually create yet

kubectl create service clusterip backend-service \
  --tcp=80:80 \
  -n k8squest \
  --dry-run=client -o yaml > backend-service.yaml
```

| Values         | Meaning                                                 |
| -------------- | ------------------------------------------------------- |
| `nodeport`     | Create a Service exposed on each node IP + NodePort     |
| `loadbalancer` | Create a Service exposed through external load balancer |
| `externalname` | Create a Service that maps to an external DNS name      |
| `clusterip`    | Internal-only Service inside cluster                    |

| Value              | Meaning                                                   |
| ------------------ | --------------------------------------------------------- |
| `--dry-run=none`   | Actually create the resource                              |
| `--dry-run=client` | Generate/check locally, do not send to API server         |
| `--dry-run=server` | Send to API server for validation, but do not save/create |

| Command part                                       | Meaning                                              |
| -------------------------------------------------- | ---------------------------------------------------- |
| `kubectl create service clusterip backend-service` | Generate a ClusterIP Service named `backend-service` |
| `--tcp=80:80`                                      | Service port `80` maps to target port `80`           |
| `-n k8squest`                                      | Put it in namespace `k8squest`                       |
| `--dry-run=client`                                 | Do not create yet                                    |
| `-o yaml`                                          | Output as YAML                                       |
| `> /tmp/fix.yaml`                                  | Save YAML into file                                  |
# Level 10: `Namespace` Confusion
## What happened

The resources were deployed to the `"default" namespace` instead of `"k8squest"`. `Namespaces` provide isolation, resources in different namespaces can't easily find each other.
## How `K8s` Behaved

`Namespaces` are virtual clusters within a physical cluster:

- Provide scope for names (can have "web" pod in multiple namespaces)
- Enable resource quotas and limits per namespace
- Provide access control boundaries (`RBAC` per `namespace`)
- Services can communicate within `namespace` easily
- `Cross-namespace` communication requires fully qualified `DNS`

## `Namespace` isolation:

```
Cluster
├── default namespace
│   ├── pod: app-1
│   └── service: api
├── k8squest namespace
│   ├── pod: client-app
│   └── service: backend-service
└── production namespace
    ├── pod: payment-processor
    └── service: payment-api
```

## `DNS` resolution:

- Same `namespace: service-name`
- `Cross-namespace`: `service-name.namespace-name.svc.cluster.local`

List all `namespaces`:
```
kubectl get namespaces
```

View resources in specific `namespace`:
```
kubectl get all -n <namespace>
```

View `resources` in all `namespaces`:
```
kubectl get pods --all-namespaces
kubectl get pods -A
```

Create `namespace`:
```
kubectl create namespace <name>
```

Set default `namespace` for context:
```
kubectl config set-context --current --namespace=<namespace>
```

Delete `namespace` (careful):
```
kubectl delete namespace <namespace>
```