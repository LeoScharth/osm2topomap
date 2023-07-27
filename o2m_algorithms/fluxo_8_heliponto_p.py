"""
Model exported as python.
Name : Heliponto
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


class Heliponto(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterString('EntrecomaChaveOSM', 'Entre com a Chave OSM', optional=True, multiLine=False, defaultValue='aeroway'))
        self.addParameter(QgsProcessingParameterString('EntrecomoValorOSM', 'Entre com o Valor OSM', optional=True, multiLine=False, defaultValue='helipad'))
        self.addParameter(QgsProcessingParameterVectorLayer('definaareadeinteresse2', 'Defina a área de interesse', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('entrecomacamadaderefernciadotipopontoasertestada', 'Entre com a camada de REFERÊNCIA do tipo PONTO a ser testada ', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Heliponto_p', 'Heliponto_P', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(30, model_feedback)
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

        # Buffer (2)
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 0.000452,
            'END_CAP_STYLE': 0,  # Round
            'INPUT': parameters['entrecomacamadaderefernciadotipopontoasertestada'],
            'JOIN_STYLE': 0,  # Round
            'MITER_LIMIT': 2,
            'SEGMENTS': 16,
            'SEPARATE_DISJOINT': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Buffer2'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
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

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Pontos
        alg_params = {
            'INPUT_1': outputs['BaixarDados']['OUTPUT'],
            'INPUT_2': QgsExpression("'|layername=points'").evaluate()
        }
        outputs['Pontos'] = processing.run('native:stringconcatenation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Poligonos
        alg_params = {
            'INPUT_1': outputs['BaixarDados']['OUTPUT'],
            'INPUT_2': QgsExpression("'|layername=multipolygons'").evaluate()
        }
        outputs['Poligonos'] = processing.run('native:stringconcatenation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Recortar (2)
        alg_params = {
            'INPUT': outputs['Pontos']['CONCATENATION'],
            'OVERLAY': parameters['definaareadeinteresse2'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Recortar2'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Extrair por localização
        alg_params = {
            'INPUT': outputs['Recortar2']['OUTPUT'],
            'INTERSECT': outputs['Buffer2']['OUTPUT'],
            'PREDICATE': 2,  # disjoint
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorLocalizao'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Recortar
        alg_params = {
            'INPUT': outputs['Poligonos']['CONCATENATION'],
            'OVERLAY': parameters['definaareadeinteresse2'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Recortar'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Buffer
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 0.000452,
            'END_CAP_STYLE': 0,  # Round
            'INPUT': outputs['Recortar']['OUTPUT'],
            'JOIN_STYLE': 0,  # Round
            'MITER_LIMIT': 2,
            'SEGMENTS': 5,
            'SEPARATE_DISJOINT': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Buffer'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Extrair por localização
        alg_params = {
            'INPUT': outputs['Recortar']['OUTPUT'],
            'INTERSECT': outputs['Buffer2']['OUTPUT'],
            'PREDICATE': 2,  # disjoint
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorLocalizao'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Unir atributos pela posição
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': parameters['entrecomacamadaderefernciadotipopontoasertestada'],
            'JOIN': outputs['Buffer']['OUTPUT'],
            'JOIN_FIELDS': '',
            'METHOD': 1,  # Take attributes of the first matching feature only (one-to-one)
            'PREDICATE': 0,  # intersect
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['UnirAtributosPelaPosio'] = processing.run('qgis:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo (5)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'nome',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': '"name"',
            'INPUT': outputs['UnirAtributosPelaPosio']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo5'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Centroides
        alg_params = {
            'ALL_PARTS': False,
            'INPUT': outputs['ExtrairPorLocalizao']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Centroides'] = processing.run('native:centroids', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo (6)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'nome_no_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': '"name"',
            'INPUT': outputs['CalculadoraDeCampo5']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo6'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'osm_id',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': '"osm_way_id"',
            'INPUT': outputs['CalculadoraDeCampo6']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'osm_id',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': '"osm_way_id"',
            'INPUT': outputs['Centroides']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(16)
        if feedback.isCanceled():
            return {}

        # Mesclar camadas vetoriais
        alg_params = {
            'CRS': None,
            'LAYERS': [outputs['CalculadoraDeCampo']['OUTPUT'],outputs['ExtrairPorLocalizao']['OUTPUT']],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MesclarCamadasVetoriais'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(17)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo
        alg_params = {
            'FIELD_LENGTH': 5,
            'FIELD_NAME': 'geometria_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': "'Não'",
            'INPUT': outputs['CalculadoraDeCampo']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(18)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo_PT_INICIO(2)
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'PontoInicio',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 1,  # Integer (32 bit)
            'FORMULA': 'strpos(  "other_tags" , (\'"name"=>"\'))+9',
            'INPUT': outputs['MesclarCamadasVetoriais']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo_pt_inicio2'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(19)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo
        alg_params = {
            'FIELD_LENGTH': 5,
            'FIELD_NAME': 'nome_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': 'if( "nome_no_osm" IS NOT NULL,  \'Sim\' ,\'Não\')',
            'INPUT': outputs['CalculadoraDeCampo']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(20)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo_NOME(2)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'nome_no_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': '"name"',
            'INPUT': outputs['CalculadoraDeCampo_pt_inicio2']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo_nome2'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(21)
        if feedback.isCanceled():
            return {}

        # Descartar campo(s) (1)
        alg_params = {
            'COLUMN': 'PontoInicio',
            'INPUT': outputs['CalculadoraDeCampo_nome2']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DescartarCampos1'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(22)
        if feedback.isCanceled():
            return {}

        # Descartar campo(s) (2)
        alg_params = {
            'COLUMN': 'path',
            'INPUT': outputs['DescartarCampos1']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DescartarCampos2'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(23)
        if feedback.isCanceled():
            return {}

        # Descartar campo(s) (3)
        alg_params = {
            'COLUMN': 'layer',
            'INPUT': outputs['DescartarCampos2']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DescartarCampos3'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(24)
        if feedback.isCanceled():
            return {}

        # Descartar campo(s) (4)
        alg_params = {
            'COLUMN': 'other_tags',
            'INPUT': outputs['DescartarCampos3']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DescartarCampos4'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(25)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo NOME_OSM (1)
        alg_params = {
            'FIELD_LENGTH': 5,
            'FIELD_NAME': 'nome_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': 'if( "nome_no_osm" IS NOT NULL,  \'Sim\' ,\'Não\')',
            'INPUT': outputs['DescartarCampos4']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoNome_osm1'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(26)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo GEOM_OSM (1)
        alg_params = {
            'FIELD_LENGTH': 5,
            'FIELD_NAME': 'geometria_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': "'Sim'",
            'INPUT': outputs['CalculadoraDeCampoNome_osm1']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoGeom_osm1'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(27)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'nome',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': '"nome_no_osm"',
            'INPUT': outputs['CalculadoraDeCampoGeom_osm1']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(28)
        if feedback.isCanceled():
            return {}

        # Mesclar camadas vetoriais
        alg_params = {
            'CRS': 'ProjectCrs',
            'LAYERS': [outputs['CalculadoraDeCampo']['OUTPUT'],outputs['CalculadoraDeCampo']['OUTPUT']],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MesclarCamadasVetoriais'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(29)
        if feedback.isCanceled():
            return {}

        # Editar campos
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '"id"','length': -1,'name': 'id','precision': 0,'type': 2},{'expression': '"nome"','length': 150,'name': 'nome','precision': -1,'type': 10},{'expression': '"geometriaaproximada"','length': -1,'name': 'geometriaaproximada','precision': 0,'type': 2},{'expression': "'Heliponto'",'length': 15,'name': 'tipopista','precision': 0,'type': 10},{'expression': '"revestimento"','length': -1,'name': 'revestimento','precision': 0,'type': 2},{'expression': '"usopista"','length': -1,'name': 'usopista','precision': 0,'type': 2},{'expression': '"homologacao"','length': -1,'name': 'homologacao','precision': 0,'type': 2},{'expression': '"operacional"','length': -1,'name': 'operacional','precision': 0,'type': 2},{'expression': '"situacaofisica"','length': -1,'name': 'situacaofisica','precision': 0,'type': 2},{'expression': '"largura"','length': -1,'name': 'largura','precision': -1,'type': 6},{'expression': '"extensao"','length': -1,'name': 'extensao','precision': -1,'type': 6},{'expression': '"altitude"','length': -1,'name': 'altitude','precision': -1,'type': 6},{'expression': '"tx_comentario_producao"','length': -1,'name': 'tx_comentario_producao','precision': -1,'type': 10},{'expression': '"id_nomebngb"','length': -1,'name': 'id_nomebngb','precision': 0,'type': 2},{'expression': '"id_produtor"','length': -1,'name': 'id_produtor','precision': 0,'type': 2},{'expression': '"id_elementoprodutor"','length': -1,'name': 'id_elementoprodutor','precision': 0,'type': 2},{'expression': '"id_antigo"','length': -1,'name': 'id_antigo','precision': 0,'type': 2},{'expression': '"cd_situacao_do_objeto"','length': 2,'name': 'cd_situacao_do_objeto','precision': -1,'type': 10},{'expression': '"id_usuario"','length': -1,'name': 'id_usuario','precision': 0,'type': 2},{'expression': '"dt_atualizacao"','length': -1,'name': 'dt_atualizacao','precision': -1,'type': 16},{'expression': '"tx_geocodigo_municipio"','length': -1,'name': 'tx_geocodigo_municipio','precision': -1,'type': 10},{'expression': '"id_complexo_aeroportuario"','length': -1,'name': 'id_complexo_aeroportuario','precision': 0,'type': 2},{'expression': '"situacaonome"','length': -1,'name': 'situacaonome','precision': 0,'type': 2},{'expression': '"insumonome"','length': -1,'name': 'insumonome','precision': -1,'type': 10},{'expression': '"situacaoquantoaolimite"','length': -1,'name': 'situacaoquantoaolimite','precision': 0,'type': 2},{'expression': '"observacaong"','length': -1,'name': 'observacaong','precision': -1,'type': 10},{'expression': '"validacaobngb"','length': 1,'name': 'validacaobngb','precision': -1,'type': 10},{'expression': '"compatibilidadeng"','length': -1,'name': 'compatibilidadeng','precision': -1,'type': 10},{'expression': '"osm_id"','length': 0,'name': 'osm_id','precision': 0,'type': 10},{'expression': '"nome_no_osm"','length': 255,'name': 'nome_no_osm','precision': 3,'type': 10},{'expression': '"geometria_osm"','length': 5,'name': 'geometria_osm','precision': 3,'type': 10},{'expression': '"nome_osm"','length': 5,'name': 'nome_osm','precision': 3,'type': 10}],
            'INPUT': outputs['MesclarCamadasVetoriais']['OUTPUT'],
            'OUTPUT': parameters['Heliponto_p']
        }
        outputs['EditarCampos'] = processing.run('qgis:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Heliponto_p'] = outputs['EditarCampos']['OUTPUT']
        return results

    def name(self):
        return 'Heliponto'

    def displayName(self):
        return 'Heliponto'

    def group(self):
        return 'IBGE'

    def groupId(self):
        return 'IBGE'

    def createInstance(self):
        return Heliponto()
