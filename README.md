# MP4 から HLS(ts + m3u8)への変換

`pipenv run start <filepath>`

を実行することで該当ディレクトリ配下のmp4をすべてHLS形式に変換し、`hls/`に出力する。変換終了後、自動的に該当ディレクトリの`localhost:3000`でサーバーが起動し、m3u8が再生できる環境であれば再生が可能となる。

※`<filepath>`は絶対パスで指定すること

<br>

`pipenv run server <filepath>`

を実行することで該当ディレクトリの`localhost:3000`でサーバーが起動する。