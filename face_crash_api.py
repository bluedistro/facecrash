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


from face_crash import crash
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import time
import os

# Initialize the Flask application
app = Flask(__name__)

# These are the extension that we are accepting to be uploaded
app.config['ALLOWED_EXTENSIONS'] = set(['png', 'jpg', 'jpeg'])

# validate file type
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

# setting up the facecrash route
@app.route('/facecrash', methods=['POST'])
def upload():

    # for now users are supposed to create a dummy dir to hold each pair of uploaded images with results
    dir_name = request.form['dir_name']
    face_frame = request.files['face_frame']
    face_mask = request.files['face_mask']

    # check the existence of directory
    if os.path.exists(dir_name):
        print('directory exists already, proceeding with entries')
        pass
    else:
        os.mkdir(dir_name)
        print('directory {} has been created'.format(dir_name))

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

    # read_files from folders
    ff_1 = os.path.join(dir_name, face_frame_filename)
    fm_1 = os.path.join(dir_name, face_mask_filename)

    # renaming the output files
    output_name = face_frame_filename+face_mask_filename

    # call the implement method in the  mash class
    crash().implement(face_frame_image=ff_1, face_mask_image=fm_1,
                              output_name=output_name, dir_name=dir_name)
    return jsonify({'status':'Okay'})


if __name__ == '__main__':
    app.run(debug=True, port=8080)