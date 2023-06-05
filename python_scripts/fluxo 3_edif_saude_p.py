"""
Model exported as python.
Name : SAUDE
Group : IBGE
With QGIS : 31605
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsExpression
import processing


class Saude(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterString('EntrecomaChaveOSM', 'Entre com a Chave OSM', optional=True, multiLine=False, defaultValue='amenity'))
        self.addParameter(QgsProcessingParameterString('EntrecomoValorOSM', 'Entre com o Valor OSM', optional=True, multiLine=False, defaultValue='hospital'))
        self.addParameter(QgsProcessingParameterVectorLayer('definaareadeinteresse2', 'Defina a área de interesse', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('entrecomacamadaderefernciadotipopontoasertestada', 'Entre com a camada de REFERÊNCIA do tipo PONTO a ser testada ', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterString('teste', 'Entre com o 2° Valor OSM', multiLine=False, defaultValue='clinic'))
        self.addParameter(QgsProcessingParameterFeatureSink('Saude_p', 'SAUDE_P', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(51, model_feedback)
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
            'URL': outputs['ConsultaPorTagsDoOsm']['OUTPUT_URL'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['BaixarDados'] = processing.run('native:filedownloader', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Consulta por TAGs do OSM (2)
        alg_params = {
            'EXTENT': parameters['definaareadeinteresse2'],
            'KEY': parameters['EntrecomaChaveOSM'],
            'SERVER': 'https://lz4.overpass-api.de/api/interpreter',
            'TIMEOUT': 25,
            'VALUE': parameters['teste']
        }
        outputs['ConsultaPorTagsDoOsm2'] = processing.run('quickosm:buildqueryextent', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Buffer (2)
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 0.000452,
            'END_CAP_STYLE': 0,
            'INPUT': parameters['entrecomacamadaderefernciadotipopontoasertestada'],
            'JOIN_STYLE': 0,
            'MITER_LIMIT': 2,
            'SEGMENTS': 16,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Buffer2'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Pontos
        alg_params = {
            'INPUT_1': outputs['BaixarDados']['OUTPUT'],
            'INPUT_2': QgsExpression('\'|layername=points\'').evaluate()
        }
        outputs['Pontos'] = processing.run('native:stringconcatenation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo Pt1
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'teste',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,
            'FORMULA': '\'Sim\'',
            'INPUT': outputs['Pontos']['CONCATENATION'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoPt1'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Baixar arquivo (2)
        alg_params = {
            'URL': outputs['ConsultaPorTagsDoOsm2']['OUTPUT_URL'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['BaixarArquivo2'] = processing.run('native:filedownloader', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Poligonos
        alg_params = {
            'INPUT_1': outputs['BaixarDados']['OUTPUT'],
            'INPUT_2': QgsExpression('\'|layername=multipolygons\'').evaluate()
        }
        outputs['Poligonos'] = processing.run('native:stringconcatenation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Pontos (2)
        alg_params = {
            'INPUT_1': outputs['BaixarArquivo2']['OUTPUT'],
            'INPUT_2': QgsExpression('\'|layername=points\'').evaluate()
        }
        outputs['Pontos2'] = processing.run('native:stringconcatenation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Poligonos (2)
        alg_params = {
            'INPUT_1': outputs['BaixarArquivo2']['OUTPUT'],
            'INPUT_2': QgsExpression('\'|layername=multipolygons\'').evaluate()
        }
        outputs['Poligonos2'] = processing.run('native:stringconcatenation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Fixar geometrias
        alg_params = {
            'INPUT': outputs['Poligonos']['CONCATENATION'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['FixarGeometrias'] = processing.run('native:fixgeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Fixar geometrias
        alg_params = {
            'INPUT': outputs['Poligonos2']['CONCATENATION'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['FixarGeometrias'] = processing.run('native:fixgeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Join_Polygon
        alg_params = {
            'CRS': 'ProjectCrs',
            'LAYERS': [outputs['FixarGeometrias']['OUTPUT'],outputs['FixarGeometrias']['OUTPUT']],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Join_polygon'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo Pt2
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'teste',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,
            'FORMULA': '\'Sim\'',
            'INPUT': outputs['Pontos2']['CONCATENATION'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoPt2'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # Multipartes para partes simples
        alg_params = {
            'INPUT': outputs['Join_polygon']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MultipartesParaPartesSimples'] = processing.run('native:multiparttosingleparts', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}

        # Join_Point
        alg_params = {
            'CRS': 'ProjectCrs',
            'LAYERS': [outputs['CalculadoraDeCampoPt1']['OUTPUT'],outputs['CalculadoraDeCampoPt2']['OUTPUT']],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Join_point'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(16)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo_OSM_ID
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'osm_id',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 1,
            'FORMULA': 'if(\"osm_id\" IS NULL,\"osm_way_id\",\"osm_id\")',
            'INPUT': outputs['MultipartesParaPartesSimples']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo_osm_id'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(17)
        if feedback.isCanceled():
            return {}

        # Descartar campo(s)
        alg_params = {
            'COLUMN': 'osm_way_id',
            'INPUT': outputs['CalculadoraDeCampo_osm_id']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DescartarCampos'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(18)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo_PT_INICIO
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'PontoInicio',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 1,
            'FORMULA': 'strpos(  \"other_tags\" , (\'\"name\"=>\"\'))+9',
            'INPUT': outputs['DescartarCampos']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo_pt_inicio'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(19)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo_NOME
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'nome_no_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,
            'FORMULA': '\"name\"',
            'INPUT': outputs['CalculadoraDeCampo_pt_inicio']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo_nome'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(20)
        if feedback.isCanceled():
            return {}

        # Dissolver
        alg_params = {
            'FIELD': 'nome_no_osm',
            'INPUT': outputs['CalculadoraDeCampo_nome']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Dissolver'] = processing.run('native:dissolve', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(21)
        if feedback.isCanceled():
            return {}

        # Buffer
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 1e-06,
            'END_CAP_STYLE': 0,
            'INPUT': outputs['Dissolver']['OUTPUT'],
            'JOIN_STYLE': 0,
            'MITER_LIMIT': 2,
            'SEGMENTS': 16,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Buffer'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(22)
        if feedback.isCanceled():
            return {}

        # Extrair por localização
        alg_params = {
            'INPUT': outputs['Join_point']['OUTPUT'],
            'INTERSECT': outputs['Buffer']['OUTPUT'],
            'PREDICATE': 2,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorLocalizao'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(23)
        if feedback.isCanceled():
            return {}

        # Recortar
        alg_params = {
            'INPUT': outputs['Dissolver']['OUTPUT'],
            'OVERLAY': parameters['definaareadeinteresse2'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Recortar'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(24)
        if feedback.isCanceled():
            return {}

        # Recortar (2)
        alg_params = {
            'INPUT': outputs['ExtrairPorLocalizao']['OUTPUT'],
            'OVERLAY': parameters['definaareadeinteresse2'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Recortar2'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(25)
        if feedback.isCanceled():
            return {}

        # Extrair por localização
        alg_params = {
            'INPUT': outputs['Recortar']['OUTPUT'],
            'INTERSECT': parameters['entrecomacamadaderefernciadotipopontoasertestada'],
            'PREDICATE': 2,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorLocalizao'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(26)
        if feedback.isCanceled():
            return {}

        # Unir atributos pela posição
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': parameters['entrecomacamadaderefernciadotipopontoasertestada'],
            'JOIN': outputs['Recortar']['OUTPUT'],
            'JOIN_FIELDS': None,
            'METHOD': 0,
            'PREDICATE': 0,
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['UnirAtributosPelaPosio'] = processing.run('qgis:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(27)
        if feedback.isCanceled():
            return {}

        # Extrair por localização
        alg_params = {
            'INPUT': outputs['Recortar2']['OUTPUT'],
            'INTERSECT': outputs['Buffer2']['OUTPUT'],
            'PREDICATE': 2,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorLocalizao'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(28)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo_PT_INICIO(2)
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'PontoInicio',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 1,
            'FORMULA': 'strpos(  \"other_tags\" , (\'\"name\"=>\"\'))+9',
            'INPUT': outputs['ExtrairPorLocalizao']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo_pt_inicio2'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(29)
        if feedback.isCanceled():
            return {}

        # Centroides
        alg_params = {
            'ALL_PARTS': False,
            'INPUT': outputs['ExtrairPorLocalizao']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Centroides'] = processing.run('native:centroids', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(30)
        if feedback.isCanceled():
            return {}

        # Descartar campo(s) (1)
        alg_params = {
            'COLUMN': 'PontoInicio',
            'INPUT': outputs['UnirAtributosPelaPosio']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DescartarCampos1'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(31)
        if feedback.isCanceled():
            return {}

        # Descartar campo(s) (2)
        alg_params = {
            'COLUMN': 'path',
            'INPUT': outputs['DescartarCampos1']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DescartarCampos2'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(32)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo_NOME(2)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'nome_no_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,
            'FORMULA': '\"name\"',
            'INPUT': outputs['CalculadoraDeCampo_pt_inicio2']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo_nome2'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(33)
        if feedback.isCanceled():
            return {}

        # Mesclar camadas vetoriais
        alg_params = {
            'CRS': 'ProjectCrs',
            'LAYERS': [outputs['CalculadoraDeCampo_nome2']['OUTPUT'],outputs['Centroides']['OUTPUT']],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MesclarCamadasVetoriais'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(34)
        if feedback.isCanceled():
            return {}

        # Descartar campo(s) (3)
        alg_params = {
            'COLUMN': 'layer',
            'INPUT': outputs['DescartarCampos2']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DescartarCampos3'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(35)
        if feedback.isCanceled():
            return {}

        # Descartar campo(s) (5)
        alg_params = {
            'COLUMN': 'other_tags',
            'INPUT': outputs['MesclarCamadasVetoriais']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DescartarCampos5'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(36)
        if feedback.isCanceled():
            return {}

        # Descartar campo(s) (4)
        alg_params = {
            'COLUMN': 'other_tags',
            'INPUT': outputs['DescartarCampos3']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DescartarCampos4'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(37)
        if feedback.isCanceled():
            return {}

        # Descartar campo(s) (6)
        alg_params = {
            'COLUMN': 'layer',
            'INPUT': outputs['DescartarCampos5']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DescartarCampos6'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(38)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo NOME_OSM (1)
        alg_params = {
            'FIELD_LENGTH': 5,
            'FIELD_NAME': 'nome_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,
            'FORMULA': 'if(  \"nome\"  IS NULL  AND  \"nome_no_osm\" IS NOT NULL,  \'Sim\' ,\'Não\')',
            'INPUT': outputs['DescartarCampos4']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoNome_osm1'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(39)
        if feedback.isCanceled():
            return {}

        # Descartar campo(s) (7)
        alg_params = {
            'COLUMN': 'path',
            'INPUT': outputs['DescartarCampos6']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DescartarCampos7'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(40)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo GEOM_OSM (1)
        alg_params = {
            'FIELD_LENGTH': 5,
            'FIELD_NAME': 'geometria_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,
            'FORMULA': '\'Não\'',
            'INPUT': outputs['CalculadoraDeCampoNome_osm1']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoGeom_osm1'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(41)
        if feedback.isCanceled():
            return {}

        # Descartar campo(s) (8)
        alg_params = {
            'COLUMN': 'PontoInicio',
            'INPUT': outputs['DescartarCampos7']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DescartarCampos8'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(42)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'nome',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 1,
            'FORMULA': 'if(  \"nome\"  IS NULL  AND  \"nome_no_osm\" IS NOT NULL,  \"nome_no_osm\" ,  if(  \"nome\"   IS NOT NULL, \"nome\" ,NULL))',
            'INPUT': outputs['CalculadoraDeCampoGeom_osm1']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(43)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo NOME_OSM (2)
        alg_params = {
            'FIELD_LENGTH': 5,
            'FIELD_NAME': 'nome_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,
            'FORMULA': 'if (\"nome_no_osm\" IS NOT NULL, \'Sim\',\'Não\')',
            'INPUT': outputs['DescartarCampos8']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoNome_osm2'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(44)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo GEOM_OSM (2)
        alg_params = {
            'FIELD_LENGTH': 5,
            'FIELD_NAME': 'geometria_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,
            'FORMULA': '\'Sim\'',
            'INPUT': outputs['CalculadoraDeCampoNome_osm2']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoGeom_osm2'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(45)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'nome',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,
            'FORMULA': '\"nome_no_osm\"',
            'INPUT': outputs['CalculadoraDeCampoGeom_osm2']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(46)
        if feedback.isCanceled():
            return {}

        # Mesclar camadas vetoriais
        alg_params = {
            'CRS': 'ProjectCrs',
            'LAYERS': [outputs['CalculadoraDeCampo']['OUTPUT'],outputs['CalculadoraDeCampo']['OUTPUT']],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MesclarCamadasVetoriais'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(47)
        if feedback.isCanceled():
            return {}

        # Descartar campo(s) (9)
        alg_params = {
            'COLUMN': 'path',
            'INPUT': outputs['MesclarCamadasVetoriais']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DescartarCampos9'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(48)
        if feedback.isCanceled():
            return {}

        # Descartar campo(s) (10)
        alg_params = {
            'COLUMN': 'layer',
            'INPUT': outputs['DescartarCampos9']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DescartarCampos10'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(49)
        if feedback.isCanceled():
            return {}

        # Descartar campo(s) (11)
        alg_params = {
            'COLUMN': 'teste',
            'INPUT': outputs['DescartarCampos10']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DescartarCampos11'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(50)
        if feedback.isCanceled():
            return {}

        # Editar campos
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '\"id\"','length': -1,'name': 'id','precision': 0,'type': 2},{'expression': '\"nome\"','length': 150,'name': 'nome','precision': -1,'type': 10},{'expression': '\"geometriaaproximada\"','length': -1,'name': 'geometriaaproximada','precision': 0,'type': 2},{'expression': '\"operacional\"','length': -1,'name': 'operacional','precision': 0,'type': 2},{'expression': '\"situacaofisica\"','length': -1,'name': 'situacaofisica','precision': 0,'type': 2},{'expression': '\"matconstr\"','length': -1,'name': 'matconstr','precision': 0,'type': 2},{'expression': '\"alturaaproximada\"','length': -1,'name': 'alturaaproximada','precision': -1,'type': 6},{'expression': '\"turistica\"','length': -1,'name': 'turistica','precision': 0,'type': 2},{'expression': '\"cultura\"','length': -1,'name': 'cultura','precision': 0,'type': 2},{'expression': '\"administracao\"','length': -1,'name': 'administracao','precision': 0,'type': 2},{'expression': '\"classeativecon\"','length': -1,'name': 'classeativecon','precision': 0,'type': 10},{'expression': '\"divisaoativecon\"','length': -1,'name': 'divisaoativecon','precision': 0,'type': 10},{'expression': '\"grupoativecon\"','length': -1,'name': 'grupoativecon','precision': 0,'type': 10},{'expression': '\"proprioadm\"','length': -1,'name': 'proprioadm','precision': 0,'type': 2},{'expression': '\"cep\"','length': 80,'name': 'cep','precision': -1,'type': 10},{'expression': '\"pais\"','length': 80,'name': 'pais','precision': -1,'type': 10},{'expression': '\"unidadefederacao\"','length': 2,'name': 'unidadefederacao','precision': -1,'type': 10},{'expression': '\"municipio\"','length': 80,'name': 'municipio','precision': -1,'type': 10},{'expression': '\"bairro\"','length': 80,'name': 'bairro','precision': -1,'type': 10},{'expression': '\"logradouro\"','length': 200,'name': 'logradouro','precision': -1,'type': 10},{'expression': '\"bloco\"','length': 80,'name': 'bloco','precision': -1,'type': 10},{'expression': '\"numerosequencial\"','length': -1,'name': 'numerosequencial','precision': 0,'type': 2},{'expression': '\"numerometrico\"','length': -1,'name': 'numerometrico','precision': 0,'type': 2},{'expression': '\"numeropavimentos\"','length': -1,'name': 'numeropavimentos','precision': 0,'type': 2},{'expression': '\"nivelatencao\"','length': -1,'name': 'nivelatencao','precision': 0,'type': 2},{'expression': '\"tx_comentario_producao\"','length': -1,'name': 'tx_comentario_producao','precision': -1,'type': 10},{'expression': '\"id_nomebngb\"','length': -1,'name': 'id_nomebngb','precision': 0,'type': 2},{'expression': '\"id_produtor\"','length': -1,'name': 'id_produtor','precision': 0,'type': 2},{'expression': '\"id_elementoprodutor\"','length': -1,'name': 'id_elementoprodutor','precision': 0,'type': 2},{'expression': '\"id_antigo\"','length': -1,'name': 'id_antigo','precision': 0,'type': 2},{'expression': '\"cd_situacao_do_objeto\"','length': 2,'name': 'cd_situacao_do_objeto','precision': -1,'type': 10},{'expression': '\"id_usuario\"','length': -1,'name': 'id_usuario','precision': 0,'type': 2},{'expression': '\"dt_atualizacao\"','length': -1,'name': 'dt_atualizacao','precision': -1,'type': 16},{'expression': '\"tx_geocodigo_municipio\"','length': -1,'name': 'tx_geocodigo_municipio','precision': -1,'type': 10},{'expression': '\"id_assentamento_precario\"','length': -1,'name': 'id_assentamento_precario','precision': 0,'type': 2},{'expression': '\"id_complexo_habitacional\"','length': -1,'name': 'id_complexo_habitacional','precision': 0,'type': 2},{'expression': '\"id_condominio\"','length': -1,'name': 'id_condominio','precision': 0,'type': 2},{'expression': '\"id_conjunto_habitacional\"','length': -1,'name': 'id_conjunto_habitacional','precision': 0,'type': 2},{'expression': '\"nomeabrev\"','length': 50,'name': 'nomeabrev','precision': -1,'type': 10},{'expression': '\"situacaonome\"','length': -1,'name': 'situacaonome','precision': 0,'type': 2},{'expression': '\"insumonome\"','length': -1,'name': 'insumonome','precision': -1,'type': 10},{'expression': '\"situacaoquantoaolimite\"','length': -1,'name': 'situacaoquantoaolimite','precision': 0,'type': 2},{'expression': '\"observacaong\"','length': -1,'name': 'observacaong','precision': -1,'type': 10},{'expression': '\"validacaobngb\"','length': 1,'name': 'validacaobngb','precision': -1,'type': 10},{'expression': '\"compatibilidadeng\"','length': -1,'name': 'compatibilidadeng','precision': -1,'type': 10},{'expression': '\"osm_id\"','length': 0,'name': 'osm_id','precision': 0,'type': 10},{'expression': '\"nome_no_osm\"','length': 255,'name': 'nome_no_osm','precision': 3,'type': 10},{'expression': '\"nome_osm\"','length': 5,'name': 'nome_osm','precision': 3,'type': 10},{'expression': '\"geometria_osm\"','length': 5,'name': 'geometria_osm','precision': 3,'type': 10}],
            'INPUT': outputs['DescartarCampos11']['OUTPUT'],
            'OUTPUT': parameters['Saude_p']
        }
        outputs['EditarCampos'] = processing.run('qgis:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Saude_p'] = outputs['EditarCampos']['OUTPUT']
        return results

    def name(self):
        return 'SAUDE'

    def displayName(self):
        return 'SAUDE'

    def group(self):
        return 'IBGE'

    def groupId(self):
        return 'IBGE'

    def createInstance(self):
        return Saude()
