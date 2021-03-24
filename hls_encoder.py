# -*- coding=utf-8 -*-

import os
import subprocess
import sys
import string
import csv

cloudfront_domain = "dusqglx8g3hsd.cloudfront.net"
trailers_cloudfront_domain = 'd14q6vju7s12ir.cloudfront.net'
s3_destination_bucket = 'adso-vod-workflow-template-destination-d25pp6byo9pp'

PROFILE_STREAMS = (


    {
        'bitrate': '7800k',
        'bitrate_max': '7820k',
        'audio_bitrate': '128k',
        'buffer_size': '7800k',
        'resolution_16_9': '1920x1080',
        'resolution_4_3': '1440x1080',
        'profile': 'high -bsf:v h264_mp4toannexb -preset slow',
        'video_codec': 'libx264',
        'name_append': '_1080p'

    },
    {
        'bitrate': '4500k',
        'bitrate_max': '4510k',
        'audio_bitrate': '128k',
        'buffer_size': '4500k',
        'resolution_16_9': '1280x720',
        'resolution_4_3': '960x720',
        'profile': 'high -level:v 4.0 -preset slow',
        'video_codec': 'libx264',
        'name_append': '_720p'

    },
    {
        'bitrate': '2000k',
        'bitrate_max': '2240k',
        'audio_bitrate': '96k',
        'buffer_size': '2000k',
        'resolution_16_9': '1024x576',
        'resolution_4_3': '720x576',
        'profile': 'main -level:v 4.0 -preset slow',
        'video_codec': 'libx264',
        'name_append': '_576'
    },
    {
        'bitrate': '700k',
        'bitrate_max': '840k',
        'audio_bitrate': '64k',
        'buffer_size': '700k',
        'resolution_16_9': '640x360',
        'resolution_4_3': '512x384',
        'profile': 'main -level:v 4.0 -preset slow',
        'video_codec': 'libx264',
        'name_append': '_360'
    },
    {
        'bitrate': '365k',
        'bitrate_max': '400k',
        'audio_bitrate': '64k',
        'buffer_size': '365k',
        'resolution_16_9': '480x272',
        'resolution_4_3': '480x250',
        'profile': 'main -level:v 4.0 -preset slow',
        'video_codec': 'libx264',
        'name_append': '_272'
    }
)

variants = ['365k', '700k', '2000k', '4500k', '7800k']



def main():
    #below lines need to be fixed
    # with open('out_urls.csv', 'wb') as f:
    #     added_scenes = csv.writer(f)
    #     added_scenes.writerow(
    #         ['nombre', 'url_master.m3u8', 'duration'])

    for subdir, dirs, files in os.walk('./'):

        for file in files:

            filepath = subdir + os.sep + file

            if filepath.endswith(".mp4"):
                format_filename(file)
                hls_encode(file)


def format_filename(s):
    """
    Take a string and return a valid filename constructed from the string.
    Uses a whitelist approach: any characters not present in valid_chars are
    removed. Also spaces are replaced with underscores.

    Note: this method may produce invalid filenames such as ``, `.` or `..`
    When I use this method I prepend a date string like '2009_01_15_19_46_32_'
    and append a file extension like '.txt', so I avoid the potential of using
    an invalid filename.

    Instead of returning the filename is modified for renaming the file
    """
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    filename = ''.join(c for c in s if c in valid_chars)
    filename = filename.replace(' ', '_')
    os.rename(s, filename)


