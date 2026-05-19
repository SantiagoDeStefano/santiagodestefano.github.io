---
layout: page
title: Categories
permalink: /categories/
---

## ML/DL from Scratch {#ml-dl}
{% for post in site.posts %}
{% if post.categories contains 'ml-dl' %}
- [{{ post.title }}]({{ post.url }})
{% endif %}
{% endfor %}

## Kubernetes {#k8s}
{% for post in site.posts %}
{% if post.categories contains 'k8s' %}
- [{{ post.title }}]({{ post.url }})
{% endif %}
{% endfor %}