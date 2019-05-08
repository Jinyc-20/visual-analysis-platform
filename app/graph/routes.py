import os
import redis
import pickle
import multiprocessing
import json as js
import pandas as pd
import numpy as np

from flask import render_template, request

from . import graph
from .graphclass import Graph
from tool import msgwrap, safepath, gen_random_string
from config import CACHE_DIR, REDIS_HOST, REDIS_DB, REDIS_PORT, PROJECT_DIR, STATIC_PATH
from common import component_detail


r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, charset='utf-8', decode_responses=True)

processing_manager = {}

@graph.route('/get', methods=['POST'])
@msgwrap
def get_graph():
    req = request.get_data().decode('utf-8')
    req = js.loads(req)
    pid = req.pop('project_id')
    with open(os.path.join(PROJECT_DIR, pid+'.pickle'), 'rb') as f:
        p_data = pickle.load(f)
    G = p_data.pop('graph', {
        'all_nodes':[],
        'all_lines':[],
    })
    return G

@graph.route('/save', methods=['POST'])
@msgwrap
def save_graph():
    req = request.get_data().decode('utf-8')
    req = js.loads(req)
    pid = req.pop('project_id')
    all_nodes = req.pop('all_nodes')
    all_lines = req.pop('all_lines')
    with open(os.path.join(PROJECT_DIR, pid+'.pickle'), 'rb') as f:
        p_data = pickle.load(f)
    p_data.update({
        'graph':{
            'all_nodes':all_nodes,
            'all_lines':all_lines,
        }
    })
    with open(os.path.join(PROJECT_DIR, pid+'.pickle'), 'wb') as f:
        f.write(pickle.dumps(p_data))


@graph.route('/run', methods=['POST'])
@msgwrap
def run():
    # TODO: check format & create Graph as parameter
    fail = {
        'succeed': 1,
        'message': '',
    }

    req = request.get_data().decode('utf-8')
    req = js.loads(req)
    pid = req.pop('project_id')
    global processing_manager
    # check the project not running yet
    if pid in processing_manager:
        if not processing_manager[pid].is_alive():
            processing_manager.pop(pid)
        else:
            fail['message'] = "this project is running now"
            return fail

    G = Graph(pid)
    all_nodes = req.pop('all_nodes')
    all_lines = req.pop('all_lines')
    for node in all_nodes:
        ret = G.add_node(node['node_name'], node['node_type'], node['details'])
        if not ret:
            message = 'add node fail ' + node['node_name'] + ' ' +  node['node_type'] + ' ' + node['details']
            fail['message'] = message
            return fail
    for line in all_lines:
        print(line, flush=True)
        ret = G.add_edge(line['line_from'], int(line['line_from_port']), line['line_to'], int(line['line_to_port']))
        if not ret:
            message = 'add edge fail' + \
                    line['line_from'] + ' ' + \
                    line['line_from_port'] + ' ' + \
                    line['line_to'] + ' ' + \
                    line['line_to_port']
            fail['message'] = message
            return fail

    ret = G.load_cache()
    if not ret:
        message = 'local cache fail'
        fail['message'] = message
        return fail

    run_node = req.pop('run', None)

    process = multiprocessing.Process(name=pid, target=G, args=(run_node,))
    process.daemon = True
    process.start()
    processing_manager.update({
        pid: process
    })



@graph.route('/progress', methods=['POST'])
@msgwrap
def progress():
    req = request.get_data().decode('utf-8')
    req = js.loads(req)
    pid = req.pop('project_id')
    global processing_manager
    status = 0
    if pid in processing_manager and processing_manager[pid].is_alive():
        status = 1
    progress_ = r.hgetall(pid)
    print(pid, "nodes' status :", progress_, flush=True)

    progress = []
    for key, value in progress_.items():
        progress.append({
            'node_name':key,
            'node_status':value
        })

    ret = {
        "status":status,
        "progress":progress
    }
    return ret

@graph.route('/stop', methods=['POST'])
@msgwrap
def stop():
    req = request.get_data().decode('utf-8')
    req = js.loads(req)
    pid = req.pop('project_id')
    global processing_manager
    if pid not in processing_manager:
        return {
            "succeed": 1,
            "message": str(pid) + " not running",
        }
    processing_manager[pid].terminate()
    processing_manager.pop(pid)


@graph.route('/sample', methods=['POST'])
@msgwrap
def sample():
    # TODO
    global CACHE_DIR
    global component_detail
    req = request.get_data().decode('utf-8')
    req = js.loads(req)
    num = int(req.pop('number', 10))
    pid = req.pop('project_id')
    nid = req.pop('node_id')

    # get pid/nid's data
    with open(os.path.join(CACHE_DIR, pid, nid+'.pickle'), 'rb') as f:
        data = pickle.load(f)
    type_ = nid.split('-')[0]
    icomp = component_detail[type_]
    out = icomp['out_port']
    ret = {
        'data':[],
    }
    retdata = ret['data']
    for i in range(len(out)):
        outtype = out[i]
        idata = data['out'][i]
        if outtype == 'DataFrame':
            num = max(num, 0)
            num = min(num, idata.shape[0])
            index = list(idata.columns)
            df = idata[0:num]
            df = df.round(3)
            types = [str(df[index[j]].dtype) for j in range(len(index))]
            df = df.fillna('NaN')
            df = np.array(df).tolist()
            retdata.append({
                'type':'DataFrame',
                'shape':list(idata.shape),
                'col_num':len(index),
                'col_index':index,
                'col_type':types,
                'row_num':num,
                'data': df
            })
        elif outtype == 'Image':
            import cv2
            savename = pid + nid + gen_random_string() + '.png'
            savedir = os.path.join('app', 'static', 'cache')
            if not os.path.exists(savedir):
                os.mkdir(savedir)
            idata = idata[0]
            shape = list(idata.shape)
            shape[0], shape[1] = shape[1], shape[0]
            resize_shape = shape[:2]
            while resize_shape[0] > 640 or resize_shape[1] > 480:
                resize_shape[0] //= 2
                resize_shape[1] //= 2
            idata = cv2.resize(idata, tuple(resize_shape))
            cv2.imwrite(os.path.join(savedir, savename), idata)
            retdata.append({
                'type':'Image',
                'data':{
                    'url':'static/cache/'+savename,
                    'shape':shape,
                }
            })
        elif outtype == 'Graph':
            pass
        elif outtype == 'Video':
            pass
        else:
            raise NotImplementedError

    return ret

@graph.route('/init', methods=['POST'])
@msgwrap
def init():
    global CACHE_DIR
    req = request.get_data().decode('utf-8')
    req = js.loads(req)
    pid = req.pop('project_id')
    keys = r.hkeys(pid)
    if len(keys) > 0:
        r.hdel(pid, *keys)
    for root, dirs, files in os.walk(os.path.join(CACHE_DIR, pid)):
        for file in files:
            os.remove(os.path.join(root, file))
