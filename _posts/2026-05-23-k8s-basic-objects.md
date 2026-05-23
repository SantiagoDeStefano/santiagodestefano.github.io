---
title: "K8s basic objects"
date: 2026-05-23
categories: [k8s]
---

## Pod

![Pod object](/assets/images/k8s_pod_object.png)

**Reminder:**
A `Pod` is a smallest deployment unit in K8s; Each `Pod` has one `container` as best practice.

For example:

```
Pod -> nginx container
```

`Pod` has its own

```
IP address
volumes
network
```

`my_pod_def.yaml`:
```
apiVersion: v1
kind: Pod
metadata:
	name: mypod
spec:
	containers:
	- name: mypod
	  image: nginx
```

`apiVersion: v1`: The API used to create a Pod object, as far as the author of this blog know, there is no `v2` or at least anything similar like `RESTFul API (/api/v1, /api/v2, ...` but:
```
v1                    : Pod, Service, Secret
apps/v1               : Deployment
batch/v1              : Job, CronJob
networking.k8s.io/v1  : Ingress, NetworkPolicy
```

`kind: Pod`: Declares that this resource is a `Pod`; `kind = what K8s object to create`. Other example: `kind: Service`, `kind: Deployment`, `kind: ConfigMap`.
Note that `kind` is not local K8s cluster like `kind` and `kubeadm`.

`name: mypod`: Sets the name of the `Pod` to `"mypod"`

`-name: mypod`: set the name of the container to `"mypod"`

`image: nginx`: Only one container in this `Pod`, and this container is created from the image `nginx:latest`
## How a pod is created?

![How a pod object is created](/assets/images/k8s_pod_how_create.png)

**Additional:**

`API Server` would enforce both `Authentication` and `Authorization`; then, `Admisison Controller` check before storing object definition to `etcd`.

`Admission Controller` would block unsecured `Pod` like:
```
Pod with `privileged: true`
Pod that uses `hostPath` to mount Node's filesystem 
Pod that enable `hostPID`, `hostIPC`, `hostNetwork`
Container: `allowPrivilegeEscalation: true`
Container that run with root user 
```

![Pod life cycle](/assets/images/k8s_pod_lifecycle.png)

The state of the pod is shown as "Unknown" when the `Kubelet` stops reporting to the `API Server`'; Mean `Step 7` failed.
## How a pod is deleted?

![How a pod is deleted](/assets/images/k8s_pod_how_delete.png)

## ReplicaSet

![ReplicaSet](/assets/images/k8s_replicaset.png)

Note: `ReplicaSet` is stored in `etcd`.

`my_replicaset.yaml`:
```
apiVersion: apps/v1
kind: ReplicaSet
metadata:
	name: nginx-replicaset
	labels:
		app: nginx
spec:
	replicas: 3
	selector:
		matchLabels:
			app: nginx
	template:
		metadata:
			labels:
				app: nginx
		spec:
			containers:
			- name: nginx
			  image: nginx:latest
			  ports:
			  - containerPort: 80
```

`metadata`: General information (name, labels, etc.)

`replicas`: The number of `Pod` replicas

`selector`: The conditions used to manage the `Pods`; which means managing `Pods` that have label `app=nginx` 

`template`: The configuration for creating new `Pods`; notes that `selector` must match `template.metadata.labels`;
```
selector says: find app=nginx
template creates: app=nginx
```

## Deployment

![Deployment](/assets/images/k8s_deployment.png)

`my_deployment.yaml`:
```
apiVersion: apps/v1
kind: Deployment
metadata:
	name: nginx-deployment
	labels:
		app: nginx
spec:
	replicas: 3
	selector:
		matchLabels:
			app: nginx
	template:
		metadata:
			labels:
				app: nginx
		spec:
			containers:
			- name: nginx
			  image: nginx:latest
			  ports:
			  - containerPort: 80
```

## How a deployment is created?

![How a deployment is created](/assets/images/k8s_deployment_how_create.png)

## How a deployment is deleted?

![How a deployment is deleted](/assets/images/k8s_deployment_how_delete.png)

