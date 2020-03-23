import os, time, datetime
from flask import Flask, render_template, request
import sys
import argparse
import numpy as np
import pandas as pd
from PIL import Image
import requests
from io import BytesIO
from pm4py.objects.log.importer.xes import factory as xes_import
from pm4py.algo.discovery.alpha import factory as alpha_miner
from pm4py.algo.discovery.inductive import factory as inductive_miner
from pm4py.visualization.petrinet import factory as pn_vis_factory
from pm4py.objects.petri.exporter import pnml as pnml_exporter
from pm4py.objects.petri.importer import pnml as pnml_importer
from pm4py.algo.conformance.alignments import factory as align_factory
from pm4py.objects.petri import utils
from pm4py.algo.discovery.dfg import factory as dfg_factory
from pm4py.visualization.dfg import factory as dfg_vis_factory
from pm4py.objects.conversion.dfg import factory as dfg_mining_factory


app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


@app.route("/", methods=['GET'])
def server():
    return render_template('index.html')

UPLOAD_FOLDER = os.path.basename('uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def read_file(file_path):
    log = xes_import.apply(file_path)
    return log

def inductive_miner_petrinet_no_decor(log_file):
    net, i_m, f_m = inductive_miner.apply(log_file)
    gviz = pn_vis_factory.apply(net, i_m, f_m, parameters={"format": "png", "debug": False})

    pn_vis_factory.save(gviz, "static/inductive_miner_petnet_no_decor.png")
    return net, i_m, f_m

def inductive_miner_petrinet_performance(log_file):
    net, i_m, f_m = inductive_miner.apply(log_file)
    gviz = pn_vis_factory.apply(net, i_m, f_m, parameters={"format": "png", "debug": False}, variant="performance", log=log_file)

    pn_vis_factory.save(gviz, "static/inductive_miner_petnet_performance.png")
    return "success!"

def inductive_miner_petrinet_frequency(log_file):
    net, i_m, f_m = inductive_miner.apply(log_file)
    gviz = pn_vis_factory.apply(net, i_m, f_m, parameters={"format": "png", "debug": False}, variant="frequency", log=log_file)

    pn_vis_factory.save(gviz, "static/inductive_miner_petnet_frequency.png")
    return "success!"

def alignments_func(log, net, i_m, f_m):
    alignment_list = align_factory.apply_log(log, net, i_m, f_m)
    return alignment_list


def directly_follows_graphs_freq(log_file):
    dfg = dfg_factory.apply(log_file)
    gviz = dfg_vis_factory.apply(dfg, log=log_file, variant="frequency")
    pn_vis_factory.save(gviz, "static/dag_frequency.png")
    return "success!"

def directly_follows_graphs_perf(log_file):
    dfg = dfg_factory.apply(log_file)
    gviz = dfg_vis_factory.apply(dfg, log=log_file, variant="performance")
    pn_vis_factory.save(gviz, "static/dag_performance.png")
    return "success!"

@app.route('/upload', methods=['POST'])
def upload_file():

    global path
    file = request.files['input_file']
    name, ext = file.filename.split(".")

    file.filename = name + "." + ext
    path = "uploads" + "/" + file.filename
    f = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(f)

    log = read_file(file_path=path)
    net, i_m, f_m = inductive_miner_petrinet_no_decor(log_file=log)
    msg2 = inductive_miner_petrinet_performance(log_file=log)
    msg3 = inductive_miner_petrinet_frequency(log_file=log)
    msg4 = directly_follows_graphs_freq(log_file=log)
    msg5 = directly_follows_graphs_perf(log_file=log)

    return render_template('links.html')


@app.route('/petrinet_no_decor')
def petrinet_no_decor():
    full_filename = os.path.join("static", 'inductive_miner_petnet_no_decor.png')
    return render_template('petrinet_no_decor.html', full_filename=full_filename)

@app.route('/petrinet_performance')
def petrinet_performance():
    full_filename = os.path.join("static", 'inductive_miner_petnet_performance.png')
    return render_template('petrinet_performance.html', full_filename=full_filename)

@app.route('/petrinet_frequency')
def petrinet_frequency():
    full_filename = os.path.join("static", 'inductive_miner_petnet_frequency.png')
    return render_template('petrinet_frequency.html', full_filename=full_filename)

@app.route('/alignment')
def alignment():
    log = read_file(file_path=path)
    net, i_m, f_m = inductive_miner_petrinet_no_decor(log_file=log)
    alignment_list = alignments_func(log=log, net=net, i_m=i_m, f_m=f_m)

    return render_template('alignments.html', alignment_list=alignment_list)

@app.route('/dag_frequency')
def dag_frequency():
    full_filename = os.path.join("static", 'dag_frequency.png')
    return render_template('dag_frequency.html', full_filename=full_filename)

@app.route('/dag_performance')
def dag_performance():
    full_filename = os.path.join("static", 'dag_performance.png')
    return render_template('dag_performance.html', full_filename=full_filename)

@app.route('/upload_page')
def upload_page():
    return render_template('index.html')

@app.route('/links_page')
def links_page():
    return render_template('links.html')

@app.after_request
def add_header(response):
    # response.cache_control.no_store = True
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == '__main__':
    app.debug = True
    host = os.environ.get('IP', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    app.run(port=port,host=host)
