---
title: "K8s high level concepts"
date: 2026-05-23
categories: [k8s]
---

# Motivation of using K8s

![Motivation 1](/assets/images/k8s_motivation_1.jpg)
![Motivation 2](/assets/images/k8s_motivation_2.png)

# High Level Architecture

![High level architecture](/assets/images/k8s_high_level_architecture.png)

# Concept of each components

![API Server and Scheduler](/assets/images/k8s_control_plane_apisv_scheduler.png)

## **`API Server`** example:
https://my-cluster.example.com:6443 - Kubernetes API Server endpoint

```
kubectl get pods
```

`kubectl` sends an HTTP request to the API Server, which look like:

```
GET /api/v1/namespaces/default/pods
Host: my-cluster.example.com:6443
Authorization: Bearer <token>
```

The **API Server** then checks auth, validates the request, talks to `etcd`, and returns the pod list.

Intuition:

```
kubectl = client
kube-apiserver = server
etcd = database
```

## **`Pod = smallest deployable unit in K8s`**, example:

Which is **not a docker container**, but usually a wrapper around one or more containers that must run together.

Example of an **YAML** to deploy a Pod:

```
apiVersion: v1
kind: Pod
metadata:
  name: my-nginx
spec:
  containers:
  - name: nginx
    image: nginx
```

In which the Pod contains

```
Pod: Container (nginx)
```

Each Pod get **one IP**:

```
Pod IP: 10.244.1.5
```

Inside the Pod:

```
localhost: shared
```

So container can call other using:

```
localhost:3000
```

**Pods are ephemeral**:

So if a Pod dies:

```
Pod destroyed
New pod created
New IP possible
```

So people uses (we would go more details into this in the future):

```
Deployment
ReplicaSet
Service
```

**1 pod - 1 container is considered best practice for K8s but there are use cases where 2 container can be in the same Pod:**

```
apiVersion: v1
kind: Pod
metadata:
  name: app-with-sidecar
spec:
  containers:
  - name: main-app
    image: nginx

  - name: logger
    image: logger-monitoring
    command: ["sh", "-c", "while true; do echo logging...; sleep 5; done"]
```

**1 pod:**
```
Container 1: nginx (main app)
Container 2: logger (monitoring/sidecar)
```


## **`Scheduler`** example:
API server stores pod request in `etcd` (we would go into this later) to run nginx-pod

```
I want nginx-pod running
```

But `nodeName = none`

Then **Scheduler** watches for **unscheduled pods**, it sees:

```
nginx-pod have no node
```

The **`Scheduler`** inspect:

```
Node1: enough CPU/RAM? yes
Node2: enough CPU/RAM? yes
Node3: tainted? no
```

Then it pick the best one, e.g.: `Node2`

```
Bind nginx-pod -> Node2
```

Then it tells the **API Server**:

```
Bind nginx-pod -> Node2
```

**`kubelet`** on Node2 sees assignment, then pulls the image + starts container.

![Controller and etcd](/assets/images/k8s_control_plane_controller_etcd.png)

## **`etcd - K8s database`**: 
It stores the cluster's source of truth, which can includes:

```
Pods
Deployments
Services
Nodes
Configs
Secrets
```

For example, when running:

```
kubectl apply -f deployment.yaml
```

**`API Server`** stores desired state in **`etcd`**:

```
"I want 3 nginx pods"
```

- **`kube-controller-manager = the fixer`** :
  
It constantly checks `Current State vs Desired State` 

For example:

`Desired State = 3 nginx pods` 
`Current State = 2 running pods`

The `kube-controller-manager` sees a mismatch, tells the `API Server` to:

```
"Create another pods"
```

![kubelet and kube-proxy](/assets/images/k8s_control_plane_kubelet_kubeproxy.png)

## **`kubelet = node agent (worker on each node)`**:

Every node runs a `kubelet`. Which execute command from `API Server`; Easy understanding:

```
"API Server says run this pod? Fine, I’ll make it happen."
```

For example, `Scheduler` assigns pod:

```
nginx-pod -> Node2
```

`kubelet` on `Node2` would:
Reads pods spec from `API Server`;
Talks to container runtime (`containerd, CRI-O, ...`);
Pulls images;
Starts container;

```
kubelet = pod executor on the node
```

## `kube-proxy = network traffic router` 

It handles `Service` networking.

For example:

```
Service: my-app
ClusterIP: 10.96.0.10
```

Behind it:

```
Pod A: 10.244.1.2
Pod B: 10.244.2.5
```

Upcoming traffic hits `ClusterIP: 10.96.0.10`;

`kube-proxy` sets `iptables/ipvs` rules, which route traffic to Pod A/B.

```
kube-proxy = traffic forwarder/load balancer
```
![Container Runtime](/assets/images/k8s_worker_node_container_runtime.png)

## `Container Runtime = software that actually runs containers`

`K8s` does not run `containers` directly;

Common container runtimes

`containerd`: Most common in modern K8s
`CRI-O`: K8s-focused runtime