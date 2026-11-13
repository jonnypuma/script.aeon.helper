import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from resources.lib import chapthumbs  # noqa: E402


def test_parse_resolution():
    assert chapthumbs.parse_resolution('320 - 10x10 - 10000') == (320, 10, 10, 10000)
    assert chapthumbs.parse_resolution('320 - 10x10') == (320, 10, 10, 10000)
    assert chapthumbs.parse_resolution('480 - 5x5 - 5000') == (480, 5, 5, 5000)
    assert chapthumbs.parse_resolution('thumbs') is None
    assert chapthumbs.parse_resolution('0 - 10x10') is None


def test_choose_resolution_prefers_320_and_short_interval():
    names = ['640 - 10x10 - 10000', '320 - 10x10 - 10000', '320 - 10x10 - 5000', 'junk']
    assert chapthumbs.choose_resolution(names) == ('320 - 10x10 - 5000', (320, 10, 10, 5000))


def test_choose_resolution_falls_back():
    assert chapthumbs.choose_resolution(['480 - 10x10', '640 - 10x10'])[0] == '480 - 10x10'
    assert chapthumbs.choose_resolution(['160 - 10x10', '240 - 10x10'])[0] == '240 - 10x10'
    assert chapthumbs.choose_resolution(['nothing']) is None
    assert chapthumbs.choose_resolution([]) is None


def test_tile_order_is_numeric():
    assert chapthumbs.tile_order(['10.jpg', '2.jpg', '0.jpg', '1.jpg', 'x.png', 'notes.txt']) == ['0.jpg', '1.jpg', '2.jpg', '10.jpg']


def test_cell():
    # 10 s per thumb, 10 x 10 per sheet: 104 s is thumb 10 = sheet 0, column 0, row 1
    assert chapthumbs.cell(104, 10000, 10, 10, 4) == (0, 0, 1)
    assert chapthumbs.cell(0, 10000, 10, 10, 4) == (0, 0, 0)
    # 2905 s = thumb 290 = sheet 2, position 90 = column 0, row 9
    assert chapthumbs.cell(2905, 10000, 10, 10, 4) == (2, 0, 9)
    assert chapthumbs.cell(1023.5, 10000, 10, 10, 4) == (1, 2, 0)
    # past the last sheet: its last cell
    assert chapthumbs.cell(99999, 10000, 10, 10, 4) == (3, 9, 9)
    assert chapthumbs.cell(-5, 10000, 10, 10, 4) == (0, 0, 0)
    assert chapthumbs.cell(10, 10000, 10, 10, 0) is None


def test_sidecar_root():
    nfs = 'nfs://192.168.0.3/Media/TV/Westworld/Season 1/Westworld.S01E05.mkv'
    assert chapthumbs.sidecar_root(nfs) == 'nfs://192.168.0.3/Media/TV/Westworld/Season 1/Westworld.S01E05.trickplay'
    assert chapthumbs.sidecar_root(r'X:\TV\Show\Season.1\ep.mkv') == r'X:\TV\Show\Season.1\ep.trickplay'
    assert chapthumbs.sidecar_root('/media/Season.1/episode') == '/media/Season.1/episode.trickplay'
    assert chapthumbs.sidecar_root('plugin://plugin.video.x/?id=1') is None
    assert chapthumbs.sidecar_root('') is None


def test_file_key():
    assert chapthumbs.file_key('104.000000') == '104.000000'
    assert chapthumbs.file_key('1,5') == '15'
    assert chapthumbs.file_key('') == ''


def test_chapter_starts():
    # Westworld S01E05 on the box: 8 chapters, 3393 s
    label = ('0.00000,3.06517,3.06517,20.98463,20.98463,30.15067,30.15067,47.24488,47.24488,65.31171,65.31171,'
             '85.61845,85.61845,97.93808')
    starts = [round(s) for s in chapthumbs.chapter_starts(label, 8, 3393)]
    assert starts == [0, 104, 712, 1023, 1603, 2216, 2905, 3323]
    assert chapthumbs.chapter_starts('', 0, 100) == []
    assert len(chapthumbs.chapter_starts(label, 3, 3393)) == 3
