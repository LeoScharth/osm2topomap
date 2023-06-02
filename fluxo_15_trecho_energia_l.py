"""
Model exported as python.
Name : Power Line
Group : IBGE
With QGIS : 31605
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsExpression
import processing


class PowerLine(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('Definaareadeinteresse', 'Defina a área de interesse', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterString('EntrecomaChaveOSM', 'Entre com a Chave OSM', multiLine=False, defaultValue='power'))
        self.addParameter(QgsProcessingParameterString('EntrecomoValorOSM', 'Entre com o Valor OSM', multiLine=False, defaultValue='line'))
        self.addParameter(QgsProcessingParameterVectorLayer('entrecomacamadaderefernciadotipolinhaasertestada', 'Entre com a camada de REFERÊNCIA do tipo LINHA a ser testada ', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('entrecomaporcentagemdeexcessomnima', 'Entre com a porcentagem de excesso (?) mínima', type=QgsProcessingParameterNumber.Double, minValue=0, maxValue=100, defaultValue=70))
        self.addParameter(QgsProcessingParameterFeatureSink('Add_trecho_energia_l', 'add_trecho_energia_l', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(18, model_feedback)
        results = {}
        outputs = {}

        # Consulta por TAGs do OSM
        alg_params = {
            'EXTENT': parameters['Definaareadeinteresse'],
            'KEY': parameters['EntrecomaChaveOSM'],
            'SERVER': 'https://lz4.overpass-api.de/api/interpreter',
            'TIMEOUT': 25,
            'VALUE': parameters['EntrecomoValorOSM']
        }
        outputs['ConsultaPorTagsDoOsm'] = processing.run('quickosm:buildqueryextent', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Recortar
        alg_params = {
            'INPUT': parameters['entrecomacamadaderefernciadotipolinhaasertestada'],
            'OVERLAY': parameters['Definaareadeinteresse'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Recortar'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Baixar dados 
        alg_params = {
            'URL': outputs['ConsultaPorTagsDoOsm']['OUTPUT_URL'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['BaixarDados'] = processing.run('native:filedownloader', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Linhas
        alg_params = {
            'INPUT_1': outputs['BaixarDados']['OUTPUT'],
            'INPUT_2': QgsExpression('\'|layername=lines\'').evaluate()
        }
        outputs['Linhas'] = processing.run('native:stringconcatenation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Buffer_Referência
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 0.000452,
            'END_CAP_STYLE': 0,
            'INPUT': outputs['Recortar']['OUTPUT'],
            'JOIN_STYLE': 0,
            'MITER_LIMIT': 2,
            'SEGMENTS': 16,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Buffer_referncia'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Linhas com quebra
        alg_params = {
            'INPUT': outputs['Linhas']['CONCATENATION'],
            'LINES': outputs['Linhas']['CONCATENATION'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['LinhasComQuebra'] = processing.run('native:splitwithlines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Recorte conforme área de interesse_linhas
        alg_params = {
            'INPUT': outputs['LinhasComQuebra']['OUTPUT'],
            'OVERLAY': parameters['Definaareadeinteresse'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RecorteConformeReaDeInteresse_linhas'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Buffer_OSM
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 0.000452,
            'END_CAP_STYLE': 0,
            'INPUT': outputs['RecorteConformeReaDeInteresse_linhas']['OUTPUT'],
            'JOIN_STYLE': 0,
            'MITER_LIMIT': 2,
            'SEGMENTS': 16,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Buffer_osm'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo_1
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'Area_TOT',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,
            'FORMULA': '$area',
            'INPUT': outputs['Buffer_osm']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo_1'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Diferença
        alg_params = {
            'INPUT': outputs['CalculadoraDeCampo_1']['OUTPUT'],
            'OVERLAY': outputs['Buffer_referncia']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Diferena'] = processing.run('native:difference', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo_2
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'Area_DIF',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,
            'FORMULA': '$area',
            'INPUT': outputs['Diferena']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo_2'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo_3
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'percentualExtraBaseRef',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,
            'FORMULA': '(\"Area_DIF\" *100)/ \"Area_TOT\"',
            'INPUT': outputs['CalculadoraDeCampo_2']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo_3'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Selecionar por atributo
        alg_params = {
            'FIELD': 'percentualExtraBaseRef',
            'INPUT': outputs['CalculadoraDeCampo_3']['OUTPUT'],
            'METHOD': 0,
            'OPERATOR': 3,
            'VALUE': parameters['entrecomaporcentagemdeexcessomnima']
        }
        outputs['SelecionarPorAtributo'] = processing.run('qgis:selectbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # Extrair feições selecionadas
        alg_params = {
            'INPUT': outputs['SelecionarPorAtributo']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairFeiesSelecionadas'] = processing.run('native:saveselectedfeatures', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # Unir atributos pelo valor do campo
        alg_params = {
            'DISCARD_NONMATCHING': True,
            'FIELD': 'osm_id',
            'FIELDS_TO_COPY': None,
            'FIELD_2': 'osm_id',
            'INPUT': outputs['RecorteConformeReaDeInteresse_linhas']['OUTPUT'],
            'INPUT_2': outputs['ExtrairFeiesSelecionadas']['OUTPUT'],
            'METHOD': 1,
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['UnirAtributosPeloValorDoCampo'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo (1)
        alg_params = {
            'FIELD_LENGTH': 5,
            'FIELD_NAME': 'PontoInicio',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,
            'FORMULA': 'strpos(  \"other_tags\" , (\'\"description\"=>\"\'))+16',
            'INPUT': outputs['UnirAtributosPeloValorDoCampo']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo1'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(16)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo (2)
        alg_params = {
            'FIELD_LENGTH': 25,
            'FIELD_NAME': 'description',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,
            'FORMULA': 'if(  \"PontoInicio\" = \'16\' , \"\", substr(  \"other_tags\" ,\"PontoInicio\" ,   strpos(  substr(  \"other_tags\" ,\"PontoInicio\" ), \'\"\')-1))',
            'INPUT': outputs['CalculadoraDeCampo1']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo2'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(17)
        if feedback.isCanceled():
            return {}

        # Editar campos
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '\"osm_id\"','length': 10,'name': 'osm_id','precision': 0,'type': 10},{'expression': '\"description\"','length': 255,'name': 'nome','precision': 0,'type': 10},{'expression': '\'Sim\'','length': 5,'name': 'geometria_osm','precision': 0,'type': 10},{'expression': 'if(\"description\" IS NOT NULL,\'Sim\',\'Não\')','length': 5,'name': 'nome_osm','precision': 0,'type': 10}],
            'INPUT': outputs['CalculadoraDeCampo2']['OUTPUT'],
            'OUTPUT': parameters['Add_trecho_energia_l']
        }
        outputs['EditarCampos'] = processing.run('qgis:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Add_trecho_energia_l'] = outputs['EditarCampos']['OUTPUT']
        return results

    def name(self):
        return 'Power Line'

    def displayName(self):
        return 'Power Line'

    def group(self):
        return 'IBGE'

    def groupId(self):
        return 'IBGE'

    def createInstance(self):
        return PowerLine()
