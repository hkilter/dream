from copy import deepcopy
import json
import numpy

from zope.dottedname.resolve import resolve

from dream.simulation.LineGenerationJSON import main as simulate_line_json

class Plugin(object):
  """Base class for pre-post processing Plugin.
  """
  def __init__(self, logger, configuration_dict):
    self.logger = logger
    self.configuration_dict = configuration_dict
    
  # returns the predecessors of a node
  def getPredecessors(self, data, node_id):
    predecessors=[]
    from copy import copy    
    edges=copy(data['graph']['edge'])
    for edge_id,edge in edges.iteritems():
        if edge['destination']==node_id:
            predecessors.append(edge['source'])
    return predecessors

  # returns the successors of a node
  def getSuccessors(self, data, node_id):
    successors=[]
    from copy import copy    
    edges=copy(data['graph']['edge'])
    for edge_id,edge in edges.iteritems():
        if edge['source']==node_id:
            successors.append(edge['destination'])
    return successors

  # calcualted the confidence inteval for a list and a confidence level
  def getConfidenceInterval(self, value_list, confidenceLevel):
    from dream.KnowledgeExtraction.ConfidenceIntervals import Intervals
    from dream.KnowledgeExtraction.StatisticalMeasures import BasicStatisticalMeasures
    BSM=BasicStatisticalMeasures()
    lb, ub = Intervals().ConfidIntervals(value_list, confidenceLevel)
    return {'lb': lb,
            'ub': ub,
            'avg': BSM.mean(value_list) 
        }
    
  # return the average of a list    
  def getAverage(self, value_list):
    return sum(value_list) / float(len(value_list))
  
  # return the standard deviation of a list                                      
  def getStDev(self, value_list):
    return numpy.std(value_list)

  # returns name of a node given its id
  def getNameFromId(self, data, node_id):
      return data['graph']['node'][node_id]['name']

class ExecutionPlugin(Plugin):
  """Plugin to handle the execution of multiple simulation runs.
  """
  def runOneScenario(self, data):
    """default method for running one scenario
    """
    return json.loads(simulate_line_json(input_data=json.dumps(data)))

  def run(self, data):
    """General execution plugin.
    """
    raise NotImplementedError

class InputPreparationPlugin(Plugin):
  def preprocess(self, data):
    """Preprocess the data before simulation run.
    """
    return data

  # adds an edge with the given source and destination
  def addEdge(self, data, source, destination, nodeData={}):
    data['graph']['edge'][source+'_to_'+destination]={
        "source": source, 
        "destination": destination, 
        "data": {}, 
        "_class": "Dream.Edge"             
    }
    return data

class OutputPreparationPlugin(Plugin):
  def postprocess(self, data):
    """Postprocess the data after simulation run.
    """
    return data

class DefaultExecutionPlugin(ExecutionPlugin):
  """Default Execution Plugin just executes one scenario.
  """
  def run(self, data):
    """Run simulation and return result to the GUI.
    """
    data["result"]["result_list"] = self.runOneScenario(data)['result']['result_list']
    data["result"]["result_list"][-1]["score"] = 0
    data["result"]["result_list"][-1]["key"] = "default"
    return data

class NewOrderExecutionPlugin(ExecutionPlugin):
  """ Execution plugin that compares the result with or with the new order.
  
  The new order is identified must have "new" in its id.
  """
  def removeNewOrder(self, data):
    data = deepcopy(data)
    data['input']['BOM']['productionOrders'] = [order for order in 
      data['input']['BOM']['productionOrders'] if not "new" in order['id'].lower()]
    for node in data['graph']['node'].values():
      if node.get('wip'):
        node['wip'] = [part for part in node['wip'] if not "new" in part['capacityProjectId'].lower()]
    return data

  def run(self, data):
    """Run simulation and return result to the GUI.
    """
    # before new order
    data["result"]["result_list"].extend(self.runOneScenario(self.removeNewOrder(data))['result']['result_list'])
    data["result"]["result_list"][-1]["score"] = 0
    data["result"]["result_list"][-1]["key"] = "before_new_order"
    data["result"]["result_list"][-1]["name"] = "Before New Order"

    if [order for order in data['input']['BOM']['productionOrders'] if "new" in order['id'].lower()]:
      # with the new order
      data["result"]["result_list"].extend(self.runOneScenario(data)['result']['result_list'])
      data["result"]["result_list"][-1]["score"] = 0
      data["result"]["result_list"][-1]["key"] = "with_new_order"
      data["result"]["result_list"][-1]["name"] = "With New Order"
    return data


class PluginRegistry(object):
  """Registry of plugins.
  """
  def __init__(self, logger, data):

    self.input_preparation_list = []
    for plugin_data in data['application_configuration']['pre_processing']['plugin_list']:
      self.input_preparation_list.append(resolve(plugin_data['_class'])(logger, plugin_data))

    self.output_preparation_list = []
    for plugin_data in data['application_configuration']['post_processing']['plugin_list']:
      self.output_preparation_list.append(resolve(plugin_data['_class'])(logger, plugin_data))

    plugin_data = data['application_configuration']['processing_plugin']
    self.execution_plugin = resolve(plugin_data['_class'])(logger, plugin_data)

  def run(self, data):
    """Preprocess, execute & postprocess.
    """
    for input_preparation in self.input_preparation_list:
        data = input_preparation.preprocess(deepcopy(data))

    outputJSONString=json.dumps(data, indent=5)
    outputJSONFile=open('sentToManPy.json', mode='w')
    outputJSONFile.write(outputJSONString)
      
    data = self.execution_plugin.run(data)

    for output_preparation in self.output_preparation_list:
        data = output_preparation.postprocess(deepcopy(data))

    return data
