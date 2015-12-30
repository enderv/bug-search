# bug-search

Simple bug-search API using Elasticsearch to store bugs. Would be useful as a middleware to help limit duplicate bugs.
Based off [BugParty](https://bitbucket.org/abram/bugparty/src/b2d1909ae173?at=elasticsearch)

* http://localhost:9200/_plugin/gui/#/dashboard - For the ElasticSearch GUI
* http://localhost:5000/bug - For the Swagger Docs
* Port 5000 for the flask app.

### Tech

* [ElasticSearch] - Search!
* [Flask] - Python web framework

### Installation

You need docker-compose

```
docker-compose build
docker-compose up
```

#### docker-compose.yml

Think it all should just work....
You can edit projects in the BugSearch/configs/Dockerconfig

### Todos

 - Add nginx to serve app
 - Fix data volume container
