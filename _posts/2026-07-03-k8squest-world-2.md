---
title: "K8squest - World 2 - Deployments & Scaling"
date: 2026-07-03
categories: [k8s]
---

# Level 11: `Deployment` Update Stuck
## What Happened:

The `deployment` tried to `roll out` a new version with `image nginx:nonexistent-v2.0-xyz` that doesn't exist. The `deployment` got stuck with some `pods` on the old working version and some failing to start with the new broken version.
`K8s'` `RollingUpdate` strategy protected you from total downtime by keeping old `pods` running while new ones failed.

## How `K8s` Behaved:

`RollingUpdate` Strategy (default for `Deployments`):

1. Create new `ReplicaSet` with new `pod` template
2. Scale up new `ReplicaSet` (create new `pods`)
3. Wait for new `pods` to be `Ready`
4. Scale down old `ReplicaSet` (terminate old `pods`)
5. Repeat until all `replicas` updated

The `deployment` got stuck at step 3; new `pods` never became `Ready` because the image didn't exist. `K8s` kept retrying but also kept the old `pods` running, preventing total service outage.

## `Deployment` states:

- Progressing: Update is happening
- Complete: All `replicas` updated and healthy
- Failed: Update couldn't complete (stuck here!)
## How `Deployments` manage `ReplicaSets`:

```
Deployment: web-app
├── ReplicaSet-abc123 (old version, replicas: 3)
│   ├── Pod-1 (Running)
│   ├── Pod-2 (Running)
│   └── Pod-3 (Running)
└── ReplicaSet-xyz789 (new version, replicas: 0 → trying to become 3)
    ├── Pod-4 (ImagePullBackOff)
    ├── Pod-5 (ImagePullBackOff)
    └── Pod-6 (Not created yet)
```

`RollingUpdate` parameters:
```
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1        # Max extra pods during update (1 = 4 total pods max)
    maxUnavailable: 0  # Max unavailable pods (0 = always keep 3 running)
```

## `Rollback` mechanism:

- `K8s` keeps old `ReplicaSets` scaled to 0
- `kubectl rollout undo` just swaps which `ReplicaSet` is scaled up
- Near-instant recovery (`pods` already exist, just scaled)


## Real-World Incident Example

A developer tagged and pushed `image checkout-service:v2.3.1` to the CI/CD pipeline, which started deploying. But they forgot to push that tag to `Docker Hub`, only the commit was pushed, not the tag.

The deployment started `rolling out` during peak Black Friday traffic (4PM EST). Half the `pods` updated to the broken version and entered `ImagePullBackOff`. Half stayed on `v2.3.0` (working).

Users experienced:
- 50% of checkout requests failed (hit broken pods)
- Intermittent cart errors
- Payment processing timeouts

