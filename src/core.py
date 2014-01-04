from collections.abc import Sequence
import threading
import urllib.request
from urllib.parse import urlparse
import queue
import os
import time
import re
import sys


class Album(dict):
    def __getattribute__(self, name):
        if name in ('aid', 'created', 'description', 'owner_id', 'size',
                    'thumb_id', 'thumb_src', 'title', 'updated'):
            return self[name]
        else:
            return dict.__getattribute__(self, name)

    def __str__(self):
        return 'Album({owner_id}_{aid}, {title})'.format(
                                                    owner_id=self['owner_id'],
                                                    aid=self['aid'],
                                                    title=self['title'])


class Photo(dict):
    @property
    def url(self):
        for src in ('src_xxxbig', 'src_xxbig', 'src_xbig',
                    'src_big', 'sc_small'):
            if src in self:
                return self[src].replace('\\', '')

    def __getattribute__(self, name):
        if name in ('aid', 'comments', 'created', 'height', 'lat', 'likes',
                      'long', 'owner_id', 'pid', 'src', 'src_big', 'src_small',
                      'src_xbig', 'src_xxbig', 'tags', 'text', 'width'):
            return self[name]
        else:
            return dict.__getattribute__(self, name)

    def __str__(self):
        return 'Photo({aid}_{pid})'.format(aid=self['aid'], pid=self['pid'])


class Audio(dict):
    @property
    def name(self):
        return '{0} - {1}'.format(self['artist'], self['title'])

    @property
    def url(self):
        return self['url'].replace('\\', '')

    def __getattribute__(self, name):
        if name in ('aid', 'comments', 'created', 'height', 'lat', 'likes',
                    'long', 'owner_id', 'pid', 'src', 'src_big', 'src_small',
                    'src_xbig', 'src_xxbig', 'tags', 'text', 'width'):
            return self[name]
        else:
            return dict.__getattribute__(self, name)

    def __str__(self):
        return 'Audio({owner_id}_{aid})'.format(owner_id=self['owner_id'],
                                                aid=self['aid'])


class DownloadTask():
    def __init__(self, url, destination):
        self.url = url
        self.destination = destination


class Downloader():
    def __init__(self, vk_api, num_threads=4):
        self.api = vk_api
        self.num_threads = num_threads
        self.tasks = queue.Queue()
        self.all_fetched_event = threading.Event()

    def parallelize(function):  # @NoSelf
        def foo(*args, **kwargs):
            self = args[0]
            self.all_fetched_event.clear()
            workers = self._parallel_download()
            try:
                function(*args, **kwargs)
            finally:
                self.all_fetched_event.set()
                for worker in workers:
                    worker.join()
        return foo

    def __download(self, url, attempts=10):
        for i in range(attempts):
            try:
                response = urllib.request.urlopen(url)
            except urllib.error.HTTPError as e:
                print('{0} ({1})'.format(str(e), url), file=sys.stderr)
            else:
                return response.read()

    @parallelize
    def get_album_photos(self, destination, user_id=None, group_id=None,
                         album_ids=None):
        owner = {}
        if user_id:
            owner['uid'] = user_id
        elif group_id:
            owner['gid'] = group_id
        if not album_ids:
            album_ids = ['profile', 'wall', 'saved'] +\
                    list(map(lambda x: Album(x).aid,
                             self.api.request('photos.getAlbums', **owner)))
        elif not isinstance(album_ids, Sequence):
            raise TypeError('album_ids is not a sequence')
        for album in album_ids:
            for photo in self.api.request('photos.get', aid=album, **owner):
                p = Photo(photo)
                path = os.path.join(destination, str(p.aid), str(p.pid)) +\
                        os.path.splitext(p.url)[-1]
                task = DownloadTask(p.url, path)
                self.tasks.put(task)

    @parallelize
    def get_user_photos(self, destination, user_id=None):
        owner = {}
        if user_id:
            owner['uid'] = user_id
        response = self.api.request('photos.getUserPhotos', count=100, **owner)
        for photo in response[1:]:
            p = Photo(photo)
            path = os.path.join(destination, str(p.aid), str(p.pid)) +\
                    os.path.splitext(p.url)[-1]
            task = DownloadTask(p.url, path)
            self.tasks.put(task)
        number = response[0]
        for offset in range(100, number, 100):
            photos = self.api.request('photos.getUserPhotos', offset=offset,
                                      count=100, **owner)[1:]
            for photo in photos:
                p = Photo(photo)
                path = os.path.join(destination, str(p.aid), str(p.pid)) +\
                        os.path.splitext(p.url)[-1]
                task = DownloadTask(p.url, path)
                self.tasks.put(task)

    @parallelize
    def get_audios(self, destination, user_id=None, group_id=None):
        owner = {}
        if user_id:
            owner['uid'] = user_id
        elif group_id:
            owner['gid'] = group_id
        tracks = self.api.request('audio.get', **owner)
        for track in tracks:
            a = Audio(track)
            path = os.path.join(destination,
                                re.sub('[^\w\-_\. ]', '_', a.name)) +\
                                os.path.splitext(urlparse(a.url).path)[-1]
            task = DownloadTask(a.url, path)
            self.tasks.put(task)

    def get_friends_photos(self, destination, user_id=None):
        owner = {'uid': user_id} if user_id else {}
        friends = self.api.request('friends.get', **owner)
        for friend in friends:
            self.get_album_photos(os.path.join(destination, str(friend)),
                                  friend)

    def _parallel_download(self):
        def work(queue):
            while True:
                if queue.empty():
                    if self.all_fetched_event.is_set():
                        break
                    else:
                        time.sleep(0.001)
                try:
                    task = queue.get_nowait()
                except Exception:
                    continue
                if not os.path.exists(os.path.dirname(task.destination)):
                    os.makedirs(os.path.dirname(task.destination),
                                exist_ok=True)
                with open(task.destination, 'wb') as f:
                    f.write(self.__download(task.url))
                #print('done:', task.url)
        threads = [threading.Thread(target=work, args=(self.tasks,))
               for i in range(self.num_threads)]
        for thread in threads:
            thread.start()
        return threads
