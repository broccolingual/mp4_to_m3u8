import sys, os
import subprocess
import codecs
import glob
import re
import time

class HLS:
    def __init__(self, path):
        self.path = path
        self.root = os.path.dirname(self.path)
        self.hls_path = self._get_hls_path()

    def get_filename(self):
        root, ext = os.path.splitext(os.path.basename(self.path))
        return root, ext

    def _get_hls_path(self):
        return os.path.join(self.root, 'hls', self.get_filename()[0])

    def _create_thumbnail(self):
        os.makedirs(self.hls_path, exist_ok=True)

        c = 'ffmpeg'
        c += f' -i {self.path}'
        c += f' -vf thumbnail -frames:v 1'
        c += f' {os.path.join(self.hls_path, "thumb.jpg")}'

        subprocess.call(c.split())

    def _create_high_resolution_m3u8(self, segment_time=2):
        filename, ext = self.get_filename()

        if ext != ".mp4":
            return

        os.makedirs(f"{self.hls_path}/h", exist_ok=True)

        c = "ffmpeg"
        c += f" -i {self.path}"
        c += " -codec copy -vbsf h264_mp4toannexb -map 0"
        c += f" -f segment -segment_format mpegts -segment_time {segment_time}"
        c += f" -segment_list {self.hls_path}/h/{filename}_h.m3u8"
        c += f" {self.hls_path}/h/{filename}_h_%5d.ts"

        subprocess.call(c.split())

    def _create_low_resolution_mp4(self):
        filename, ext = self.get_filename()

        c = 'ffmpeg'
        c += f' -i {self.path}'
        c += ' -f mp4 -vcodec h264 -vb 500k -s 640x360 -pix_fmt yuv420p'
        c += ' -ac 2 -ar 48000 -ab 128k -acodec aac -strict experimental'
        c += ' -movflags faststart'
        c += f' {self.root}/{filename}_low.{ext}'

        subprocess.call(c.split())

    def _create_low_resolution_m3u8(self, segment_time=2):
        filename, ext = self.get_filename()
        os.makedirs(f"{self.hls_path}/l", exist_ok=True)

        c = 'ffmpeg'
        c += f' -i {self.root}/{filename}_low.{ext}'
        c += ' -codec copy -vbsf h264_mp4toannexb -map 0'
        c += f' -f segment -segment_format mpegts -segment_time {segment_time}'
        c += f' -segment_list {self.hls_path}/l/{filename}_l.m3u8'
        c += f' {self.hls_path}/l/{filename}_l_%5d.ts'

        subprocess.call(c.split())

        os.remove(f'{self.root}/{filename}_low.{ext}')

    def create_hls_high(self):
        self._create_thumbnail()
        self._create_high_resolution_m3u8(segment_time=5)

        filename, ext = self.get_filename()
        os.makedirs(self.hls_path, exist_ok=True)

        t = '#EXTM3U'
        t += '\n##EXT-X-VERSION:3'
        t += '\n#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=4000000'
        t += f'\nh/{filename}_h.m3u8'

        f = codecs.open(f'{self.hls_path}/playlist.m3u8', 'w', 'utf-8')
        f.write(t)
        f.close()

    def create_hls(self):
        self._create_thumbnail()
        self._create_high_resolution_m3u8()
        self._create_low_resolution_mp4()
        self._create_low_resolution_m3u8()

        filename, ext = self.get_filename()
        os.makedirs(self.hls_path, exist_ok=True)

        t = '#EXTM3U'
        t += '\n##EXT-X-VERSION:3'
        t += '\n#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=500000'
        t += f'\nl/{filename}_l.m3u8'
        t += '\n#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=4000000'
        t += f'\nh/{filename}_h.m3u8'

        f = codecs.open(f'{self.hls_path}/playlist.m3u8', 'w', 'utf-8')
        f.write(t)
        f.close()


if __name__ == "__main__":
    path = sys.argv[1]
    print(path)

    files = glob.glob(f"{path}/**/*.mp4", recursive=True)
    print(f"Number of Files: {len(files)}")

    start = time.time()
    for file in files:
        print(f"File Path: {file}")
        try:
            hls = HLS(file)
            hls.create_hls_high()
        except Exception as e:
            print(e)
    end = time.time()
    elapsed_time = end-start
    print(f"Elapsed Time: {elapsed_time}[sec]")
    
    # run server(localhost:3000)
    try:
        subprocess.call(f"python -m http.server 3000 --directory {path}/hls")
    except KeyboardInterrupt:
        pass