Why it took 2 hours to fix:
1. Team didn't know about `kubectl rollout undo` (new to K8s)
2. Tried to "fix forward" by building new image (30 min CI/CD time)
3. New build also failed (wrong tag again)
4. Tried manual pod deletion (didn't help, `deployment` kept creating broken ones)
5. Finally, senior engineer suggested checking `rollout history`
6. Ran `kubectl rollout undo deployment/checkout-service`
7. Instant recovery in 30 seconds

Check `deployment` status
```
kubectl get deployment <name> -n <namespace>
kubectl describe deployment <name> -n <namespace>
```

Check `rollout status` (shows if `stuck/progressing/complete`)
```
kubectl rollout status deployment/<name> -n <namespace>
```

View `rollout history`:
```
kubectl rollout history deployment/<name> -n <namespace>
```

View specific `revision` details:
```
kubectl rollout history deployment/<name> --revision=2 -n <namespace>
```

`Rollback` to previous version (MOST IMPORTANT!):
```
kubectl rollout undo deployment/<name> -n <namespace>
```

`Rollback` to specific revision:
```
kubectl rollout undo deployment/<name> --to-revision=3 -n <namespace>
```

Pause a `rollout` (stop updates `mid-rollout`):
```
kubectl rollout pause deployment/<name> -n <namespace>
```

Resume a paused `rollout`:
```
kubectl rollout resume deployment/<name> -n <namespace>
```

Restart `deployment` (rolling restart with same image):
```
kubectl rollout restart deployment/<name> -n <namespace>
```

See all `ReplicaSets` (old ones are kept for `rollback`!):
```
kubectl get replicasets -n <namespace>
```

## What's Next?

Next level: You'll learn about `ReplicaSets` and how Deployments use them under the hood!
Pro tip: In production, always keep `rollout history`. The default is 10 revisions. You can change with:
```
spec:
  revisionHistoryLimit: 10  # Keep last 10 ReplicaSets
```

# Level 12: The `Restart Loop`:

## What Happened:

The `pods` were stuck in a restart loop because the liveness probe was checking `endpoint /nonexistent-healthz` which returned `404 (Not Found)`. `K8s` interpreted this as "`pod` is unhealthy" and kept restarting it, which of course failed the health check again immediately. 

This is a classic configuration error that can cause cascading failures in production.

## How `K8s` Behaved:

1. `Pod` starts
2. Wait `initialDelaySeconds` (5 seconds)
3. Check liveness probe (`HTTP GET /nonexistent-healthz:8080`)
4. Get `404` response
5. Increment failure count (1/2)
6. Wait `periodSeconds` (5 seconds)
7. Check again: `404`
8. Increment `failure count` (2/2)
9. `failureThreshold` reached! Kill `pod`
10. Restart `pod`
11. Repeat from step 1, Infinite loop!

## Why `K8s` kept restarting:

- Liveness probes determine if a `container` is alive and healthy
- Failed liveness probe = "`Container` is dead or stuck, restart it"
- `K8s` tries to `"heal"` by restarting
- But if the probe config is wrong, restarts don't help!

| Probe Type | Purpose                         | Action on Failure   | Use Case                             |
| ---------- | ------------------------------- | ------------------- | ------------------------------------ |
| Liveness   | Is `container` alive?           | Restart `container` | Detect deadlocks, infinite loops     |
| Readiness  | Is container ready for traffic? | Remove from service | Slow startup, dependencies not ready |

```
# HTTP probe (most common)
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
    httpHeaders:
      - name: Custom-Header
        value: Awesome
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

# TCP probe (just checks if port is open)
livenessProbe:
  tcpSocket:
    port: 8080
  initialDelaySeconds: 15
  periodSeconds: 20

# Exec probe (run command inside container)
livenessProbe:
  exec:
    command:
      - cat
      - /tmp/healthy
  initialDelaySeconds: 5
  periodSeconds: 5
```

- `initialDelaySeconds`: Wait before first check (app startup time)
- `periodSeconds`: How often to check
- `timeoutSeconds`: How long to wait for response
- `failureThreshold`: How many `failures` before action (restart for `liveness`)
- `successThreshold`: How many `successes` needed to be considered healthy (usually 1)

## Real-World Incident Example:

Company: SaaS platform (500K daily users)
Impact: 45-minute complete outage, 100% of users affected
Cost: $750K in lost revenue + $1.2M in SLA refunds = $1.95M

A developer added a liveness probe to a critical authentication service:
```
livenessProbe:
  httpGet:
    path: /v2/health  # New endpoint in v2 branch
    port: 8080
  failureThreshold: 2
  periodSeconds: 5
```

`Problem`: The `PR` merged but the `/v2/health endpoint` wasn't in the deployed code yet, it was on a different branch! The health endpoint was actually `/health (v1)`.
The cascade:
```
14:00 - Deployment starts
14:01 - First pod starts, liveness probe fails (404)
14:01 - Pod restarted (failure threshold: 2, so 10 seconds to kill)
14:01 - Old pod terminated (RollingUpdate)
14:01 - New pod starts, fails again
14:02 - All 50 pods in restart loop
14:03 - Service has 0 healthy endpoints
14:03 - 100% of users see "Service Unavailable"
14:03 - On-call paged, team scrambles
14:20 - Team identifies liveness probe issue
14:25 - Quick fix: kubectl edit deployment, change /v2/health -> /health
14:30 - Pods stabilize
14:45 - Service fully recovered
```

Why it was catastrophic:
1. No gradual `rollout` - All `pods` updated at once
2. No pre-production testing - Liveness probe never tested in staging
3. Fast failure - `failureThreshold: 2` with `periodSeconds: 5 = 10 second` kill time
4. Authentication service - When it's down, entire platform is down

Fix:

Changed path from `/v2/health` to `/health`; `Pods` recovered immediately
```
kubectl edit deployment auth-service
```

1. Always test `health endpoints` before deploying
2. Use longer `initial delays` for slow-starting apps
3. Set higher failure thresholds (3-5) to tolerate transient issues
4. Use progressive `rollouts` (not all at once)
5. Monitor restart counts - alert if `pods` restart repeatedly

Describe `pod` to see liveness probe failures:
```
kubectl describe pod <name> -n <namespace>
```
`Events`: "Liveness probe failed"

Check `deployment` probe `configuration`:
```
kubectl get deployment <name> -n <namespace> -o yaml | grep -A 20 livenessProbe
```

Edit `deployment` (fix probe config):
```
kubectl edit deployment <name> -n <namespace>
```

Check `probe` results in real-time:
```
kubectl get events -n <namespace> --watch
```

## Best Practices for Liveness Probes

```
1. Use appropriate initialDelaySeconds:
initialDelaySeconds: 30  # Give app time to start

2. Set reasonable failure thresholds:
failureThreshold: 3  # Allow some transient failures

3. Keep health checks lightweight:
// Bad: Health check does database query
// Good: Health check just returns 200 OK

4. Use separate liveness and readiness probes:
livenessProbe:
  httpGet:
    path: /healthz   # Is process alive?
readinessProbe:
  httpGet:
    path: /ready     # Is service ready for traffic?

5 Test in staging first:
- Deploy to staging with new probe
- Verify pods stay healthy
- Then deploy to production
```

## Not-so-good Practices:
```
1. Don't use same probe for liveness and readiness:
- Liveness = "restart me if broken"
- Readiness = "don't send traffic yet"

2. Don't make health checks expensive:
# Bad: Checks database, does cleanup, runs migrations
# Good: Returns 200 if process is running

3. Don't use very short periods:
periodSeconds: 1   # Too aggressive! Creates load
periodSeconds: 10  # Better

4. Don't forget initialDelaySeconds:
# Bad: App needs 20s to start but initialDelay is 5s
# Result: Immediate restart loop!
```

## Debugging Restart Loops:

```
1. Check if pods are restarting
kubectl get pods -n <namespace>

2. If RESTARTS is increasing, describe the pod
kubectl describe pod <name> -n <namespace>

3. Look for:
- "Liveness probe failed" in Events
- "Back-off restarting failed container"

4. Check probe configuration
kubectl get deployment <name> -n <namespace> -o yaml | grep -A 20 livenessProbe

5. Test the health endpoint manually
kubectl port-forward pod/<name> 8080:8080 -n <namespace>
curl http://localhost:8080/healthz  # Should return 200

6. If endpoint is wrong, fix it
kubectl edit deployment <name> -n <namespace>
```

 Key takeaway: `Liveness probes` should be simple and reliable. When in doubt, use a TCP socket probe or a very basic HTTP endpoint that just returns 200.
# Level 13: Traffic to Unready `Pods`:

The `pods` were receiving traffic before they were ready to handle it, causing `502 Bad Gateway` errors for users. The root cause: no `readiness probe` configured.

Without a `readiness probe`, `K8s` assumes that as soon as a pod's status is "Running", it's ready to receive traffic. But `"Running"` just means the `container` process started, not the app inside the `container` is ready to use.

The app had a `20-second startup delay` (simulated with `sleep 20` in `postStart hook` - a command `K8s` run right after the `container` starts ). During those 20 seconds, pods were added to the `Service endpoints` and received real user traffic, but they couldn't handle it yet as the pod hasn't ready.

```
postStart hook = run something after container starts
readinessProbe = check whether app is ready for traffic
```

## How `k8S` Behaved:

Without `readiness probe`:
`Pod` lifecycle:
1. `Pod` created
2. `Container` starts, `Status: Running`
3. Immediately added to `Service endpoints` (bad!)
4. Receives traffic from `Service`
5. App still starting up (sleep 20 running)
6. Returns `502 Bad Gateway` to users
7. After 20s, app is actually `ready`

With `readiness probe`:
`Pod` lifecycle:
1. `Pod` created
2. `Container` starts, `Status: Running`
3. Not added to `Service` yet (`readiness probe` not passed)
4. Wait `initialDelaySeconds (22s)`
5. Check `readiness probe` HTTP GET /:8080
6. Get `200 OK` response
7. Mark `pod` as `Ready`
8. Added to Service endpoints after `rediness probe` passed
9. Receives traffic, app is ready

## Liveness vs Readiness:

| Aspect            | Liveness Probe                   | Readiness Probe                           |
| ----------------- | -------------------------------- | ----------------------------------------- |
| Question          | "Is the `container` alive?"      | "Is the `container` ready for traffic?"   |
| Action on failure | Restart the `container`          | Remove from `Service endpoints`           |
| Use case          | Detect deadlocks, infinite loops | Prevent traffic during `startup/overload` |
| Failure is        | Fatal (needs restart)            | Temporary (will recover)                  |
| Example           | Process crashed                  | Database connection not ready             |

## When to Use Each `Probe`:

Use `Liveness Probe` when:
- Detecting application deadlocks
- Process is stuck in an infinite loop
- Memory leak has frozen the app = the app consumed too much RAM and can no longer work properly
- Recovery method: `Restart`

Use `Readiness Probe` when:
- Application needs time to load data into cache
- Waiting for database connection
- Loading configuration files
- Temporary overload (too many requests)
- Recovery method: Wait, don't make it ready to receive traffic

## `Readiness Probe` Configuration:

```
readinessProbe:
  # HTTP probe (most common)
  httpGet:
    path: /ready            # Endpoint that checks if app is ready
    port: 8080
    httpHeaders:
      - name: X-Custom-Header
        value: health-check

  initialDelaySeconds: 10   # How long to wait before first check
  periodSeconds: 5          # How often to check
  timeoutSeconds: 3         # Max time to wait for response
  successThreshold: 1       # How many successes needed (usually 1)
  failureThreshold: 3       # How many failures before marking unready
```

## Alternative `probe` types:

```
# TCP socket probe (just check if port is listening)
readinessProbe:
  tcpSocket:
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10

# Exec probe (run a command)
readinessProbe:
  exec:
    command:
      - cat
      - /tmp/ready
  initialDelaySeconds: 5
  periodSeconds: 5
```


## Lessons:
- Always use `readiness probes` for apps with startup time
- Test under production-like load before an event
- Implement health endpoint that checks actual `readiness`, not just `"is process running"`
- Use progressive `rollouts` to catch issues early
- Monitor error rates during `deployments`

Check which `pods` are receiving traffic:
```
kubectl get endpoints <service-name> -n <namespace>
```

`Describe pod` to see `readiness probe` status:
```
kubectl describe pod <name> -n <namespace>
```
Look for `"Readiness"` in `Conditions` section

Check `deployment rollout` status:
```
kubectl rollout status deployment/<name> -n <namespace>
```
We can see:
```
ReplicaSet created?
Pods started?
Pods became Ready?
Old Pods scaled down?
Deployment finished?
```


```
livenessProbe = check if app is alive
readinessProbe = check if app is ready
startupProbe = check if app has finished starting
```

# Level 14: `HPA` Can't Scale:

The `HorizontalPodAutoscaler` (HPA) was configured correctly, but it couldn't scale because `metrics-server` was not installed. Without `metrics-server`, `K8s` can't know the CPU/memory usage of `pods`, so `HPA` can't make scaling decisions.

## How `K8s` Behaved:

```
    +-----------------------------------------+
    |           HPA wants to scale            |
    +-----------------------------------------+
                         │
                         ▼
    +-----------------------------------------+
    |   Needs current CPU/memory metrics      |
    +-----------------------------------------+
                         │
                         ▼
    +-----------------------------------------+
    |          Queries Metrics API            |
    +-----------------------------------------+
                         │
                         ▼
    +-----------------------------------------+
    |   Metrics API served by metrics-server  |
    +-----------------------------------------+
                         │
                         ▼
            +─────────────────────────+
            |  [X] metrics-server     |
            |      NOT INSTALLED      |
            +─────────────────────────+
                         │
                         ▼
    +-----------------------------------------+
    |       HPA shows "<unknown>/50%"         |
    +-----------------------------------------+
                         │
                         ▼
    +-----------------------------------------+
    |      Cannot make scaling decisions      |
    +-----------------------------------------+
```

## What `metrics-server` does:

```
+-----------------------------------------+
|  metrics-server runs as a deployment    |
|        in kube-system namespace         |
+-----------------------------------------+
                     │
                     ▼
+-----------------------------------------+
|    Collects resource metrics from       |
|         kubelet on each node            |
+-----------------------------------------+
                     │
                     ▼
+-----------------------------------------+
|           Aggregates metrics            |
|          (CPU, memory usage)            |
+-----------------------------------------+
                     │
                     ▼
+-----------------------------------------+
|        Exposes them via the             |
|       Kubernetes Metrics API            |
+-----------------------------------------+
                     │
                     ▼
+-----------------------------------------+
|       HPA, kubectl top, and other       |
|          tools consume metrics          |
+-----------------------------------------+
```

## `K8s` Metrics Architecture:

```
+-----------------------------------------+
|    kubectl top / HPA / Dashboard        |
+-----------------------------------------+
                     │
                     │ Query metrics
                     ▼
+-----------------------------------------+
|               Metrics API               |
|          (metrics.k8s.io/v1)            |
+-----------------------------------------+
                     │
                     │ Implemented by
                     ▼
+-----------------------------------------+
|             metrics-server              |
|           (kube-system ns)              |
+-----------------------------------------+
                     │
                     │ Scrapes metrics
                     ▼
+-----------------------------------------+
|          kubelet on each node           |
|      (cAdvisor provides container       |
|          CPU/memory stats)              |
+-----------------------------------------+
```

## `HPA` scaling logic:

```
spec:
  minReplicas: 1
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50 # Target: 50% CPU
```

How `HPA` decides to scale:

```
Current state:
- Deployment has 2 pods
- Pod 1: 80% CPU 
- Pod 2: 70% CPU 
- Average: 75% CPU

Target: 50% CPU

HPA calculation:
  desiredReplicas = ceil(currentReplicas × (currentMetric / targetMetric))
  desiredReplicas = ceil(2 × (75 / 50))
  desiredReplicas = ceil(2 × 1.5)
  desiredReplicas = ceil(3)
  desiredReplicas = 3

Action: Scale up from 2 to 3 replicas
```

Scaling behavior:
- Scale up: Immediate (when CPU > target)
- Scale down: 5-minute stabilization window (prevent flapping)
- Cooldown: 3 minutes between scale-up events, 5 minutes for scale-down
## `metrics-server` Configuration:
Standard installation:
```
kubectl apply -f
https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

For local development (`kind`, `Docker Desktop`, `minikube`):

```
# Add --kubelet-insecure-tls flag
kubectl patch deployment metrics-server -n kube-system --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": 
"--kubelet-insecure-tls"}]'
```

## Why `--kubelet-insecure-tls`?

- `metrics-server` pulls CPU/memory data from each node’s `kubelet` over HTTPS
- `kubelet` uses self-signed certs in local clusters (`kind`/`minikube`/`Docker Desktop`); those certs don’t match a trusted CA → TLS verification fails; `metrics-server` can’t connect → `kubectl top` breaks

# Level 15: Zero-Downtime Deployment Failure

## What Happened:

The deployment was configured with `maxUnavailable: 100%` and `maxSurge: 0`, which allowed Kubernetes to terminate all pods simultaneously during a rolling update.

## How `K8s` Behaved:

With wrong config (`maxUnavailable: 100%`, `maxSurge: 0`):

```
Rolling update starts (3 replicas → new version)
      ↓