## Service:

`Service` is an object in K8s that provides a way to connect and communicate between `Pods` , or between `Pods` and outside world.
![[Pasted image 20260522015355.png]]
The `Deployment` ensures `Pods` are running, while the `Service` forwards incoming requests to available `Pods`, even if `Pod` IPs change.

Note that `Service` is different from `CNI`;
```
CNI:
- gives Pod an IP
- connects Pod networking between nodes

Service:
- gives stable virtual IP/name
- forwards traffic to matching Pods
```

## Service Type

![[Pasted image 20260522015716.png]]

| Feature       | ClusterIP                                                                | NodePort                                               | LoadBalancer                      |
| ------------- | ------------------------------------------------------------------------ | ------------------------------------------------------ | --------------------------------- |
| Exposition    | Internal cluster                                                         | External                                               | External                          |
| Accessibility | Default service type. Internal clients use a stable internal IP address. | Through a dedicated port `30000 - 32767` on all nodes. | Through a cloud load balancer IP. |
| Use cases     | Internal communication                                                   | Testing public/private access for a short time.        | External production access.       |
Note: Another Service type is `ExternalName`, used to create a `CNAME` DNS record. Read more about [DNS records](https://www.cloudflare.com/learning/dns/dns-records/dns-a-record/) and [Kubernetes ExternalName Service](https://adil.medium.com/kubernetes-service-externalname-6b4cfb7640a2).

`my_service.yaml`
```
apiVersion: v1
kind: Service
metadata:
	name: nginx
spec:
	selector:
		tier: frontend
	ports:
		- port: 3000
		  protocol: TCP
		  targetPort: 80
	type: ClusterIP
```

`metadata`: Sets the service name to `nginx`

`tier: frontend`: Select the `Pods` to expose based on their labels

`- port: 3000`: The port the `Service` will expose inside the cluster; Access the `Service` through port 3000

`protocol: TCP`: Network protocol used; Default is `TCP`

`targetPort: 80`: Port the selected `Pods` to forward traffic to; This `Service` routes traffic from port 3000 (inside the cluster) to port 80 of the matching `Pods`

`type: ClusterIP`: Service type; can be `ClusterIP`, `NodePort`, `LoadBalancer`

## Namespace

`Namespaces` provide a mechanism for isolating groups of resources within a single cluster.

![[Pasted image 20260522202458.png]]

`Practical Applications`:
- Separate development, testing, and production environment (`dev`, `qa`)
- Manage resources by application group or user group

`Some resources are not tied to a Namespace, such as`:
- `Nodes`
- `PersistentVolumes`
- `ClusterRoles`

`Default Namespace in K8s`:
- `default`: The default `Namespace` when no specific `Namespace` is specified
- `kube-system`: Contains the resources and `Pods` essential for the operation of K8s (e.g., `kube-dns`, `kube-proxy`, `coredns`)

## Volume

There are 5 types of `Volume` in `K8s`:
```
- emptyDir
- PersistentVolume (PV)
- PersistentVolumeClaim (PVC)
- ConfigMap
- Secret
```

![[Pasted image 20260522203104.png]]

`Volume` in K8s is a **storage mechanism** that allows containers within a `Pod` to:
- Share data between containers
- Store data temporarily (data exists only while `Pod/container` exists) or persistently (saved even if `Pod` is deleted/recreated)
- Each `Volume` is attached to a `Pod` and can be shared by all `containers` within that `Pod`
- `Volumes` are mounted into the `containers`

`Type of Volumes in K8s`:

`emptyDir`: a `temporary volume` that is created when a `Pod` starts and is deleted when the `Pod` stops; Commonly used to share data between `containers` within the same `Pod`.
```
apiVersion: v1
kind: Pod
metadata:
	name: emptydir-example
spec:
	containers:
	- name: nginx
	  image: nginx
	  volumeMounts:
	  - mountPath: "/data"
	    name: temp-storage
	volumes:
	- name: temp-storage
	  emptyDir: {}
```

`containers`: The container runs the `nginx` image

`volumeMounts`: Mounts the `temp-storage` at `/data` within the `container`

`- name: temp-storage`: Defines a volume named 'temp-storage' with `emptyDir` type

## Persistent Volume (PV)

`Persistent Volume (PV)` is a **storage resource** in `K8s` that is managed by the cluster

![[Pasted image 20260522205242.png]]

Simple understanding: 
`PV` is not a disk itself, `PV` is `K8s` saying: 
```
"Hey, I know this disk exists, and Pods can use it."
```

```
Disk = real room
PV   = room registration paper
Pod  = person using the room
```

## Persistent Volume Claim (PVC)

`Persistent Volume Claim (PVC)` is a **user requested** to consume storage resources `(PV)`

![[Pasted image 20260522210039.png]]

Simple understanding:
```
PV  = actual room
PVC = booking request: "I need a room"
Pod = person using the booked room
```

Actual flow:
```
1. Admin creates/provides PV
   "Here is 10GB storage"

2. Developer creates PVC
   "I need 5GB storage"

3. Kubernetes binds PVC to a suitable PV
   "This PV matches your request"

4. Pod uses PVC
   "Pod can now save files there"
```

### PV and PVC

**PV**:
```
apiVersion: v1
kind: PersistentVolume
metadata:
	name: pv-example
spec:
	capacity:
		storage: 1Gi
	accessModes:
		- ReadWriteOnce
	persistentVolumeReclaimPolicy: Retain
	hostPath:
		path: "/mnt/data"
```

`metadata:` Create a `PV` named `pv-example`

`storage: 1Gi`: 1 gibibyte, about 1.07 GB

`- ReadWriteOnce`: Can be mounted read/write by one node at a time

`persistentVolumeReclaimPolicy`:
```
- Retain: Keep the PV/data after PVC is deleted. Manual cleanup needed
  
- Delete: Delete the PV and underlying storage after PVC is deleted. Common with dynamic cloud storage
```

`path: "/mnt/data"`: Use node folder `/mnt/data` as the real storage, should've uses Cloud

`PVC`:
```
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
	name: pvc-example
spec:
	accessModes:
		- ReadWriteOnce
	resources:
		requests:
			storage: 1Gi
```

The `PV` defines the actual storage resource (`1GB` with `ReadWriteOnce` mode), and the `PVC` requests and binds to that storage for use by `Pods`.

## ConfigMap

`ConfigMap` is an object in `K8s` used to **store non-sensitive configuration data** in **key-value** pairs.

![[Pasted image 20260523125257.png]]

```
apiVersion: v1
kind: Pod
metadata:
	name: configmap-example
spec:
	containers:
	- name: nginx
	  image: nginx
	  volumeMounts:
	  - mountPath: "/etc/config"
	    name: config-volume
	volumes:
	- name: config-volume
	  configMap:
		  name: my-configmap
```

`-mountPath: "/etc/config"`: The path inside the container where the `ConfigMap` files will appear

`configMap`: Specify that this volume is populated by a `ConfigMap`

```
- ConfigMap my-configmap is mounted into the nginx container at /etc/config.
Each key in the ConfigMap becomes a file inside /etc/config.

- Sets up a `Pod` running `nginx`, with a `ConfigMap` named `"my-configmap"` mounted into `/etc/config`
```

Example use case:

`ConfigMap`:
```
apiVersion: v1
kind: ConfigMap
metadata:
  name: my-configmap
data:
  default.conf: |
    server {
      listen 80;
      location / {
        return 200 "Hello from ConfigMap\n";
      }
    }
```

`Pod` mount it:
```
apiVersion: v1
kind: Pod
metadata:
  name: configmap-example
spec:
  containers:
  - name: nginx
    image: nginx
    volumeMounts:
    - mountPath: "/etc/nginx/conf.d"
      name: config-volume
  volumes:
  - name: config-volume
    configMap:
      name: my-configmap
```

**Explanation:**
- The `ConfigMap` key  is named: `default.conf`; 
- When mounted as a volume, `K8s` creates a file with that name: `/etc/nginx/conf.d/default.conf`; 
- Nginx automatically reads config files from: `etc/nginx/conf.d`;
So `nginx` sees that file as its config.

`ConfigMap`
```
data:
  default.conf: |
    server {
      listen 80;
    }
```

Would becomes `/etc/nginx/conf.d/default.conf` with content:
```
server {
  listen 80;
}
```

## Secrets

![[Pasted image 20260523132105.png]]

`Secret` is an object in `K8s` used to **store** and **manage sensitive information** (such as passwords, API tokens, or SSL certificates).

**Type of Secrets**:

```
- Opaque: The default type, used to store arbitrary key-value pairs.
Use case: 
DB_PASSWORD=123456;
API_KEY=abcd;

- kubernetes.io/dockerconfigjson: Used for private Docker registry login.
Use case:
Pull image from private Docker Hub / ECR / GitLab registry;
kubernetes.io/tls;

- TLS: Stores TLS certificate + private key.
Use case:
HTTPS certificate for Ingress;

- Service Account Token: Token used by a SA to talk to the K8s API server.
Use case:
Pod uses SA token to call API Server;
```

```
apiVersion: v1
kind: Pod
metadata:
	name: secret-example
spec:
	containers:
	- name: nginx
	  image: nginx
	  volumeMounts:
	  - mountPath: "/etc/secret"
	    name: secret-volume
	volumes:
	- name: secret-volume
	  secret:
	  secretName: my-secret
```

`mountPath: "/etc/secret"`: The path inside the container where the Secret files will appear.

`secretName: my-secret`: Use the Secret named `my-secret` as the volume source.

Sets up a `Pod` running `nginx`, with a `Secrets` named `"my-secret"` mounted into **`/etc/secret`**

At this point, you might question why a lot of other `yaml` also uses `mountPath`, `volumeMounts` and all. That  is because `K8s` uses the same pattern for many volume types.

```
volume      = what storage/data source
volumeMount = attach it to container
mountPath   = folder path inside container
```

In which many of these volume types uses:

```
ConfigMap
Secret
emptyDir
hostPath
PVC
```
## Daemonset

![[Pasted image 20260523135518.png]]

`DaemoSet` is an object in `K8s` that ensures a `Pod` runs on every `Node` in the cluster.

Common use case:
```
- Monitoring: Run monitoring tools such as Prometheus Node Exporter on every Node
- Security: Run security monitoring agents on all Nodes
- Storage: Running a cluster storage daemonsete on every Node
```

## Ingress

![[Pasted image 20260523140727.png]]

`Ingress` in an object in `K8s` that is allowed to **manage HTTP and HTTPS traffic** to applications running inside the cluster.
`Ingress` provides capabilities such as:
```
- Routing traffic based on hostname and URL path
- Establishing HTTPS connections using TLS
- Centralized management of external traffic into the cluster
```

- `Ingress Resource`: defines the `HTTP/HTTPS` routing rules:
	- Hostname routing: Routes traffic based on hostname, e.g. `example.com`.
	- Path-based routing: Routes traffic based on URL paths, e.g. `/api`, `/frontend`.

- `Ingress Controller`:
	- The `Ingress Resource` only works when there is an active Ingress Controller.
	- The `Ingress Controller` processes Ingress Resources and routes traffic according to the defined rules.
	- Popular Ingress controllers:
		- `NGINX` Ingress Controller
		- `Traefik`
		- `HAProxy`

`Ingress - path based routing`
```
spec:
	rules:
	- host: example
	  http:
		  paths:
		  - path: /api
		    pathType: Prefix
		    backend:
			    service:
				    name: api-service
				    port:
					    number: 8080
		  - path: /web
		    pathType: Backend
		    backend:
			    service: api-service
				    name: web-service
				    port:
					    number: 80
```

`- host: example`: Route only requests with this host.

`-path: /api`: Requests to `http(s)://example.com/api/*` go to the `'api-service'` on port 8080.

`- path: /web`: Requests to `http(s)://example.com/api/*` go to the `'web-service'` on port 80.

`Ingress - Host based Routing`
```
spec:
	rules:
	- host: api.example.com
	  http:
		  paths:
		  - path: /
		    pathType: Prefix
		    backend:
			    service:
				    name: api-service
				    port:
						number: 8080
	- host: web.example.com
	  http:
		  paths:
		  - path: /
		    pathType: Prefix
		    backend:
			    service:
				    name: api-service
				    port:
						number: 80
```

`- host: api.example.com`: Matches requests sent to `'api.example.com'` with `("/")` and routes them to the `'api-service Service'` on port 8080.

`- host: web.example.com`: Matches requests sent to `'web.example.com'` with `("/")` and routes them to the `'web-service Service'` on port 80.

`Ingress - TLS`:
```
spec:
	tls:
	- hosts:
	  - example.com
	  secretName: tls-secret
	rules:
	- host: example.com
	  http:
		  paths:
		  - path: /
		    pathType: Prefix
		    backend:
			    service:
				    name: my-service
				    port:
					    number: 80
```

`tls`: Sets up TLS for incoming requests to the host `"example.com"`

`- example.com`: Lists the host names the TLS setting applies to

`secretName: tls-secret`: Refers to the `K8s Secret` containing the `TLS` certificate and key

`rules`: Configures how traffic to `example.com` is routed

## Job

A `Job` in `K8s` is a **controller** that **runs a task once** until it finishes successfully

- `Pod` Failure Policy: Control how `Jobs` handle `Pod` failures
- Parallel Processing: `Jobs` can be configured to run multiple `Pods` in parallel
- Use case:
	- Running a data processing script one time
	- Running a database migration when deploying a new version

```
apiVersion: batch/v1
kind: Job
metadata:
	name: example-job
spec:
	template:
		spec:
			containers:
			- name: job-container
			  image: busybox
			  command: ["echo", "Hello from Job"]
			restartPolicy: Never
```

`image: busybox`: `Container` image to run

`command`: Command for the `container` to execute

`restartPolicy: Never`: `Pods` will be restarted if they complete for fail

## CronJob

A `CronJob` is like a `Job`, but in **runs on a schedule**. It creates a new `Job` automatically at the chosen time.

- Scheduling: `CronJobs` use a schedule field that accepts standard cron syntax (e.g., */5 * * * * for every 5 minutes)
- Use case:
	- Runs a daily backup at midnight
	- Send daily email reports
	- Clean up old files or logs every week
	
```
apiVersion: batch/v1
kind: CronJob
metadata:
	name: example-cronjob
spec:
	schedule: "0 * * * *"
	jobTemplate:
		spec:
			template:
				spec:
					containers:
						- name: cronjob-container
						  image: busybox
						  command: ["echo", "Hello every hour"]
					restartPolicy: Never
```

`schedule: "0 * * * *"`: `Cron` schedule runs at every hour at minute 0

`image: busybox`: `Container` image to run

`restartPolicy: Never`: `Pods` will not be restarted if they complete for fail

## Recap

|Object type|Purpose|Explanation|
|---|---|---|
|Pod|The smallest execution unit|Runs one or more containers.|
|Deployment, ReplicaSet, StatefulSet, DaemonSet|Managing Pods|Deployment creates ReplicaSet under the hood. DaemonSet distributes Pods across nodes. StatefulSet gives each Pod a stable identity so it can reconnect to its data after failure.|
|Service|Manage services|Provides stable access to Pods.|
|PersistentVolume (PV), PersistentVolumeClaim (PVC)|Manage disks|A PVC is like a request/certificate to use a PV, so Pods attached to a PVC can access the PV.|
|ConfigMap, Secret|Manage environment variables and secrets|ConfigMap stores non-sensitive config. Secret stores sensitive data like passwords/tokens.|
|Namespace|A virtual cluster|Objects with the same function/team/environment are usually grouped into one namespace.|
|Job, CronJob|Discontinuous running Pods|Job runs a task once. CronJob runs a task on a schedule.|
