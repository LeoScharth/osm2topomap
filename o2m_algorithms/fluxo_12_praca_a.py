"""
Model exported as python.
Name : Praca
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


class Praca(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterString('EntrecomaChaveOSM', 'Entre com a Chave OSM', multiLine=False, defaultValue='leisure'))
        self.addParameter(QgsProcessingParameterString('EntrecomoValorOSM', 'Entre com o Valor OSM', multiLine=False, defaultValue='park'))
        self.addParameter(QgsProcessingParameterVectorLayer('definaareadeinteresse2', 'Defina a área de interesse', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Geom', 'geom', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Praa_a', 'praca_A', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(8, model_feedback)
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

        # Polígonos
        alg_params = {
            'INPUT_1': outputs['BaixarDados']['OUTPUT'],
            'INPUT_2': QgsExpression("'|layername=multipolygons'").evaluate()
        }
        outputs['Polgonos'] = processing.run('native:stringconcatenation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Fixar geometrias
        alg_params = {
            'INPUT': outputs['Polgonos']['CONCATENATION'],
            'METHOD': 1,  # Structure
            'OUTPUT': parameters['Geom']
        }
        outputs['FixarGeometrias'] = processing.run('native:fixgeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Geom'] = outputs['FixarGeometrias']['OUTPUT']

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Recortar (2)
        alg_params = {
            'INPUT': outputs['FixarGeometrias']['OUTPUT'],
            'OVERLAY': parameters['definaareadeinteresse2'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Recortar2'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Multipartes para partes simples
        alg_params = {
            'INPUT': outputs['Recortar2']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MultipartesParaPartesSimples'] = processing.run('native:multiparttosingleparts', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Extrair por expressão
        alg_params = {
            'EXPRESSION': '"name" LIKE \'%Praca%\' OR "name" LIKE \'%Praca%\' OR "name" LIKE \'%praca%\' OR "name" LIKE \'%praca%\' OR "name" LIKE \'%PRAcA%\' OR "name" LIKE \'%PRACA%\' OR "name" LIKE \'%Pracinha%\' OR "name" LIKE \'%pracinha%\' OR "name" LIKE \'%Largo%\' OR "name" LIKE \'%largo%\' OR "name" LIKE \'%LARGO%\' OR "name" LIKE \'%Parquinho%\' OR "name" LIKE \'%parquinho%\' OR "name" LIKE \'%PARQUINHO%\'',
            'INPUT': outputs['MultipartesParaPartesSimples']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorExpresso'] = processing.run('native:extractbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Editar campos
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '"name"','length': 255,'name': 'nome','precision': 0,'type': 10},{'expression': "'Sim'",'length': 5,'name': 'geometriaAproximada','precision': 0,'type': 10},{'expression': 'if("tourism" IS NOT NULL, \'Sim\', \'Não\')','length': 5,'name': 'turistica','precision': 0,'type': 10},{'expression': 'if("osm_id" IS NULL,"osm_way_id","osm_id")','length': 10,'name': 'osm_id','precision': 0,'type': 10},{'expression': '"name"','length': 255,'name': 'nome_no_osm','precision': 0,'type': 10},{'expression': "'Sim'",'length': 5,'name': 'geometria_osm','precision': 0,'type': 10},{'expression': 'if("name" IS NOT NULL,\'Sim\',\'Não\')','length': 5,'name': 'nome_osm','precision': 0,'type': 10}],
            'INPUT': outputs['ExtrairPorExpresso']['OUTPUT'],
            'OUTPUT': parameters['Praa_a']
        }
        outputs['EditarCampos'] = processing.run('qgis:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Praa_a'] = outputs['EditarCampos']['OUTPUT']
        return results

    def name(self):
        return 'Praca'

    def displayName(self):
        return 'Praca'

    def group(self):
        return 'IBGE'

    def groupId(self):
        return 'IBGE'

    def createInstance(self):
        return Praca()