maxUnavailable: 100% means can terminate 100% of 3 = all 3 pods
maxSurge: 0 means cannot create extra pods
      ↓
Step 1: Terminate all 3 old pods
      ↓
Step 2: Create 3 new pods
      ↓
Step 3: Wait for new pods to be ready
      ↓
Service has 0 pods for 10-30 seconds → DOWNTIME!
```

With fixed config (`maxUnavailable: 1`, `maxSurge: 1`):

```
Rolling update starts (3 replicas → new version)
      ↓
maxUnavailable: 1 means max 1 pod down (keep 2 running)
maxSurge: 1 means can create 1 extra pod (total 4)
      ↓
Step 1: Create 1 new pod (now 4 total)
Step 2: Wait for new pod to be ready
Step 3: Terminate 1 old pod (back to 3 total, 2 old + 1 new)
Step 4: Create another new pod (4 total again)
Step 5: Wait for it to be ready
Step 6: Terminate another old pod
Step 7-8: Repeat for last pod
      ↓
Service ALWAYS has at least 2 pods running → ZERO DOWNTIME!
```

`maxUnavailable:` Maximum number of pods that can be unavailable during the update.
`maxSurge:` Maximum number of pods that can be created.

# Level 16: PDB Blocks All Evictions

## What Happened:

The `PodDisruptionBudget (PDB)` was configured with `minAvailable: 3` for a deployment with 3 replicas. This created an impossible requirement: "Keep all 3 pods available while trying to evict one". Now, all voluntary pod evictions were blocked, preventing node maintenance, cluster upgrades, and autoscaling operations.

## How `K8s` Behaved:

```
Node drain requested (kubectl drain node-1)
      ↓
