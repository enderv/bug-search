__author__ = 'Chris'
import elasticsearch
import elasticsearch.helpers
import itertools
# important performance related constants


def iter_batches(iterable, size):
    '''split up an iterable into batches.

    :returns: an iterator of lists
    '''
    i = iter(iterable)
    while True:
        batch = list(itertools.islice(i, size))
        if len(batch) == 0:
            raise StopIteration
        yield batch

BULK_READ_SIZE = 1000
BULK_WRITE_SIZE = 100

class ESType(object):
    def __init__(self, index, doc_type, client):
        assert index
        assert doc_type
        self.doc_type = doc_type
        self.index = index
        self.client = client
        self.kwargs = {
            'index': self.index
            ,'doc_type': self.doc_type
        }

    def refresh(self):
        self.client.indices.refresh(self.index)

    def update_doc(self, doc_id, updates):
        body = {'doc': updates, 'doc_as_upsert':True}
        return self.client.update(id=doc_id, body=body, **self.kwargs)

    def update(self, docs):
        return self.bulk(updates=docs)

    def bulk(self, inserts=[], replacements={}, updates={}):
        actions = [{'_op_type': 'index', '_source': body} for body in inserts]
        actions.extend([{'_id': id, '_op_type': 'index','_source': body}
                        for (id, body) in replacements.iteritems()])
        actions.extend([{'_id': id, '_op_type': 'update',
                        'doc_as_upsert': True, 'doc': body}
                        for (id, body) in updates.iteritems()])
        results = elasticsearch.helpers.bulk(self.client,
                actions, chunk_size=BULK_WRITE_SIZE, **self.kwargs)

        if results[1]:
            raise Exception(results[1])
        return True

    def index(self, doc):
        return self.client.index(body=doc, **self.kwargs)

    def __contains__(self, item):
        return self.client.exists(id=item, **self.kwargs)

    def get(self, key, default=None):
        try:
            response = self.client.get(id=key, **self.kwargs)
            return response['_source']
        except ElasticSearch.Error404:
            return default

    def __iter__(self):
        return iter(self.keys())

    def count(self):
        return int(self.client.count(q='*', **self.kwargs)['count'])

    def search(self, body, exclude_topics=True, **user_kwargs):
        kwargs = self.kwargs.copy()
        kwargs.update({'size': 30}) # default query size
        kwargs.update(user_kwargs)

        if exclude_topics:
            kwargs.setdefault('_source_exclude', []).append('topics.*')

        response = self.client.search(body=body, **kwargs)
        return response['hits']['hits']

    def scan(self, body, exclude_topics=True, **user_kwargs):
        '''good for very big request like getting all the docs'''
        kwargs = self.kwargs.copy()
        kwargs.update({'size': BULK_READ_SIZE})
        kwargs.update(user_kwargs)

        if exclude_topics:
            kwargs.setdefault('_source_exclude', []).append('topics.*')

        response = elasticsearch.helpers.scan(self.client, query=body, **kwargs)
        return response

    def mget(self, docids, exclude_topics=True, **user_kwargs):
        '''returns a generator of (id, document) pairs, one for
            each id in docids'''
        kwargs = self.kwargs.copy()
        kwargs.update(user_kwargs)
        if exclude_topics:
            kwargs.setdefault('_source_exclude', []).append('topics.*')

        for batch in iter_batches(docids, BULK_READ_SIZE):
            results = self.client.mget({'ids': list(batch)}, **kwargs)
            for r in results['docs']:
                yield r['_id'], r['_source']

    def keys(self):
        response = self.scan({
            'query': {
                'match_all': {}
            }
        }, fields=[])

        return sorted([hit['_id'] for hit in response])

    def values(self):
        response = self.scan({
            'query': {
                'match_all': {}
            }
        }, _source=True)

        sorted_hits = sorted(response, key=lambda x: x['_id'])
        return [hit['_source'] for hit in sorted_hits]

    def items(self, **kwargs):
        response = self.scan({
            'query': {
                'match_all': {}
            }
        }, _source=True, **kwargs)

        return [(hit['_id'], hit['_source']) for hit in response]



