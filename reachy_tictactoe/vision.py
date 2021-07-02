import numpy as np
import cv2 as cv
import logging
import os

import cv2 as cv 
from PIL import Image

#TC from edgetpu.utils import dataset_utils
from utils import dataset
#TC from edgetpu.classification.engine import ClassificationEngine
from adapters import classify, common
from utils.edgetpu import make_interpreter
from utils.dataset import read_label_file

from .utils import piece2id
from .detect_board import get_board_cases


logger = logging.getLogger('reachy.tictactoe')

#TC 
dir_path = os.path.dirname(os.path.realpath(__file__))
model_path = os.path.join(dir_path, 'models')


#TC boxes_classifier = ClassificationEngine(os.path.join(model_path, 'ttt-boxes.tflite'))
#TC boxes_labels = dataset_utils.read_label_file(os.path.join(model_path, 'ttt-boxes.txt'))
#path_model_box = '/home/reachy/dev/reachy-tictactoe/reachy_tictactoe/models/ttt_classif.tflite'
#path_label_box = '/home/reachy/dev/reachy-tictactoe/reachy_tictactoe/models/ttt_classif.txt'
#path_model_board = '/home/reachy/dev/reachy-tictactoe/reachy_tictactoe/models/ttt-valid-board.tflite'
#path_label_board = '/home/reachy/dev/reachy-tictactoe/reachy_tictactoe/models/ttt-valid-board.txt'

path_model_box = '/home/reachy/dev/reachy-tictactoe/reachy_tictactoe/models/ttt-boxes.tflite'
path_label_box = '/home/reachy/dev/reachy-tictactoe/reachy_tictactoe/models/ttt-boxes.txt'
path_model_board = '/home/reachy/dev/reachy-tictactoe/reachy_tictactoe/models/ttt-valid-board.tflite'
path_label_board = '/home/reachy/dev/reachy-tictactoe/reachy_tictactoe/models/ttt-valid-board.txt'


#TC valid_classifier = ClassificationEngine(os.path.join(model_path, 'ttt-valid-board.tflite'))
#TC valid_labels = dataset_utils.read_label_file(os.path.join(model_path, 'ttt-valid-board.txt'))

interpreterBox = make_interpreter(os.path.join(model_path, 'ttt-boxes.tflite'))
interpreterBox.allocate_tensors()
labelsBox = read_label_file(os.path.join(model_path, 'ttt-boxes.txt'))
sizeBox = common.input_size(interpreterBox)

interpreterBoard = make_interpreter(os.path.join(model_path, 'ttt-valid-board.tflite'))
interpreterBoard.allocate_tensors()
labelsBoard = read_label_file(os.path.join(model_path, 'ttt-valid-board.txt'))
sizeBoard = common.input_size(interpreterBoard)

sizeInterpreterBoard = common.input_size(interpreterBoard)
sizeInterpreterBox = common.input_size(interpreterBox)

board_cases = np.array((
    ((81, 166, 260, 340), #Coordinates first board cases (top-left corner) (Xbl, Xbr, Ytr, Ybr)
     (166, 258, 260, 340), #Coordinates second board cases
     (258, 349, 260, 340),),

    ((74, 161, 340, 432),
     (161, 261, 340, 432),
     (261, 360, 340, 432),),

    ((65, 161, 432, 522),
     (161, 266, 432, 522),
     (266, 365, 432, 522),),
))

# left, right, top, bottom
board_rect = np.array((
    62, 372, 250, 508,
))

shape = (224, 224)

def get_board_configuration(img):
    board = np.zeros((3, 3), dtype=np.uint8)

    # try:
    #     custom_board_cases = get_board_cases(img)
    # except Exception as e:
    #     logger.warning('Board detection failed', extra={'error': e})
    #     custom_board_cases = board_cases
    custom_board_cases = board_cases
    sanity_check = True

    for row in range(3):
        for col in range(3):
            lx, rx, ly, ry = custom_board_cases[row, col]
            #img = img.convert('RGB')
            #img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
            #img = img.resize(shape, Image.NEAREST)
            #TC piece, score = identify_box(img[ly:ry, lx:rx])
            piece, score = identify_box(img[ly:ry, lx:rx])
            #if score < 0.9:
            #    sanity_check = False
            #    return [], sanity_check
            # We invert the board to present it from the Human point of view
            if score < 0.9:
                piece = 0
            board[2 - row, 2 - col] = piece
    return board, sanity_check


def identify_box(box_img):

    #TC res = boxes_classifier.classify_with_image(img_as_pil(box_img), top_k=1)
    #box_img = cv.cvtColor(box_img, cv.COLOR_BGR2RGB)
    #box_img = cv.resize(box_img , (224,224))
    pil_img = Image.fromarray(box_img).convert('RGB').resize(sizeInterpreterBox, Image.ANTIALIAS)
    #common.set_input(interpreterBox, img_as_pil(box_img))
    common.set_input(interpreterBox, pil_img)
    interpreterBox.invoke()
    result = classify.get_classes(interpreterBox, top_k=1, score_threshold=0.1)
    label = labelsBox.get(result[0].id)
    logger.info(f'label : {label}')        
    assert result

    label, score = result[0]

    return label, score


def is_board_valid(img):
    lx, rx, ly, ry = board_rect
    #TC board_img = img[ly:ry, lx:rx]
    #board_img = img[ly:ry, lx:rx]
    #img = img.convert('RGB')
    #board_img = cv.cvtColor(board_img, cv.COLOR_BGR2RGB)
    #board_img = board_img.resize(shape, Image.NEAREST)
    #board_img = cv.resize(board_img , shape)
    #TC res = valid_classifier.classify_with_image(img_as_pil(board_img), top_k=1)
    pil_img = Image.fromarray(img[ly:ry, lx:rx]).convert('RGB').resize(sizeInterpreterBoard, Image.ANTIALIAS)
    #common.set_input(interpreterBoard, img_as_pil(board_img))
    common.set_input(interpreterBoard, pil_img)
    interpreterBoard.invoke()
    result = classify.get_classes(interpreterBoard, top_k=1, score_threshold=0.1)
    assert result
    label = labelsBoard.get(result[0].id)
    

    label_index, score = result[0]
    #TC label = valid_labels[label_index]
    logger.info('pouetteeeee')
    logger.info('Board validity check', extra={
        'label': label,
        'score': score,
    })

    return label == 'valid' and score > 0.65


def img_as_pil(img):
    return Image.fromarray(cv.cvtColor(img.copy(), cv.COLOR_BGR2RGB))