Kubernetes needs to evict pods on node-1
      ↓
Checks PDB for db-proxy pods
      ↓
PDB says: minAvailable = 3
Current healthy pods = 3
If we evict 1 pod: 3 - 1 = 2
Is 2 >= 3? NO!
      ↓
Eviction denied!
      ↓
Node drain FAILS
```


| Voluntary Disruptions (PDB applies) | Involuntary Disruptions (PDB doesn't apply) |
| ----------------------------------- | ------------------------------------------- |
| `kubectl drain`                     | Node crash                                  |
| Cluster upgrades                    | Node hardware failure                       |
| Autoscaler scale-down               | Pod killed by OOMKiller                     |
| Node decommissioning                | Network partition                           |


```
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: myapp-pdb
spec:
  minAvailable: 2 # Keep at least 2 pods running
selector:
  matchLabels:
    app: myapp
    
spec:
  minAvailable: 67%  # Keep at least 67% running

spec:
  maxUnavailable: 1  # Allow at most 1 pod unavailable

spec:
  maxUnavailable: 33%  # Allow at most 33% unavailable
```

# Level 17: Blue-Green Gone Wrong

## What happened:

Deployed a new version of the application (`GREEN`) using a `blue-green` deployment strategy, but users were still seeing the old version (`BLUE`).

The root cause: `service selector` wasn't updated to point to the new `deployment`.

Both `deployment` were running, but the service was only routing traffic to the `blue` (old) pods because of the label selector mismatch.

## How `K8s` Behaved:

`Service` selector matching:
```
Service selector:
  app: myapp
  version: blue

