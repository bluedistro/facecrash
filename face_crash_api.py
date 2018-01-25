# ----------------------------------------------------------------------------------------------------------
# Copyright (c) 2018 Kingsley Biney
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
#     The above copyright notice and this permission notice shall be included
#     in all copies or substantial portions of the Software.
#
#     THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#     OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#     MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
#     NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#     DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#     OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#     USE OR OTHER DEALINGS IN THE SOFTWARE.

try:
    from face_crash import Crash
    from flask import Flask, request, jsonify
    from werkzeug.utils import secure_filename
except ImportError as e:
    print(str(e))
import time
import os
import platform

# platform requirements check: platform - Linux, python version (Major and Minor): 2.7
operating_system = str(platform.platform())
machine_bit_type = str(platform.machine())
system_type = str(platform.system())

py_version = str(platform.python_version())
py_version_split = py_version.split('.')
py_version_major = int(py_version_split[0])
py_version_minor = int(py_version_split[1])

print('\n[INFO] This program has only been tested on Python version: 2.7. Make sure you are running on python 2.7')
print('please wait ...\n')
time.sleep(3)

print('[INFO] Detected OS: {}'.format(operating_system))
time.sleep(1)
print('[INFO] Detected Python Version: {}'.format(py_version))
time.sleep(1)
print('[INFO] Machine: {}\n'.format(machine_bit_type))
time.sleep(1)

# Initialize the Flask application
app = Flask(__name__)

# These are the extension that we are accepting to be uploaded
app.config['ALLOWED_EXTENSIONS'] = set(['png', 'jpg', 'jpeg', 'JPG', 'JPEG', 'PNG'])


# validate file type
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


# setting up the facecrash route
@app.route('/facecrash', methods=['POST'])
def upload():

    # for now users are supposed to create a dummy dir to hold each pair of uploaded images and results
    dir_name = request.form['dir_name']
    face_frame = request.files['face_frame']
    face_mask = request.files['face_mask']

    # check the existence of directory
    if os.path.exists(dir_name):
        print('directory exists already, proceeding with entries')
        pass
    else:
        try:
            os.mkdir(dir_name)
            print('directory {} has been created'.format(dir_name))
        except Exception as e:
            print(str(e))

    if face_frame and allowed_file(face_frame.filename):
        # Make the filename safe, remove unsupported chars prefixed with time
        face_frame_filename = str(time.time()) + "__" + secure_filename(face_frame.filename)

        # save file in directory
        face_frame.save(os.path.join(dir_name, face_frame_filename))

    if face_mask and allowed_file(face_mask.filename):
        # Make the filename safe, remove unsupported chars prefixed with time
        face_mask_filename = str(time.time()) + "__" + secure_filename(face_mask.filename)

        # save file in directory
        face_mask.save(os.path.join(dir_name, face_mask_filename))

    # get the full path of the directory with the images
    ff_1 = os.path.join(dir_name, face_frame_filename)
    fm_1 = os.path.join(dir_name, face_mask_filename)

    # renaming the output files
    output_name = face_frame_filename+face_mask_filename

    # call the implement method in the  mash class
    Crash().implement(face_frame_image=ff_1, face_mask_image=fm_1, output_name=output_name,
                      dir_name=dir_name)
    return jsonify({'status':'Okay'})


if __name__ == '__main__':

    if system_type == 'Linux' and py_version_major == 2 and py_version_minor == 7:
            app.run(debug=True, port=8080)
    else:
        print('Core requirements not found thereby quitting ...')
        exit(1)