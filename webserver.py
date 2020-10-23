import sys
import threading

from typing import List

from flask import Flask, render_template, jsonify

import logging

from Managers.data_manager import HAZWaveManager
from Managers.configuration_manager import ConfigurationManager
from models.consts import *
from models.node_relation import NodeRelation

_LOGGER = logging.getLogger(__name__)

app = Flask(__name__)
configuration = ConfigurationManager()
configuration.initialize()

manager = HAZWaveManager(configuration)
initialize_thread = threading.Thread(target=manager.initialize)
initialize_thread.start()


@app.route("/")
def home():
    return home_index()


@app.route(f"/{WEBSITE_INDEX}")
def home_index():
    return render_template(WEBSITE_INDEX)


@app.route("/data/nodes.json")
def nodes_data():
    content = None

    try:
        nodes = manager.get_nodes()

        items = []
        for node in nodes:
            item = node.__dict__
            edges: List[NodeRelation] = item.get("edges", [])
            relations = []

            for edge in edges:
                if isinstance(edge, dict):
                    relation = edge
                else:
                    relation = edge.__dict__

                relations.append(relation)

            item["edges"] = relations
            items.append(item)

        content = jsonify(items)

    except Exception as ex:
        exc_type, exc_obj, exc_tb = sys.exc_info()

        _LOGGER.error(f"Failed to get nodes due to error: {ex} [Line:{exc_tb.tb_lineno}]")

    return content


app.run(host=SERVER_BIND,
        port=configuration.server_port,
        debug=configuration.is_debug,
        ssl_context=configuration.ssl_context)

