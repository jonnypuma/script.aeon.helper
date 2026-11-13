# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from resources.lib import dvprofile


class TestDvProfile(unittest.TestCase):
    def test_label(self):
        self.assertEqual(dvprofile.label('<video><hdrtype>dolbyvision</hdrtype><hdrdetail>7FEL</hdrdetail></video>'), 'P7 FEL')
        self.assertEqual(dvprofile.label('<hdrdetail> 7mel </hdrdetail>'), 'P7 MEL')
        self.assertEqual(dvprofile.label('<hdrdetail>8.1</hdrdetail>'), 'P8.1')
        self.assertEqual(dvprofile.label('<hdrdetail>5</hdrdetail>'), 'P5')
        self.assertEqual(dvprofile.label('<hdrdetail>8.4</hdrdetail>'), 'P8.4')
        self.assertEqual(dvprofile.label('<hdrdetail>HDR10</hdrdetail>'), '')
        self.assertEqual(dvprofile.label(''), '')
        self.assertEqual(dvprofile.label(None), '')

    def test_label_cmm(self):
        cmm = '<video_profile>Main 10</video_profile><hdr_format>dovi</hdr_format><dovi_profile>7</dovi_profile><dovi_el_type>FEL</dovi_el_type>'
        self.assertEqual(dvprofile.label_cmm(cmm), 'P7 FEL')
        self.assertEqual(dvprofile.label_cmm('<dovi_profile> 7 </dovi_profile><dovi_el_type>mel</dovi_el_type>'), 'P7 MEL')
        # what the box's files hold (scan of 150 Dolby Vision films, 2026-11-13)
        self.assertEqual(dvprofile.label_cmm('<dovi_profile>8.1</dovi_profile><dovi_bl_compat>1</dovi_bl_compat>'), 'P8.1')
        self.assertEqual(dvprofile.label_cmm('<dovi_profile>5</dovi_profile><dovi_bl_compat>0</dovi_bl_compat>'), 'P5')
        self.assertEqual(dvprofile.label_cmm('<dovi_profile>8</dovi_profile><dovi_bl_compat>4</dovi_bl_compat>'), 'P8.4')
        self.assertEqual(dvprofile.label_cmm('<dovi_profile>7</dovi_profile><dovi_el_type>MEL</dovi_el_type><dovi_bl_compat>6</dovi_bl_compat>'), 'P7 MEL')
        self.assertEqual(dvprofile.label_cmm('<dovi_profile>7</dovi_profile>'), 'P7')
        self.assertEqual(dvprofile.label_cmm('<hdr_format>sdr</hdr_format>'), '')
        self.assertEqual(dvprofile.label_cmm(None), '')

    def test_side_paths(self):
        # the film that showed no chip: its .nfo lost <hdrdetail>, its .cmm_mediainfo.xml says 7 FEL
        path = 'nfs://192.168.0.3/Media/Movies/10 Cloverfield Lane (2016)/10.Cloverfield.Lane.REMUX-FraMeSToR.mkv-xpost.mkv'
        folder = 'nfs://192.168.0.3/Media/Movies/10 Cloverfield Lane (2016)/'
        self.assertEqual(dvprofile.side_paths(path), [
            ('nfo', folder + '10.Cloverfield.Lane.REMUX-FraMeSToR.mkv-xpost.nfo'),
            ('nfo', folder + 'movie.nfo'),
            ('cmm', folder + '10.Cloverfield.Lane.REMUX-FraMeSToR.mkv-xpost.cmm_mediainfo.xml')])
        self.assertEqual(dvprofile.side_paths('plugin://x/?a=1'), [])

    def test_nfo_paths(self):
        self.assertEqual(dvprofile.nfo_paths('nfs://host/Movies/A (2001)/A.2001.mkv'),
                         ['nfs://host/Movies/A (2001)/A.2001.nfo', 'nfs://host/Movies/A (2001)/movie.nfo'])
        self.assertEqual(dvprofile.nfo_paths('C:\\Films\\B.mkv'), ['C:\\Films\\B.nfo', 'C:\\Films\\movie.nfo'])
        self.assertEqual(dvprofile.nfo_paths('plugin://x/?a=1'), [])
        self.assertEqual(dvprofile.nfo_paths(''), [])


if __name__ == '__main__':
    unittest.main()
