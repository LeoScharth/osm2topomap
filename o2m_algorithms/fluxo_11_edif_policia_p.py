"""
Model exported as python.
Name : Policia
Group : IBGE
With QGIS : 33200
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsExpression
import processing


class Policia(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterString('EntrecomaChaveOSM', 'Entre com a Chave OSM', optional=True, multiLine=False, defaultValue='amenity'))
        self.addParameter(QgsProcessingParameterString('EntrecomoValorOSM', 'Entre com o Valor OSM', optional=True, multiLine=False, defaultValue='police'))
        self.addParameter(QgsProcessingParameterVectorLayer('definaareadeinteresse2', 'Defina a área de interesse', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Policia_p', 'Policia_p', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(13, model_feedback)
        results = {}
        outputs = {}

        # Consulta por TAGs do OSM
        alg_params = {
            'EXTENT': parameters['definaareadeinteresse2'],
            'KEY': parameters['EntrecomaChaveOSM'],
            'SERVER': 'https://lz4.overpass-api.de/api/interpreter',
            'TIMEOUT': 25,
            'VALUE': parameters['EntrecomoValorOSM']
        }
        outputs['ConsultaPorTagsDoOsm'] = processing.run('quickosm:buildqueryextent', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Baixar dados 
        alg_params = {
            'DATA': '',
            'METHOD': 0,  # GET
            'URL': outputs['ConsultaPorTagsDoOsm']['OUTPUT_URL'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['BaixarDados'] = processing.run('native:filedownloader', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Pontos
        alg_params = {
            'INPUT_1': outputs['BaixarDados']['OUTPUT'],
            'INPUT_2': QgsExpression("'|layername=points'").evaluate()
        }
        outputs['Pontos'] = processing.run('native:stringconcatenation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Poligonos
        alg_params = {
            'INPUT_1': outputs['BaixarDados']['OUTPUT'],
            'INPUT_2': QgsExpression("'|layername=multipolygons'").evaluate()
        }
        outputs['Poligonos'] = processing.run('native:stringconcatenation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Recortar (2)
        alg_params = {
            'INPUT': outputs['Pontos']['CONCATENATION'],
            'OVERLAY': parameters['definaareadeinteresse2'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Recortar2'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Fixar geometrias
        alg_params = {
            'INPUT': outputs['Poligonos']['CONCATENATION'],
            'METHOD': 1,  # Structure
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['FixarGeometrias'] = processing.run('native:fixgeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Recortar
        alg_params = {
            'INPUT': outputs['FixarGeometrias']['OUTPUT'],
            'OVERLAY': parameters['definaareadeinteresse2'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Recortar'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Buffer
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 1e-06,
            'END_CAP_STYLE': 0,  # Round
            'INPUT': outputs['Recortar']['OUTPUT'],
            'JOIN_STYLE': 0,  # Round
            'MITER_LIMIT': 2,
            'SEGMENTS': 16,
            'SEPARATE_DISJOINT': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Buffer'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Centroides
        alg_params = {
            'ALL_PARTS': False,
            'INPUT': outputs['Recortar']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Centroides'] = processing.run('native:centroids', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Extrair por localização
        alg_params = {
            'INPUT': outputs['Recortar2']['OUTPUT'],
            'INTERSECT': outputs['Buffer']['OUTPUT'],
            'PREDICATE': 2,  # disjoint
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorLocalizao'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'osm_id',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': 'if("osm_id" IS NULL,"osm_way_id","osm_id")',
            'INPUT': outputs['Centroides']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Mesclar camadas vetoriais
        alg_params = {
            'CRS': 'ProjectCrs',
            'LAYERS': [outputs['CalculadoraDeCampo']['OUTPUT'],outputs['ExtrairPorLocalizao']['OUTPUT']],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MesclarCamadasVetoriais'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Editar campos
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '"name"','length': 255,'name': 'nome','precision': 0,'type': 10},{'expression': '"osm_id"','length': 10,'name': 'osm_id','precision': 0,'type': 10},{'expression': '"name"','length': 255,'name': 'nome_no_osm','precision': 0,'type': 10},{'expression': "'Sim'",'length': 5,'name': 'geometria_osm','precision': 0,'type': 10},{'expression': 'if("name" IS NOT NULL,\'Sim\',\'Não\')','length': 5,'name': 'nome_osm','precision': 0,'type': 10}],
            'INPUT': outputs['MesclarCamadasVetoriais']['OUTPUT'],
            'OUTPUT': parameters['Policia_p']
        }
        outputs['EditarCampos'] = processing.run('qgis:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Policia_p'] = outputs['EditarCampos']['OUTPUT']
        return results

    def name(self):
        return 'Policia'

    def displayName(self):
        return 'Policia'

    def group(self):
        return 'IBGE'

    def groupId(self):
        return 'IBGE'

    def createInstance(self):
        return Policia()
