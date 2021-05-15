import sys, os
import subprocess
import codecs
import glob
import re

class HLS:
    def __init__(self, path):
        self.path = path.replace(os.sep, '/')
        self.path_separater = "\\"
        self.hls_path = self._get_hls_path()

    def get_filename(self, filename):
        m = re.match(r"(?P<filename>.*)\.(?P<extension>[a-zA-Z0-9_]+)", filename)
        if m:
            return m.group('filename'), m.group('extension')

    def _get_hls_path(self):
        l = self.path.split("/")
        filename, _ = self.get_filename(l[-1])
        l.pop(-1)
        return f"{'/'.join(l)}/hls/{filename}"

    def _create_high_resolution_m3u8(self, segment_time=2):
        l = self.path.split("/")
        filename, _ = self.get_filename(l[-1])
        l.pop(-1)
        os.makedirs(f"{self.hls_path}/h", exist_ok=True)

        c = "ffmpeg"
        c += f" -i {self.path}"
        c += " -codec copy -vbsf h264_mp4toannexb -map 0"
        c += f" -f segment -segment_format mpegts -segment_time {segment_time}"
        c += f" -segment_list {self.hls_path}/h/{filename}_h.m3u8"
        c += f" {self.hls_path}/h/{filename}_h_%5d.ts"

        code = subprocess.call(c.split())
        # print('process=' + str(code))

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
        # print('process=' + str(code))

    def _create_low_resolution_m3u8(self, segment_time=2):
        l = self.path.split("/")
        filename, extention = self.get_filename(l[-1])
        l.pop(-1)
        os.makedirs(f"{self.hls_path}/l", exist_ok=True)

        c = 'ffmpeg'
        c += f' -i {"/".join(l)}/{filename}_low.{extention}'
        c += ' -codec copy -vbsf h264_mp4toannexb -map 0'
        c += f' -f segment -segment_format mpegts -segment_time {segment_time}'
        c += f' -segment_list {self.hls_path}/l/{filename}_l.m3u8'
        c += f' {self.hls_path}/l/{filename}_l_%5d.ts'

        code = subprocess.call(c.split())
        # print('process=' + str(code))

        os.remove(f'{"/".join(l)}/{filename}_low.{extention}')

    def create_hls_high(self):
        self._create_high_resolution_m3u8(segment_time=5)

        l = self.path.split("/")
        filename, _ = self.get_filename(l[-1])
        l.pop(-1)
        os.makedirs(self.hls_path, exist_ok=True)

        t = '#EXTM3U'
        t += '\n##EXT-X-VERSION:3'
        t += '\n#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=4000000'
        t += f'\nh/{filename}_h.m3u8'

        f = codecs.open(f'{self.hls_path}/{filename}_playlist.m3u8', 'w', 'utf-8')
        f.write(t)
        f.close()

    def create_hls(self):
        self._create_high_resolution_m3u8()
        self._create_low_resolution_mp4()
        self._create_low_resolution_m3u8()

        l = self.path.split("/")
        filename, _ = self.get_filename(l[-1])
        l.pop(-1)
        os.makedirs(self.hls_path, exist_ok=True)

        t = '#EXTM3U'
        t += '\n##EXT-X-VERSION:3'
        t += '\n#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=500000'
        t += f'\nl/{filename}_l.m3u8'
        t += '\n#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=4000000'
        t += f'\nh/{filename}_h.m3u8'

        f = codecs.open(f'{self.hls_path}/{filename}_playlist.m3u8', 'w', 'utf-8')
        f.write(t)
        f.close()


if __name__ == "__main__":
    path = sys.argv[1]
    files = glob.glob(f"{path}/**/*.mp4", recursive=True)
    print(f"Number of Files: {len(files)}")

    for file in files:
        print(f"File Path: {file}")
        try:
            hls = HLS(file)
            hls.create_hls_high()
        except Exception as e:
            print(e)
    
    # run server(localhost:3000)
    subprocess.call(f"python -m http.server 3000 --directory {path}/hls")