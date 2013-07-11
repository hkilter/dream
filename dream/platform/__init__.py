import json
import traceback
import multiprocessing
import pydot

from flask import Flask, jsonify, redirect, url_for
from flask import request

from dream.simulation.LineGenerationJSON import main as simulate_line_json

app = Flask(__name__)
# Serve static file with no cache
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.route("/")
def front_page():
  return redirect(url_for('static', filename='index.html'))


@app.route("/positionGraph", methods=["POST", "OPTIONS"])
def positionGraph():
  """Uses graphviz to position nodes of the graph.
  """
  graph = pydot.Dot()

  for node in request.json['element'].itervalues():
    graph.add_node(pydot.Node(node['id']))
    for successor in node.get('successorList', []):
      graph.add_edge(pydot.Edge(node['id'], successor))

  new_graph = pydot.graph_from_dot_data(graph.create_dot())

  # calulate the ratio from the size of the bounding box
  ratio = new_graph.get_bb()
  origin_left, origin_top, max_left, max_top = [float(p) for p in
    new_graph.get_bb()[1:-1].split(',')]
  ratio_top = max_top - origin_top
  ratio_left = max_left - origin_left

  preference_dict = dict()
  for node in new_graph.get_nodes():
    # skip technical nodes
    if node.get_name() in ('graph', 'node', 'edge'):
      continue
    left, top = [float(p) for p in node.get_pos()[1:-1].split(",")]
    preference_dict[node.get_name()[1:-1]] = dict(
      top=1-(top/ratio_top),
      left=1-(left/ratio_left),)

  return jsonify(preference_dict)


@app.route("/runSimulation", methods=["POST", "OPTIONS"])
def runSimulation():
  parameter_dict = request.json['json']
  app.logger.debug("running with:\n%s" % (json.dumps(parameter_dict,
                                          sort_keys=True, indent=2)))

  try:
    timeout = int(parameter_dict['general']['processTimeout'])
  except (KeyError, ValueError, TypeError):
    timeout = 60

  queue = multiprocessing.Queue()
  process = multiprocessing.Process(
    target=_runSimulation,
    args=(parameter_dict, queue))
  process.start()
  process.join(timeout)
  if process.is_alive():
    # process still alive after timeout, terminate it
    process.terminate()
    process.join()
    return jsonify(dict(error='Timeout after %s seconds' % timeout))

  return jsonify(queue.get())

def _runSimulation(parameter_dict, queue):
  try:
    result = simulate_line_json(input_data=json.dumps(parameter_dict))
    queue.put(dict(success=json.loads(result)))
  except Exception, e:
    tb = traceback.format_exc()
    app.logger.error(tb)
    queue.put(dict(error=tb))


def main(*args):
  app.run(debug=True)

if __name__ == "__main__":
  main()
