# HLS Encoder that uses ffmpeg , Bento4 mp4-hls and mediainfo in the background and optionally uploads results into an s3 folder using the aws sdk


## Before running the script:
1. ffmpeg, mediainfo and python3 must be installed.
2. Create a virtual enviroment if python2 is installed on your machine instead of python3. Install python3 inside the virtual enviroment.
3. Move the mp4 files to be encoded into the same folder where the python script and the scripts folder is.
4. If subtitles are needed , move them into the same folder.
5. Subtitles must have the same name as the video file with the 2 letters iso code and also the subtitle language. Subtitles must be in srt format.
 ### Example:
    video_file: test.mp4
    subtitle_file_english: test_en.srt (english_version)
    subtitle_file_spanish: test_es.srt (spanish_version)
6. If you want to upload the output folder into an s3 bucket you must install the aws sdk on your computer. The upload is done with "aws sync" command.
7. Replace this variable at the top of the script with your own s3 bucket name:
    
    `s3_destination_bucket = '<YOUR_S3_BUCKET>'`

8. You can fine tune the encoder settings with your choosen bitrates on the PROFILE STREAM dict inside the script.
Currently the ffmpeg command is a one pass encoding.

9. You will need to create a mezzanine file in order to have a compilant input with the encoder. If you have the audio files for other languages in separated mono files, this is the ffmpeg command I use for adding them in a single mezzanine mp4 file:

```shell
ffmpeg  -i <video file>   -i <spanish language L track wav file>  -i <spanish language R track wav file>  -i <italian language L track wav file>  -i <italian language R track wav file>  -i <italian language L track wav file>  -i <catalan language L track wav file> -i <catalan language R track wav file>   -map 0:v -c:v copy  -filter_complex "[1:0][2:0]amerge=inputs=2[a1]; [3:0][4:0]amerge=inputs=2[a2]; [5:0][6:0]amerge=inputs=2[a3]" -map "[a1]" -map "[a2]" -map "[a3]"  -metadata:s:a:0 language=spa -metadata:s:a:1 language=cat -metadata:s:a:2 language=ita  /<output_folder>/<output_file>.mp4 

```
As you can see here ` -metadata:s:a:0 language=spa ` the command is using a 3 letter code iso for adding the language metadata. This is a must if you want to show the language on the video player. 

## Usage:

### Encode files whitout upload:
`python hls_encoder.py`
### Encode files and upload them into your s3 bucket:
`python hls_encoder.py sync_bucket`

The result will be an "output" folder with 5 -or less depending on the input video resolution- different chunked variants and the master playlist (master.m3u8).  If the video file have more than one language inside, these tracks will appear in the output folder too. Keep in mind that the language metadata must be set beforehand in order to show the language on the player as it's shown in the above ffmpeg command.
All the chunks are **encrypted** using the **aes-128 encryption**. Output video files won't be inflated. This means only the same resolution and lower ones will be done. Never a resolution higher than the original one.