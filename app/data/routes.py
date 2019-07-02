import os
import json
from flask import render_template, request, send_file, Response
import numpy as np
import pandas as pd

from config import DATA_DIR
from . import data
from tool import msgwrap, get_type, safepath, gen_random_string, sample_data


@data.route('/upload', methods=['POST'])
@msgwrap
def upload():
    # TODO : return message
    global DATA_DIR
    path = request.form.get('dataset')
    path = safepath(path)
    file = request.files['file']
    path = os.path.join(DATA_DIR, path)
    file.save(path)
    return {
        "size":os.path.getsize(path),
        'type':get_type(path),
    }

@data.route('/createset', methods=['POST'])
@msgwrap
def createset():
    global DATA_DIR
    req = request.get_data().decode('utf-8')
    req = json.loads(req)
    path = req.pop('dataset')
    path = safepath(path)
    path = os.path.join(DATA_DIR, path)
    os.mkdir(path)

@data.route('/view', methods=['POST'])
@msgwrap
def view():
    global DATA_DIR
    file_limit = 20
    def oswalk(obj, path):
        dirs = sorted(os.listdir(path))
        for i in dirs:
            new_path = os.path.join(path, i)
            if os.path.isdir(new_path):
                obj[i] = {}
                oswalk(obj[i], new_path)
        cnt = 0
        for i in dirs:
            new_path = os.path.join(path, i)
            if os.path.isfile(new_path):
                obj[i] = [os.path.getsize(new_path) // 1024, get_type(new_path)]
                cnt += 1
                if cnt >= file_limit:
                    break
    structure = {}
    oswalk(structure, DATA_DIR)
    return {
        'structure':json.dumps(structure)
    }

@data.route('/get', methods=['POST'])
@msgwrap
def get():
    global DATA_DIR
    req = request.get_data().decode('utf-8')
    req = json.loads(req)
    path = safepath(req.pop('dataset'))
    name = safepath(req.pop('name'))
    path = os.path.join(DATA_DIR, path, name)
    if not os.path.exists(path):
        return {
            'succeed':0,
            'message':"File Not Exists",
        }
    if not os.path.isfile(path):
        return {
            'succeed':0,
            'message':path+ ' is not a file',
        }
    ret = sample_data(path, type_='path')

    return ret

@data.route('/move', methods=['POST'])
@msgwrap
def move():
    global DATA_DIR
    req = request.get_data().decode('utf-8')
    req = json.loads(req)
    src = safepath(req.pop('src_path'))
    dest = safepath(req.pop('dest_path'))
    src = os.path.join(DATA_DIR, src)
    dest = os.path.join(DATA_DIR, dest)
    os.rename(src, dest)

@data.route('/delete', methods=['POST'])
@msgwrap
def delete():
    global DATA_DIR
    req = request.get_data().decode('utf-8')
    req = json.loads(req)
    path = safepath(req.pop('path'))
    path = os.path.join(DATA_DIR, path)
    if os.path.isdir(path):
        for root, dirs, files in os.walk(path, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(path)
    else:
        os.remove(path)

@data.route('/download', defaults={'path':''}, methods=['GET'])
@data.route('/download/<path:path>', methods=['GET'])
def download(path):
    import io
    global DATA_DIR
    print(path)
    path = safepath(path)
    path = os.path.join(os.getcwd(), DATA_DIR, path)
    print(path)
    def send_chunk(filepath):
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(20 * 1024 * 1024)
                if not chunk:
                    break
                yield chunk
    return Response(send_chunk(path), content_type='application/octet-stream')