app-blue pods (OLD):
  labels:
    app: myapp 
    version: blue
  Result in a match, traffic would went through this.

app-green pods (NEW):
  labels:
    app: myapp
    version: green
  Result in an unmatch, no traffic.
```

```
Before fix:
kubectl get endpoints app-service
NAME              ENDPOINTS
app-service       10.1.0.5:8080,10.1.0.6:8080,10.1.0.7:8080
↑ These are the BLUE pods

After fix (selector changed to version: green):
kubectl get endpoints app-service
NAME              ENDPOINTS
app-service       10.1.0.8:8080,10.1.0.9:8080,10.1.0.10:8080
↑ These are the GREEN pods
```


| Aspect         | Blue-Green Deployment            | Rolling Update            |
| -------------- | -------------------------------- | ------------------------- |
| Resource usage | 2× (both versions running)       | 1× + surge                |
| Switchover     | Instant (change selector)        | Gradual (pod by pod)      |
| Testing        | Test full production environment | Limited testing window    |
| Rollback       | Instant (revert selector)        | Slower (re-deploy)        |
| Risk           | Lower (tested before switch)     | Medium (gradual exposure) |
| Cost           | Higher (double resources)        | Lower                     |


```
kubectl run -it --rm test --image=busybox --restart=Never -n k8squest -- wget -q -O- app-service

