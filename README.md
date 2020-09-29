
Going for something like this (https://github.com/letmaik/avatar-animator) that
links to a webcam in linux. Using the facemesh model in tensorflowjs examples,
then generate an animated image which goes to a v4l2 loopback virtual camera.

Refs:

* https://github.com/letmaik/avatar-animator (not on linux, slow frame rate)
* https://github.com/tensorflow/tfjs-models/tree/master/facemesh (key model)
* https://github.com/alievk/avatarify (bit funky)
* https://www.youtube.com/watch?v=Cb5x8uChBow (blender to make these?)

# Tried:

* Using tensorflow python. Doesn't seem to be an option as many functions are
  web-specific and model definitions aren't compatible? Can't get tfjs-converter
  working and blazeface seems web-specific.
* Using input streams. Ok to load a single image into the model but I'm not sure
  how to push a video stream.

# Current:

* NodeJS web server handles the model, pushing single frames seems via web
  requests seems to work ok so far.
* OpenCV2 grabs camera frames, sends them to facemesh server, receives keypoints
  back, plots image, writes to ffmpeg process which produces a video stream.

# Issues:

* Lot of image conversion going on:
    * OpenCV2 grabs a frame as a numpy array, encodes as jpeg to send to server,
      then decoded to pixel array then tensor.
    * Would be better to have ffmpeg split the stream to images itself (for that
      I need to know how to read an image2pipe input stream as a frame sequence).
* guvcview (and ffplay) can handle the output stream but Zoom doesn't. Seems to be a
  formatting issue as writing the input frames directly to output also doesn't
  work. Presumably I just need to tweak the ffmpeg settings.
* Python code may be better as async, where each update triggers the next process in line:
    * new image on stdin -> update latest image
    * on schedule or trigger -> update latest keypoints
    * on schedule or trigger -> update current output frame
    * on schedule -> write frame to stdout
    * (unsure how much of this 'backpressure' is handled by ffmpeg i/o streams
      themselves, which is which opencv2's approach of getting frames is a
      little easier to follow)
