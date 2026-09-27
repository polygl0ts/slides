# Slides

**Public** repository that contains all slides and recordings that were given for polygl0ts presentations.

## Folder structure

Push any slides deck into the `decks/` folder.
Slides deck should have the following naming convention: 
YYYY-MM-DD-title.pdf

## Video Encoding

If you do a recording it will likely be >100 MB, so you need to compress it to <100MB so github is willing
to track it. You can do it like so:
```bash
# First pass to generate stats over the whole vid
# -y                    auto-approve
# -i input.mp4          input file
# -c:v libx264          use H.264 ecnoding
# -preset slow          take some time, get good quality
# -b:v 270k             average video bitrate, reduce this if you want to reduce the size more
# -r 30                 30 FPS
# -pass 1               just do analysis
# -an                   don't look at audio
# -f null /dev/null     no video output needed
ffmpeg -y -i input.mp4 -c:v libx264 -preset slow -b:v 270k -r 30 -pass 1 -an -f null /dev/null

# Second pass, compress the video with the stats we just calculated
# -pass 2               actually do the compression
# -c:a aac              encode the audio as AAC
# -b:a 64k              use 64 kbps for audio
# -ac 1                 use mono instead of stereo audio
# -movflags +faststart  make browsers able to start the vid before it is fully loaded
ffmpeg -i input.mp4 -c:v libx264 -preset slow -b:v 270k -r 30 -pass 2 -c:a aac -b:a 64k -ac 1 -movflags +faststart input-small.mp4

# Clean up artifacts
rm ffmpeg2pass-0.log ffmpeg2pass-0.log.mbtree
```
Input is `input.mp4`, output is `input-small.mp4`. If it is still not small enough, reduce the bitrate (or framerate) (but check the quality afterwards!).
