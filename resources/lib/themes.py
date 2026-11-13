"""Theme songs: a theme.mp3 (or .flac/.ogg/.wav/.m4a/.wma) in a movie or TV show folder plays while the item is selected."""
THEME_NAMES = ('theme.mp3', 'theme.flac', 'theme.ogg', 'theme.m4a', 'theme.wav', 'theme.wma')
BS = chr(92)
SKIP_PREFIXES = ('videodb://', 'plugin://', 'addons://', 'library://', 'special://')


def folder_of(path):
    """The real folder of a library item's Path, or '' when it has none (virtual paths, empty)."""
    path = (path or '').strip()
    if path.startswith('stack://'):
        path = path[len('stack://'):].split(' , ')[0]
        cut = max(path.rfind('/'), path.rfind(BS))
        path = path[:cut + 1] if cut >= 0 else ''
    if not path or path.startswith(SKIP_PREFIXES):
        return ''
    if not path.endswith(('/', BS)):
        path += BS if (BS in path and '/' not in path) else '/'
    return path


def find_theme(path, exists):
    """First theme file in the folder, or ''."""
    folder = folder_of(path)
    if not folder:
        return ''
    for name in THEME_NAMES:
        if exists(folder + name):
            return folder + name
    return ''
