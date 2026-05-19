---
layout: home
---

## Categories

### ML/DL from Scratch
{% for post in site.posts %}
{% if post.categories contains 'ml-dl' %}
- [{{ post.title }}]({{ post.url }})
{% endif %}
{% endfor %}

### Kubernetes
{% for post in site.posts %}
{% if post.categories contains 'k8s' %}
- [{{ post.title }}]({{ post.url }})
{% endif %}
{% endfor %}