kubectl run: Create and runs a temporary Pod

-it:
  -i: Keep stdin open
  -t: Allocate a terminal (interactive mode)
  
--rm: aAutomatically deletes the Pod after it exists
test: the name of the Pod

--image=busybox: Uses the busybox container image, which is a tiny Linux image containing common utilities like `wget`, `sh`, `nslookup`, etc.

--restart=Never: Create a Pod directly, not a Deployment or Job

-n k8squest: Runs the Pod in the k8squest namespace

--: Everything after this is the cmd execute inside the container, not interpreted by kubectl

wget: Fetches a webpage
-q: Quiet mode (hide progress)
-O-: Send the download content to standard output instead of saving to a file
app-service: The K8s Service being accessed
```

# Level 18: Canary Weight Imbalance

## What happened:

The `canary deployment` had a 50/50 traffic split (5 stable pods, 5 canary pods) instead of the intended 90/10 split. 

This means half of users were exposed to the new, untested canary version - defeating the entire purpose of canary deployments.

`Canary deployments` should expose only a small percentage of users to the new version for safe testing.

| Stable Pods | Canary Pods | Total | Canary % | Use Case |
|-------------|-------------|-------|----------|----------|
| 9 | 1 | 10 | 10% | Initial canary |
| 8 | 2 | 10 | 20% | Expand testing |
| 5 | 5 | 10 | 50% | Half and half |
| 2 | 8 | 10 | 80% | Nearly full |
| 0 | 10 | 10 | 100% | Complete rollout |
| 95 | 5 | 100 | 5% | Large-scale 5% canary |

Correct configuration
```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-stable
spec:
  replicas: 50
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-canary
spec:
  replicas: 5
