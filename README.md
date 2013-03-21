vkdownloader
============

App for parallel downloading of photos, audios and other from vk.com


Getting started
----------

Install [vk package](https://github.com/Fatal1ty/vk) first.

[Get access token](https://vk.com/developers.php?id=-1_37230422&s=1) for necessary access rights:
* downloading album photos: photos
* downloading photos that a user has been tagged in: photos
* downloading friends photos (albums, profiles, walls, saved): friends,photos
* downloading audios: audio

Do some imports:

```
    from vk import api
    from core import Downloader
```

and create some instances:

```
    vk_api = api.API('PUT_YOUR_ACCESS_TOKEN_HERE')
    downloader = Downloader(vk_api)
```

### Downloading album photos (including profile, wall and saved photos):

```
    # photos from all albums of current user:
    downloader.get_album_photos(destination='my_albums')
    # photos from all albums of user with uid=1:
    downloader.get_album_photos(destination='user_albums', user_id=1)
    # profile photos and photos from album 159337866 of user with uid=1:
    downloader.get_album_photos(destination='two_albums', user_id=1,
                                album_ids=['profile', 159337866])
    # photos from all albums of group with id=22468706:
    downloader.get_album_photos(destination='group_albums', group_id=22468706)
```



### Downloading photos that a user has been tagged in:

```
    # photos that a current user has been tagged in:
    downloader.get_user_photos(destination='my_photos')
    # photos that a user with uid=1 has been tagged in:
    downloader.get_user_photos(destination='user_photos', user_id=1)
```

### Downloading friends albums photos:

```
    # photos from all albums of my friends:
    downloader.get_friends_photos(destination='my_friends_albums')
    # photos from all albums of friends of user with uid=1:
    downloader.get_friends_photos(destination='friends_albums', user_id=1)
```

### Downloading audios:

```
    # audios of current user:
    downloader.get_audios(destination='my_audios')
    # audios of user with uid=1
    downloader.get_audios(destination='user_audios', user_id=1)
```
