import sys, os
import subprocess
import codecs
import re

class HLS:
    def __init__(self, path):
        self.path = path

    def get_filename(self, filename):
        m = re.match(r"(?P<filename>[a-zA-Z0-9_]+)\.(?P<extension>[a-zA-Z0-9_]+)", filename)
        if m:
            return m.group('filename'), m.group('extension')


    def _create_high_resolution_m3u8(self, segment_time=2):
        l = self.path.split("/")
        filename, _ = self.get_filename(l[-1])
        l.pop(-1)
        m3u8_path = f"{'/'.join(l)}/{filename}"
        os.makedirs(f"{m3u8_path}/h", exist_ok=True)

        c = "ffmpeg"
        c += f" -i {self.path}"
        c += " -codec copy -vbsf h264_mp4toannexb -map 0"
        c += f" -f segment -segment_format mpegts -segment_time {segment_time}"
        c += f" -segment_list {m3u8_path}/h/{filename}_h.m3u8"
        c += f" {m3u8_path}/h/{filename}_h_%5d.ts"

        code = subprocess.call(c.split())
        print('process=' + str(code))

    def _create_low_resolution_mp4(self):
        l = self.path.split("/")
        filename, extention = self.get_filename(l[-1])
        l.pop(-1)

        c = 'ffmpeg'
        c += f' -i {self.path}'
        c += ' -f mp4 -vcodec h264 -vb 500k -s 640x360 -pix_fmt yuv420p'
        c += ' -ac 2 -ar 48000 -ab 128k -acodec aac -strict experimental'
        c += ' -movflags faststart'
        c += f' {"/".join(l)}/{filename}_low.{extention}'

        code = subprocess.call(c.split())
        print('process=' + str(code))

    def _create_low_resolution_m3u8(self, segment_time=2):
        l = self.path.split("/")
        filename, extention = self.get_filename(l[-1])
        l.pop(-1)
        m3u8_path = f"{'/'.join(l)}/{filename}"
        os.makedirs(f"{m3u8_path}/l", exist_ok=True)

        c = 'ffmpeg'
        c += f' -i {"/".join(l)}/{filename}_low.{extention}'
        c += ' -codec copy -vbsf h264_mp4toannexb -map 0'
        c += f' -f segment -segment_format mpegts -segment_time {segment_time}'
        c += f' -segment_list {m3u8_path}/l/{filename}_l.m3u8'
        c += f' {m3u8_path}/l/{filename}_l_%5d.ts'

        code = subprocess.call(c.split())
        print('process=' + str(code))

        os.remove(f'{"/".join(l)}/{filename}_low.{extention}')

    def create_hls_high(self):
        self._create_high_resolution_m3u8()

        l = self.path.split("/")
        filename, _ = self.get_filename(l[-1])
        l.pop(-1)
        m3u8_path = f"{'/'.join(l)}/{filename}"
        os.makedirs(m3u8_path, exist_ok=True)

        t = '#EXTM3U'
        t += '\n##EXT-X-VERSION:3'
        t += '\n#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=4000000'
        t += f'\nh/{filename}_h.m3u8'

        f = codecs.open(f'{m3u8_path}/{filename}_playlist.m3u8', 'w', 'utf-8')
        f.write(t)
        f.close()

    def create_hls(self):
        self._create_high_resolution_m3u8()
        self._create_low_resolution_mp4()
        self._create_low_resolution_m3u8()

        l = self.path.split("/")
        filename, _ = self.get_filename(l[-1])
        l.pop(-1)
        m3u8_path = f"{'/'.join(l)}/{filename}"
        os.makedirs(m3u8_path, exist_ok=True)

        t = '#EXTM3U'
        t += '\n##EXT-X-VERSION:3'
        t += '\n#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=500000'
        t += f'\nl/{filename}_l.m3u8'
        t += '\n#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=4000000'
        t += f'\nh/{filename}_h.m3u8'

        f = codecs.open(f'{m3u8_path}/{filename}_playlist.m3u8', 'w', 'utf-8')
        f.write(t)
        f.close()


if __name__ == "__main__":
    path = sys.argv[1]

    hls = HLS(path)
    hls.create_hls_high()