```

# Level 19: Stateful App Data Loss

## What happened:

`K8s` was using a `Deployment` for a database, which is designed for stateless applications.
Databases are stateful workloads that need:

- Stable, predictable `pod` names
- Persistent storage that follows the `pod`
- Ordered startup and shutdown
- Stable network identities

 `Deployments` don't provide any of these guarantees, which can lead to data loss, corruption, and split-brain scenarios:
 
 - Occurs in a distributed database when a network failure or communication problem causes two or more nodes to believe they are the primary (leader) at the same time. 
   
 - As a result, multiple nodes independently accept write requests, causing the database to diverge because different copies of the data are modified separately. When communication is restored, the cluster contains conflicting data and must resolve which changes are correct, which can be difficult or may result in data loss.
   
 - Modern distributed databases prevent split-brain by using leader election - choose one database to be leader and quorum protocols - voting through RESTFul API, ensuring that only a node with approval from a majority of the cluster can act as the leader and accept writes.

## `StatefulSet` Guarantees:

1. Stable `Pod` Names:
```
Deployment:   myapp-7d8f9c-abc12    (random hash)
StatefulSet:  myapp-0               (stable ordinal)
```

2. Stable `Network` Identity:
```
DNS for StatefulSet pods:
- database-0.database-service.k8squest.svc.cluster.local
- database-1.database-service.k8squest.svc.cluster.local
- database-2.database-service.k8squest.svc.cluster.local
```
Even if `pod` is deleted and recreated, `DNS` name stays the same.

3. Ordered Startup:
```
StatefulSet starts pods in order:
1. Create database-0, wait until Ready
2. Create database-1, wait until Ready
3. Create database-2, wait until Ready
Primary must start first.
```

4. Ordered Shutdown:
```
StatefulSet deletes pods in reverse order:
1. Delete database-2, wait until Terminated
2. Delete database-1, wait until Terminated
3. Delete database-0, wait until Terminated

Replicas stop before primary.
```

5. `Persistent Volume` Per `Pod`:

```
# StatefulSet with volumeClaimTemplates
apiVersion: apps/v1
kind: StatefulSet
spec:
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 10Gi

apiVersion: apps/v1
kind: StatefulSet
spec:
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 10Gi

Creates:
- PVC: data-database-0 - Pod: database-0
- PVC: data-database-1 - Pod: database-1
- PVC: data-database-2 - Pod: database-2

If database-0 pod is deleted, new database-0 pod gets same PVC.

PVC name = <template-name>-<statefulset-pod-name>
data-database-0
```

## Use case for each:

Use `Deployment`:
- Web servers
- API backends (stateless)
- Batch jobs (stateless)
- Microservices (no local state)
- Cache layers (can lose data)

Use `StatefulSet`:
- Databases (PostgreSQL, MySQL, MongoDB)
- Message queues (Kafka, RabbitMQ)
- Distributed caches (Redis Cluster)
- Consensus systems (etcd, ZooKeeper)
- Any app that needs stable identity

# Level 20: `ReplicaSet` Without Deployment

## What Happened:

 There is a standalone `ReplicaSet`, which is a low-level `K8s` resource that doesn't provide update management capabilities. While `ReplicaSets` ensure the right number of `pods` are running, they don't handle: 
 
 - Rolling updates
 - Rollbacks
 - Declarative version changes
 - Rollout history
   
`Deployments` are the recommended abstraction that manages `ReplicaSets` and provides all the features.

How to create a `deployment.yaml`
```
kubectl create deployment web-app --image=hashicorp/http-echo:latest -n k8squest --replicas=3 -- -text="Version 2.0" -listen=:8080
```