                                    FACE MASH
--------------------------------------------------------------------------------------------------------------
An API to swap to mask frontal facial features of one image onto another facial image's fontal frame

HOW TO TEST
----------
1. This program has been tested only with Python 2.7, it's performance in Python 3.x is....x :)
2. Make sure all python modules modules in the requirements.txt are properly installed and functioning
3. You might need to POSTMAN or other similar alternatives to make an HTTP POST request to the API.
4. Run the face_mash_api.py file
5. The field names to use in POSTMAN are:
    * face_frame: The frame image on which the mask image will be laid (type-> file)
    * face_mask: the mask image to be laid on the frame image (type ->  file)
    * dir_name: directory to hold input and output files (type -> text)
6. Now, make a POST request to the API which will be running on port:8080 by default
   to test it out.
   The full url is: http://127.0.0.1/face_mash