#!/usr/bin/env python
# coding: utf-8

import os
from rknn.api import RKNN
from math import exp
from sys import exit
import argparse
import onnxscript
from onnxscript.rewriter import pattern
import onnx.numpy_helper as onh
import numpy as np
import onnx
import onnxruntime as ort
from rknn.utils import onnx_edit

os.chdir(os.path.dirname(os.path.abspath(__file__)))

speech_length = 171

def convert_encoder():
    rknn = RKNN(verbose=True)

    ONNX_MODEL=f"sense-voice-encoder.onnx"
    RKNN_MODEL=ONNX_MODEL.replace(".onnx",".rknn")
    DATASET="dataset.txt"
    QUANTIZE=False

    #开局先给我来个大惊喜，rknn做第一步常量折叠的时候就会在这个子图里报错，所以要单独拿出来先跑一遍
    #然后把这个子图的输出结果保存下来喂给rknn
    onnx.utils.extract_model(ONNX_MODEL, "extract_model.onnx", ['speech_lengths'], ['/make_pad_mask/Cast_2_output_0'])
    sess = ort.InferenceSession("extract_model.onnx", providers=['CPUExecutionProvider'])
    extract_result = sess.run(None, {"speech_lengths": np.array([speech_length], dtype=np.int64)})[0]

    # 删掉模型最后的多余transpose, 速度从365ms提升到350ms
    ret = onnx_edit(model = ONNX_MODEL,
        export_path = ONNX_MODEL.replace(".onnx", "_edited.onnx"),
        # # 1, len, 25055 -> 1, 25055, 1, len   # 这个是坏的, 我真服了，
        # outputs_transform = {'encoder_out': 'a,b,c->a,c,1,b'},
        outputs_transform = {'encoder_out': 'a,b,c->a,c,b'},
    )
    ONNX_MODEL = ONNX_MODEL.replace(".onnx", "_edited.onnx")

    # pre-process config
    print('--> Config model')
    rknn.config(quantized_algorithm='normal', quantized_method='channel', target_platform='rk3588', optimization_level=3)
    print('done')

    # Load ONNX model
    print("--> Loading model")
    ret = rknn.load_onnx(
        model=ONNX_MODEL,
        inputs=["speech", "/make_pad_mask/Cast_2_output_0"],
        input_size_list=[[1, speech_length, 560], [extract_result.shape[0], extract_result.shape[1]]],
        input_initial_val=[None, extract_result],
        # outputs=["output"]
    )

    if ret != 0:
        print('Load model failed!')
        exit(ret)
    print('done')

    # Build model
    print('--> Building model')
    ret = rknn.build(do_quantization=QUANTIZE, dataset=DATASET, rknn_batch_size=None)
    if ret != 0:
        print('Build model failed!')
        exit(ret)
    print('done')

    # export
    print('--> Export RKNN model')
    ret = rknn.export_rknn(RKNN_MODEL)
    if ret != 0:
        print('Export RKNN model failed!')
        exit(ret)
    print('done')

# usage: python convert_rknn.py encoder|all

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=str, help="model to convert", choices=["encoder", "all"], nargs='?')
    args = parser.parse_args()
    if args.model is None:
        args.model = "all"

    if args.model == "encoder":
        convert_encoder()
    elif args.model == "all":
        convert_encoder()
    else:
        print(f"Unknown model: {args.model}")
        exit(1)
