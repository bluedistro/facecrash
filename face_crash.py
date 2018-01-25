# Copyright (c) 2015 Matthew Earl
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
    import cv2
    import dlib
    import numpy
except ImportError as e:
    print(str(e))
import os


class TooManyFaces(Exception):
    pass


class NoFaces(Exception):
    pass


class Crash:

    def __init__(self):

        self.PREDICTOR_PATH = 'shape_predictor_68_face_landmarks.dat'
        self.SCALE_FACTOR = 1
        self.FEATHER_AMOUNT = 11

        self.FACE_POINTS = list(range(17, 68))
        self.MOUTH_POINTS = list(range(48, 61))
        self.RIGHT_BROW_POINTS = list(range(17, 22))
        self.LEFT_BROW_POINTS = list(range(22, 27))
        self.RIGHT_EYE_POINTS = list(range(36, 42))
        self.LEFT_EYE_POINTS =list(range(42, 48))
        self.NOSE_POINTS = list(range(27, 35))
        self.JAW_POINTS = list(range(0, 17))

        # Points to use to line up the images
        self.ALIGN_POINTS = (self.LEFT_BROW_POINTS + self.RIGHT_EYE_POINTS + self.RIGHT_EYE_POINTS +
                             self.RIGHT_BROW_POINTS + self.NOSE_POINTS + self.MOUTH_POINTS)

        # Points from the second image to overlay on the first.
        #  The convex hull of each element will be overlaid
        self.OVERLAY_POINTS =  [
            self.LEFT_EYE_POINTS + self.RIGHT_EYE_POINTS + self.LEFT_BROW_POINTS + self.RIGHT_BROW_POINTS,
            self.NOSE_POINTS + self.MOUTH_POINTS,
        ]

        # Amount of blur to use during colour correction, as a fraction of the pupillary distance
        self.COLOUR_CORRECT_BLUR_FRAC = 0.6

        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(self.PREDICTOR_PATH)

    def get_landmarks(self, im):
        rects = self.detector(im, 1)

        if len(rects) > 1:
            raise TooManyFaces

        if len(rects) == 0:
            raise NoFaces

        return numpy.matrix([[p.x, p.y] for p in self.predictor(im, rects[0]).parts()])

    @staticmethod
    def annotate_landmarks(im, landmarks):
        im = im.copy()
        for idx, point in enumerate(landmarks):
            pos = (point[0, 0], point[0, 1])
            cv2.putText(im, str(idx), pos,
                        fontFace=cv2.FONT_HERSHEY_SCRIPT_SIMPLEX,
                        fontScale=0.4,
                        color = (0, 0, 255))

            cv2.circle(im, pos, 3, color=(0, 255, 255))
        return im

    @staticmethod
    def draw_convex_hull(im, points, color):
        points = cv2.convexHull(points)
        cv2.fillConvexPoly(im, points, color=color)

    def get_face_mask(self, im, landmarks):
        im = numpy.zeros(im.shape[:2], dtype=numpy.float64)

        for group in self.OVERLAY_POINTS:
            self.draw_convex_hull(im,
                             landmarks[group],
                             color=1)

        im = numpy.array([im, im, im]).transpose((1, 2, 0))

        im = (cv2.GaussianBlur(im, (self.FEATHER_AMOUNT, self.FEATHER_AMOUNT), 0) > 0) * 1.0
        im = cv2.GaussianBlur(im, (self.FEATHER_AMOUNT, self.FEATHER_AMOUNT), 0)

        return im

    @staticmethod
    def transformation_from_points(points1, points2):

        points1 = points1.astype(numpy.float64)
        points2 = points2.astype(numpy.float64)

        c1 = numpy.mean(points1, axis=0)
        c2 = numpy.mean(points2, axis=0)
        points1 -= c1
        points2 -= c2

        s1 = numpy.std(points1)
        s2 = numpy.std(points2)

        points1 /= s1
        points2 /= s2

        U, S, Vt = numpy.linalg.svd(points1.T * points2)

        R = (U * Vt).T

        return numpy.vstack([numpy.hstack(((s2 / s1 ) * R,
                                           c2.T - (s2/s1) * R * c1.T)),
                             numpy.matrix([0., 0., 1.])])

    def read_im_and_landmarks(self, fname):
        im = cv2.imread(fname, cv2.IMREAD_COLOR)
        im = cv2.resize(im, (im.shape[1] * self.SCALE_FACTOR,
                             im.shape[0] * self.SCALE_FACTOR))

        landmarks = self.get_landmarks(im)

        return im, landmarks

    @staticmethod
    def warp_im(im, M, dshape):
        output_im = numpy.zeros(dshape, dtype=im.dtype)
        cv2.warpAffine(im,
                       M[:2],
                       (dshape[1], dshape[0]),
                       dst=output_im,
                       borderMode=cv2.BORDER_TRANSPARENT,
                       flags=cv2.WARP_INVERSE_MAP)

        return output_im

    def correct_colours(self, im1, im2, landmarks1):
        blur_amount = self.COLOUR_CORRECT_BLUR_FRAC * numpy.linalg.norm(
            numpy.mean(landmarks1[self.LEFT_EYE_POINTS], axis=0) -
            numpy.mean(landmarks1[self.RIGHT_EYE_POINTS], axis=0))

        blur_amount = int(blur_amount)

        if blur_amount % 2 == 0:
            blur_amount += 1

        im1_blur = cv2.GaussianBlur(im1, (blur_amount, blur_amount), 0)
        im2_blur = cv2.GaussianBlur(im2, (blur_amount, blur_amount), 0)
        # Avoid divide-by-zero
        im2_blur += (128 * (im2_blur <= 1.0)).astype(im2_blur.dtype)

        return (im2.astype(numpy.float64) * im1_blur.astype(numpy.float64) /
                im2_blur.astype(numpy.float64))

    def implement(self, face_frame_image, face_mask_image, output_name, dir_name):

        '''
        :param face_frame_image: the frame image on which the mask image will be laid
        :param face_mask_image:  the mask image to be laid on the frame image
        :param output_name: preferred nomenclature for output image file
        :param dir_name: directory to hold input and output files
        :return:
        '''

        im1, landmarks1 = self.read_im_and_landmarks(face_frame_image)
        im2, landmarks2 = self.read_im_and_landmarks(face_mask_image)

        M = self.transformation_from_points(landmarks1[self.ALIGN_POINTS],
                                            landmarks2[self.ALIGN_POINTS])

        mask = self.get_face_mask(im2, landmarks2)
        warped_mask = self.warp_im(mask, M, im1.shape)
        combined_mask = numpy.max([self.get_face_mask(im1, landmarks1), warped_mask],
                                  axis=0)

        warped_im2 = self.warp_im(im2, M, im1.shape)
        warped_corrected_im2 = self.correct_colours(im1, warped_im2, landmarks1)

        output_im = im1 * (1.0 - combined_mask) + warped_corrected_im2 * combined_mask
        output_name = str(output_name) + '.jpg'
        output = os.path.join(dir_name, output_name)
        cv2.imwrite(output, output_im)