def hls_encode(file):
    base = os.path.basename(file)
    out_name = os.path.splitext(base)[0]
    directory = os.path.abspath(os.getcwd()) + '/' + out_name
    thumbs_out = os.path.join(directory, 'thumbnails')
    trailer_out = os.path.join('trailer')

    try:
        aspect_ratio = mediainfo_get_prop_value(
            file, 'Video', 'DisplayAspectRatio_Original/String')
        if not aspect_ratio:
            aspect_ratio = mediainfo_get_prop_value(
                file, "Video", "DisplayAspectRatio/String")
    except ValueError as e:
        raise ValueError(e)
    try:
        width = mediainfo_get_prop_value(file, "Video", "Width")

    except ValueError as e:
        raise ValueError(e)
    try:
        duration = mediainfo_get_prop_value(file, "Video", "Duration")

    except ValueError as e:
        raise ValueError(e)
    try:
        duration_TC = mediainfo_get_prop_value(
            file, "Video", "Duration/String3")

    except ValueError as e:
        raise ValueError(e)

    def thumbnails_time_divider(duration, jumps, jump_miliseconds):

        jump_size = int(duration)/jumps
        pointer = 0
        points = []

        for i in range(jumps):
            try:
                points.append(pointer)
                pointer += jump_size - jump_miliseconds
            except:
                pass
        return points

    def trailer_cmd(times, file, scene_duration):
        '''
        Returns this ffmpeg command that will create a mini trailer of the input video file
        # 'ffmpeg -i multi_audio_test_no_audio.mp4 -vf "select='between(t, 4, 6.5)+between(t, 17, 26)+between(t, 74, 91)', setpts=N/FRAME_RATE/TB" tes.mp4'
        The number of seconds of each scene can be changed in the
        '''
        cmd = 'ffmpeg -i {} -an '.format(file)
        cmd += "-vf "
        cmd += '"select='
        cmd += "'"
        counter = 0
        scene_number_of_seconds = scene_duration
        for time in times:
            if counter == 0:
                cmd += 'between(t,{},{})'.format(time/1000,
                                                 time/1000 + scene_number_of_seconds)
            else:
                cmd += '+between(t,{},{})'.format(time/1000,
                                                  time/1000 + scene_number_of_seconds)
            counter += 1
        cmd += "'"
        cmd += ', setpts=N/FRAME_RATE/TB" '
        cmd += "-s {} ".format("426x240")
        cmd += "{}/{}_trailer.mp4".format(trailer_out, out_name)
        return cmd

    def get_profile(variant, aspect_ratio, PROFILE_STREAMS):

        for profile in PROFILE_STREAMS:
            if aspect_ratio == '4:3':

                profile_resol = profile['resolution_4_3']  
                 
                profile_width = profile_resol.split("x")
                if int(width) >= int(profile_width[0]) and profile['bitrate'] == variant:
                    return profile

            else:
                profile_resol = profile['resolution_16_9']
                profile_width = profile_resol.split("x")

                if int(width) >= int(profile_width[0]) and profile['bitrate'] == variant:

                    return profile, profile_resol

    def create_command(directory, file, stream):
        """
        Creates the ffmpeg single pass commands to generate the variants before creating the .m3u8 master playlist.

        :param args:
        :param kwargs:
        :return: the cmd as string
        """
        output_name = out_name + stream[0]['name_append'] + '.mp4'
        output = os.path.join(directory, output_name)
        cmd = 'ffmpeg -y '
        cmd += '-i {} -c:v libx264 -profile:v {} -s {} '.format(
            file, stream[0]['profile'], stream[1])
        cmd += '-g 50 -keyint_min 50 -sc_threshold 0 -bf 3 -b_strategy 2 -refs 2 -coder 0 '
        cmd += '-b:v {} -maxrate {} -bufsize {} -pix_fmt yuv420p '.format(
            stream[0]['bitrate'], stream[0]['bitrate_max'], stream[0]['buffer_size'])
        cmd += '-c:a aac -b:a {}  -ar 44100 -movflags faststart  -map 0:v -map 0:a {}'.format(
            stream[0]['audio_bitrate'], output)

        return cmd

    def create_master_playlist():
        """
        Create the command to generate the master playlist (master.m3u8) for the profile.
        Run the 'mp4-hls.py' script
        :param args:
        :param kwargs:
        :return:
        """
        mezzanines = []

        for subdir, dirs, files in os.walk(directory):

            for file in files:
                filepath = subdir + os.sep + file
                if filepath.endswith(".mp4"):
                    if not filepath.endswith("trailer.mp4"):
                        mezza = ''.join(file)
                        mezzanines.append("'%s/%s' " % (directory, mezza))

        cmd = "python3 scripts/utils/mp4-hls.py -o '{outputs}' -f {mezzanines}".format(

            outputs=directory,
            mezzanines=''.join(mezzanines)
        )
        return cmd
    def aes_128_key():

            try:
                os.remove('enc.key')
            except OSError:
                print('KEY_ERROR:', OSError)
                pass
            cmd='openssl rand 16 > enc.key'
            return cmd
    def create_master_playlist_with_subtitles_and_encryption():
        
        """
        mp4-hls.py command with subtitles and encryption
        """
        mezzanines = []
        subtitles = []
        current_file_name = ""
        # generate key
        run(aes_128_key())
        for subdir, dirs, files in os.walk(directory):
            
            for file in files:
               
                filepath = subdir + os.sep + file
                if filepath.endswith(".mp4"):
                    
                    if not filepath.endswith("trailer.mp4"):
                        
                        current_file_name = file[:-8]
                       
                        # print("FILE:", current_file_name)
                        # print("*"*50)
                        mezza = ''.join(file)
                        mezzanines.append("'%s/%s' " % (directory, mezza))
        
        for subdir, dirs, files in os.walk(os.getcwd()):
            for file in files:
               
                filepath = subdir + os.sep + file
             
                if filepath.endswith(".srt") and file[:-7] == current_file_name :
                    
                    subtitles.append(subtitles_assembler(file))
                

        cmd = 'python scripts/utils/mp4-hls.py --encryption-key=$(hexdump -e {x} enc.key) --output-encryption-key  {mezzanines} {subtitles}'.format(
            x="""'"%x"'""",
           
            mezzanines=''.join(mezzanines),
            subtitles=''.join(subtitles)
        )
        return cmd
    


    def move_bento4_output_into_movie_folder():
        cmd = 'mv output {directory}'.format(
            directory=directory
        )
        run(cmd)

    def create_output_folders(directory):
        if not os.path.exists(directory):
            os.makedirs(directory)
            if len(sys.argv)>1:
                if sys.argv[2] == 'trailer':
                    trailer = os.path.join(directory, "trailer")
                    os.makedirs(trailer)


    def run(cmd, shell=False):
        print("cmd START:", cmd)
        p = subprocess.check_output(cmd, shell=True)
        print("cmd finished")

    selected_streams = []
    commands = []
    create_output_folders(directory) 
    def subtitles_assembler(in_file):
        """
        looks for srt subtitles with same name as file is being processed. Extract two-letter iso code. Convert them into vtt and returns the subtitle string needed on mp4-hls.py script"

        """
       
        base_name = os.path.splitext(in_file)[0]
       
        subtitle_string_for_mp42hls = ""
        filepath = os.path.join(os.getcwd(),in_file)
        file_base = os.path.splitext(in_file)[0]
        size = len(file_base)    
           
        if base_name == file_base:
            
            output_vtt = os.path.join(os.getcwd() , os.path.splitext(os.path.basename(filepath))[0] + '.vtt')
            
            language = os.path.splitext(os.path.basename(filepath))[0][-2:]
            # convert srt into vtt
            cmd = 'ffmpeg -y -i {filepath} {output}'.format(
                filepath=filepath,
                output=output_vtt
            )
            run(cmd)
            single_subt_string = '[+format=webvtt,+language={language}]{output_vtt} '.format(
                language=language,
                output_vtt=output_vtt
            )
            subtitle_string_for_mp42hls += single_subt_string
        
        return subtitle_string_for_mp42hls

    def s3_upload():
        """
        Upload output folder into aws s3 bucket using sync command
        """
        cmd = 'aws s3 sync {variants_folder}/output/  s3://{destination_bucket}/{out_name}'.format(
            variants_folder=directory,
            destination_bucket=s3_destination_bucket,
            out_name=out_name
        )
        print ('SYNC_COMMAND:', cmd)
        return cmd
    
    # add trailer support on arguments
    # if len(sys.argv)>1:
        
    #     if sys.argv[2] == 'trailer':
    #         times = thumbnails_time_divider(duration, 12, 1000)
    #         trailer = trailer_cmd(times, file, 0.8)
    #         run(trailer)
    

    for variant in variants:
        stream = get_profile(variant, aspect_ratio, PROFILE_STREAMS)
        if stream:
            selected_streams.append(stream)

    for stream in selected_streams:
        commands.append(create_command(directory, file, stream))
    for cmd in commands:
       
        run(cmd)
    
    m3u8_cmd = create_master_playlist_with_subtitles_and_encryption()
    try:
        run(m3u8_cmd)
        
    except subprocess.CalledProcessError as e:
        print("ERROR:",e.output)
        try:
            os.rmdir("output")
            run(m3u8_cmd)
        except subprocess.CalledProcessError as e:
            print("ERROR_2:",e.output)
            pass

    
    move_bento4_output_into_movie_folder()
    #upload output folder into s3 bucket
    
    if len(sys.argv)>1:
        
        if sys.argv[1] == 'sync_bucket':
            sync_cmd = s3_upload()
            run(sync_cmd)
    # fill csv with master and trailer url
    cloudfront_url = os.path.join(cloudfront_domain,  out_name, 'master.m3u8')

    with open('out_urls.csv', 'a') as f:
        added_scenes = csv.writer(f)
        added_scenes.writerow(
            [out_name, cloudfront_url, duration_TC])


def mediainfo_get_prop_value(fq_file_name, ptype, prop_name):
    """
    Get the value of a single mediainfo property.

    Run 'mediainfo --Info-Parameters' to get an exhaustive list.
        Example: 'mediainfo --Inform=Video;%Duration% /home/myuser/test_file.avi'

    :param fq_file_name:
    :ptype: mediainfo property type (e.g. 'Video', 'Audio',...)
    :param prop_name: mediainfo property name (e.g. 'Count', 'Title, 'Language',...)
    :return:
    """

    cmd = ['mediainfo', '--Inform=%s;%%%s%%\\n' %
           (ptype, prop_name), fq_file_name]
    pout = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    prop_value = pout.communicate()[0].strip()
    return prop_value


if __name__ == "__main__":
    main()


# %%
