# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from resources.lib import mediainfo as mi

# the user's examples (2026-11-17), shortened to the fields that matter
TMM = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<!--created on 2026-03-14 09:43:55 - tinyMediaManager 5.2.8-->
<MediaInfo xmlns="https://mediaarea.net/mediainfo" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="2.0">
  <creatingLibrary url="https://www.tinymediamanager.org" version="5.2.8">tinyMediaManager</creatingLibrary>
  <media ref="/EC2480/Media/Movies/get.hard.2015.unrated.1080p.bluray.x264-sparks/Get.Hard.2015.THEATRICAL.2160p.MA.WEB-DL.DTS-HD.MA.5.1.DV.HDR.H.265-FLUX.mkv">
    <track type="General">
      <FileName>Get.Hard.2015.THEATRICAL.2160p.MA.WEB-DL.DTS-HD.MA.5.1.DV.HDR.H.265-FLUX</FileName>
      <Format>Matroska</Format>
      <FileSize>21150146986</FileSize>
      <Duration>6017.022</Duration>
      <OverallBitRate>28120418</OverallBitRate>
    </track>
    <track type="Video">
      <Format>HEVC</Format>
      <Format_Profile>Main 10@L5@High</Format_Profile>
      <HDR_Format>Dolby Vision / SMPTE ST 2086</HDR_Format>
      <HDR_Format_Commercial>HDR10 / HDR10</HDR_Format_Commercial>
      <Width>3840</Width>
      <Height>2160</Height>
      <FrameRate>23.976</FrameRate>
      <BitDepth>10</BitDepth>
      <transfer_characteristics>PQ</transfer_characteristics>
    </track>
    <track type="Audio">
      <Format>DTS</Format>
      <Format_Commercial_IfAny>DTS-HD Master Audio</Format_Commercial_IfAny>
      <Format_AdditionalFeatures>XLL</Format_AdditionalFeatures>
      <Channels>6</Channels>
      <Language>en-US</Language>
      <Language_String3>eng</Language_String3>
      <Default>Yes</Default>
    </track>
    <track type="Text" typeorder="1"><Format>UTF-8</Format><Language>en</Language><Language_String3>eng</Language_String3><Default>No</Default><Forced>No</Forced></track>
    <track type="Text" typeorder="2"><Format>UTF-8</Format><Title>SDH</Title><Language>en</Language><Language_String3>eng</Language_String3><Default>No</Default><Forced>No</Forced></track>
    <track type="Menu">
      <Chapters_Pos_Begin>101</Chapters_Pos_Begin>
      <Chapters_Pos_End>112</Chapters_Pos_End>
      <_00_00_00_083>en:Chapter 01</_00_00_00_083>
    </track>
  </media>
</MediaInfo>'''

CMM = '''<?xml version="1.0" encoding="UTF-8"?>
<mediainfo version="1">
  <file>
    <name>Alien (1979) Theatrical Version UHD Blu-ray Remux 2160p HEVC HDR10+ DTS-HD MA 5.1.mkv</name>
    <size>50513653711</size>
    <container>MKV</container>
    <duration_seconds>6997</duration_seconds>
    <bitrate_mbps>57.75</bitrate_mbps>
    <video_codec>HEVC</video_codec>
    <video_profile>Main 10</video_profile>
    <width>3840</width>
    <height>2160</height>
    <resolution>4K</resolution>
    <fps>23.976</fps>
    <aspect_ratio>1.78</aspect_ratio>
    <bit_depth>10</bit_depth>
    <hdr_format>hdr10</hdr_format>
    <is_hybrid>false</is_hybrid>
    <is_3d>false</is_3d>
    <video_source>UHD Bluray</video_source>
    <source_format>UHD Remux</source_format>
    <edition>Theatrical Cut</edition>
    <chapters>32</chapters>
  </file>
  <audio_tracks>
    <track><codec>DTS-HD MA</codec><lang>eng</lang><channels>5.1</channels><default>true</default><title>DTS-HD MA 5.1</title></track>
    <track><codec>DTS-HD MA</codec><lang>eng</lang><channels>5</channels><default>false</default><title>DTS-HD MA 4.1 (Original Theatrical Audio)</title></track>
    <track><codec>ac3</codec><lang>eng</lang><channels>2.0</channels><default>false</default><title>Commentary from 1999 by Ridley Scott</title><bitrate_kbps>224</bitrate_kbps></track>
  </audio_tracks>
  <subtitle_tracks>
    <track><lang>eng</lang><codec>hdmv_pgs_subtitle</codec><flags>sdh</flags><default>false</default><title>English SDH</title></track>
    <track><lang>spa</lang><codec>hdmv_pgs_subtitle</codec><default>false</default></track>
    <track><lang>fra</lang><codec>hdmv_pgs_subtitle</codec><default>false</default></track>
    <track><lang>spa</lang><codec>hdmv_pgs_subtitle</codec><default>false</default></track>
  </subtitle_tracks>
  <external_subtitles />