class ElasticSearch(object):
    """
    A helpful ElasticSearch wrapper with some basic utilities
    """
    Error404 = elasticsearch.exceptions.NotFoundError

    # types
    BUGS = 'bug'
    TOPICS = 'topic'
    GENERATED = 'generated'
    SIMILARITIES = 'similarities'

    BUGPARTY_INDEX_NAME = 'bugparty_internal'
    TASKS = 'tasks'
    PROJECTS = 'project'


    #TODO change defaults
    def __init__(self, index="bug", hosts='http://localhost:9200', doc_type="bug"):
        self.index = index
        self.hosts = hosts
        self.doc_type = doc_type
        self.client = elasticsearch.Elasticsearch(self.hosts)
        self.kwargs = {
            'index': self.index
            ,'doc_type': self.doc_type
        }


    def __delitem__(self, key):
        """Delete Item by Key"""
        self.client.delete(id=key, ignore=[404], **self.kwargs)

    def __setitem__(self, key, value):
        response = self.client.index(id=str(key), body=value, **self.kwargs)

    def __getitem__(self, key, fields=None):
        key = str(key)
        if fields:
            response = self.client.get(id=key, fields=fields, **self.kwargs)
            return response['fields']
        else:
            response = self.client.get(id=key, **self.kwargs)
            return response['_source']

    def search(self, body, index=None, doc_type=None, exclude_topics=True, **user_kwargs):
        """A Basic search """
        if index:
            self.kwargs['index'] = index
        if doc_type:
            self.kwargs['doc_type'] = doc_type

        kwargs = self.kwargs.copy()
        kwargs.update({'size': 30}) # default query size
        kwargs.update(user_kwargs)

        if exclude_topics:
            kwargs.setdefault('_source_exclude', []).append('topics.*')

        response = self.client.search(body=body, **kwargs)
        return response['hits']['hits']

    #TODO move this somewhere! manage.py?
    def create_dbs_for_project(self):
        """Scaffolding for this particular project need to move elsewhere"""
        assert self.index
        self.client.indices.create(self.index, ignore=400)
        bug_mapping = {
            "bug": {
                "_id": {
                  "path": "bugid"
                },
                "_timestamp": {
                  "enabled": True,
                  "path": "openedDate",
                  "format": "dateOptionalTime"
                },
                "properties": {
                  "openedDate": {
                    "type": "date",
                    "format": "dateOptionalTime"
                  }
                }
              }
            }
        self.client.indices.put_mapping(index=self.index,
            doc_type=ElasticSearch.BUGS, body=bug_mapping)
        generated_mapping = {
            "generated" : {
                "properties" : {
                    "data.tar.gz" : {
                        "type" : "string",
                        "index" : "no",
                        "norms" : {
                            "enabled" : False
                        }
                    }
                }
            }
        }
        self.client.indices.put_mapping(index=self.index,
            doc_type=ElasticSearch.GENERATED, body=generated_mapping)

    def search_fields(self, fields, query, index=None, doc_type=None):
        """Search multiple fields and aggreate the results to one list"""
        result_dict = {}
        master_list = []
        scores = {}
        for field in fields:
            items = self.search({
            'query': {
                'fuzzy_like_this_field': {
                    field: {
                        'like_text': query
                        ,'max_query_terms': 250
                    }
                }
            }
        }, index=index, doc_type=doc_type,  size=25)
            if len(items) > 0 :
                result_dict[field] = items

        seen = set()
        all = []
        for field in result_dict:
            for item in result_dict[field]:
                if item['_id'] not in seen:
                    seen.add(item['_id'])
                    all.append(item)

        return all

    def search_field(self, field, query, index=None, doc_type=None):
        """Search single specified field and return results list"""
        return self.search({
            'query': {
                'fuzzy_like_this_field': {
                    field: {
                        'like_text': query
                        ,'max_query_terms': 250
                    }
                }
            }
        }, index=index, doc_type=doc_type, size=25)

if __name__ == "__main__":
    print"here"
    test = ElasticSearch()

    test.search_fields(['title','description'],'load')