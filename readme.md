# HLS Encoder

A robust HLS encoder that utilizes **FFmpeg**, **Bento4 mp4-hls**, and **MediaInfo** to convert videos into encrypted HLS streams. It also optionally uploads the resulting streams to an Amazon S3 bucket.

## Features

- Encodes video files to encrypted HLS format (AES-128 encryption).
- Uses realistic bitrates without inflating the original video resolution.
- Optional automatic upload to an Amazon S3 bucket.

## Prerequisites

- **FFmpeg**, **Bento4 mp4-hls**, and **MediaInfo** must be installed on your system.
- If uploading to S3, the AWS CLI must also be installed and configured.

## Setup Instructions

1. Clone this repository.
2. Place video files to be encoded in the same directory as the Python script and `scripts` folder.
3. (Optional) If subtitles are needed, place them in the same directory. Subtitles must:
   - Be in `.srt` format.
   - Share the video filename followed by a two-letter ISO language code (e.g., `video_en.srt`).

3. To upload results to S3, update the following variable in the script:

```python
s3_destination_bucket = '<YOUR_S3_BUCKET>'
```

## Creating a Mezzanine File (with multiple audio tracks)

If your input video has multiple audio tracks in separate WAV files, use the following command to merge them into a mezzanine MP4 file:

```shell
ffmpeg -i <video file> \
       -i <spanish_L.wav> -i <spanish language R track wav file> \
       -i <italian language L track wav file> -i <italian language R track wav file> \
       -i <additional language L track wav file> -i <additional language R track wav file> \
       -filter_complex "[1:0][2:0]amerge=inputs=2[a1]; [3:0][4:0]amerge=inputs=2[a2]; [5:0][6:0]amerge=inputs=2[a3]" \
       -map 0:v -map "[a1]" -map "[a2]" -map "[a3]" \
       output.mp4
```

**Important**: Ensure that audio language metadata is set correctly (use ISO 639-2 three-letter codes).

## Usage

### Encode without uploading:
```shell
python hls_encoder.py
```

### Encode and upload to S3

```shell
python hls_encoder.py sync
```

## Features

- AES-128 encryption for secure HLS streaming.
- Automatically generates video streams equal to or lower than the original resolution to avoid quality inflation.

---

For any contributions, improvements, or issues, please open a GitHub issue or submit a pull request.