</mediainfo>'''

NAMES = {'eng': 'English', 'spa': 'Spanish', 'fra': 'French'}


class TestMediaInfo(unittest.TestCase):
    def test_side_paths(self):
        self.assertEqual(mi.side_paths('smb://nas/Movies/Alien (1979)/Alien (1979).mkv'),
                         [('cmm', 'smb://nas/Movies/Alien (1979)/Alien (1979).cmm_mediainfo.xml'),
                          ('tmm', 'smb://nas/Movies/Alien (1979)/Alien (1979)-mediainfo.xml')])
        self.assertEqual(mi.side_paths('D:\\Films\\Heat.mkv')[0], ('cmm', 'D:\\Films\\Heat.cmm_mediainfo.xml'))
        self.assertEqual(mi.side_paths('plugin://x/?a=1'), [])
        self.assertEqual(mi.side_paths(''), [])

    def test_guess_source(self):
        self.assertEqual(mi.guess_source('Get.Hard.2015.THEATRICAL.2160p.MA.WEB-DL.DTS-HD.MA.5.1-FLUX'), 'WEB-DL')
        self.assertEqual(mi.guess_source('Heat.1995.1080p.BluRay.x264-SPARKS'), 'Blu-ray')
        self.assertEqual(mi.guess_source('Heat.1995.2160p.UHD.BluRay.REMUX.HDR'), 'UHD Remux')
        self.assertEqual(mi.guess_source('Heat.1995.1080p.BluRay.REMUX.AVC'), 'Blu-ray Remux')
        self.assertEqual(mi.guess_source('Heat.1995.2160p.BluRay.x265', 2160), 'UHD Blu-ray')
        self.assertEqual(mi.guess_source('Heat.1995.DVDRip.XviD'), 'DVD')
        self.assertEqual(mi.guess_source('Show.S01E01.720p.HDTV.x264'), 'HDTV')
        self.assertEqual(mi.guess_source('Show.S01E01.1080p.WEBRip.x264'), 'WEBRip')
        self.assertEqual(mi.guess_source('Heat (1995)'), '')
        self.assertEqual(mi.guess_edition('Get.Hard.2015.THEATRICAL.2160p'), 'Theatrical')
        self.assertEqual(mi.guess_edition("Blade Runner (1982) Director's Cut"), "Director's Cut")

    def test_tmm(self):
        info = mi.parse('tmm', TMM)
        self.assertEqual(info['from'], mi.TMM)
        self.assertEqual(info['source'], 'WEB-DL')
        self.assertEqual(info['edition'], 'Theatrical')
        self.assertEqual(info['container'], 'MKV')
        self.assertEqual(info['hdr'], 'Dolby Vision')
        self.assertTrue(info['hybrid'])
        self.assertEqual(info['chapters'], 11)
        self.assertEqual(info['audio'][0]['codec'], 'DTS-HD MA')
        self.assertEqual(info['audio'][0]['channels'], '5.1')
        p = mi.props(info, lambda c: NAMES.get(c, c))
        self.assertEqual(p['res'], '4K')
        self.assertEqual(p['hdr'], 'Dolby Vision + HDR10')
        self.assertEqual(p['video'], 'HEVC \u00b7 Main 10 \u00b7 10-bit \u00b7 23.976 fps')
        self.assertEqual(p['audio'], 'DTS-HD MA 5.1 (English)')
        self.assertEqual(p['subs.count'], '2')
        self.assertEqual(p['subs.langs'], 'English')
        self.assertEqual(p['sdh'], 'SDH')
        self.assertEqual(p['bitrate'], '28.1 Mb/s')
        self.assertEqual(p['size'], '21.2 GB')
        self.assertEqual(p['chapters'], '11')
        self.assertEqual(p['format'], 'WEB-DL')             # 0.3.102: guessed from the name
        self.assertEqual(p['vsource'], '')                  # tinyMediaManager writes no video source
        self.assertEqual(p['vcodec'], 'HEVC')
        self.assertEqual(mi.parse('cmm', TMM), None)        # not Curator's file

    def test_cmm(self):
        info = mi.parse('cmm', CMM)
        self.assertEqual(info['from'], mi.CURATOR)
        self.assertEqual(info['source'], 'UHD Remux')
        self.assertEqual(info['edition'], 'Theatrical Cut')
        self.assertEqual(info['hdr'], 'HDR10')
        p = mi.props(info, lambda c: NAMES.get(c, c))
        self.assertEqual(p['source'], 'UHD Remux')
        self.assertEqual(p['format'], 'UHD Remux')          # 0.3.102: <source_format>
        self.assertEqual(p['vsource'], 'UHD Bluray')        # <video_source>
        self.assertEqual(p['vcodec'], 'HEVC')               # <video_codec>
        self.assertEqual(p['edition'], 'Theatrical Cut')    # <edition>
        self.assertEqual(p['res'], '4K')
        self.assertEqual(p['audio'], 'DTS-HD MA 5.1 (English)')
        self.assertEqual(p['audio.count'], '3')
        self.assertEqual(p['commentary'], '1')
        self.assertIn('Commentary from 1999 by Ridley Scott', p['audio.list'])
        self.assertIn('DTS-HD MA 5 (English) \u00b7 DTS-HD MA 4.1 (Original Theatrical Audio)', p['audio.list'])
        self.assertEqual(p['subs.count'], '4')
        self.assertEqual(p['subs.langs'], 'English, Spanish, French')
        self.assertEqual(p['sdh'], 'SDH')
        self.assertEqual(p['chapters'], '32')
        self.assertEqual(p['bitrate'], '57.8 Mb/s')
        self.assertEqual(p['size'], '50.5 GB')

    def test_bad(self):
        self.assertIsNone(mi.parse('cmm', ''))
        self.assertIsNone(mi.parse('cmm', '<not xml'))
        self.assertEqual(mi.props(None), {})



class ContainerNameTest(unittest.TestCase):
    def test_container_names(self):
        self.assertEqual(mi.container_name('Matroska'), 'MKV')
        self.assertEqual(mi.container_name('MPEG-4'), 'MP4')
        self.assertEqual(mi.container_name('mkv'), 'MKV')
        self.assertEqual(mi.container_name('Something'), 'SOMETHING')
        self.assertEqual(mi.container_name(''), '')

if __name__ == '__main__':
    unittest.main()
