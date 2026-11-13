# -*- coding: utf-8 -*-
"""Live TV lists for Home: last played channels and the channels of a group. No Kodi imports."""


def last_played(channels, limit=20):
    """Channels that have been watched, most recent first. channels: PVR.GetChannels entries with 'lastplayed'
    ('' or a 1970 date = never)."""
    seen = [channel for channel in channels or () if (channel.get('lastplayed') or '') > '1971']
    seen.sort(key=lambda channel: channel['lastplayed'], reverse=True)
    return seen[:limit] if limit else seen


def progress(broadcast):
    """How far the running programme is, 0-100 ('' when unknown)."""
    value = (broadcast or {}).get('progresspercentage')
    try:
        return str(int(round(float(value))))
    except (TypeError, ValueError):
        return ''


def describe(channel):
    """What the skin shows for one channel: {'label', 'now', 'next', 'progress', 'icon', 'channelid', 'number'}."""
    now = channel.get('broadcastnow') or {}
    nxt = channel.get('broadcastnext') or {}
    return {'label': channel.get('label') or channel.get('channel') or '', 'now': now.get('title') or '', 'next': nxt.get('title') or '',
            'plot': now.get('plot') or now.get('plotoutline') or '', 'progress': progress(now),
            'icon': channel.get('icon') or channel.get('thumbnail') or '', 'channelid': channel.get('channelid'),
            'number': str(channel.get('channelnumber') or '')}
