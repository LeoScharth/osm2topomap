"""
Model exported as python.
Name : Policia_Rodoviaria
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


class Policia_rodoviaria(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterString('EntrecomaChaveOSM', 'Entre com a Chave OSM', optional=True, multiLine=False, defaultValue='police'))
        self.addParameter(QgsProcessingParameterString('EntrecomoValorOSM', 'Entre com o Valor OSM', optional=True, multiLine=False, defaultValue='traffic_police'))
        self.addParameter(QgsProcessingParameterVectorLayer('definaareadeinteresse2', 'Defina a área de interesse', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('entrecomacamadaderefernciadotipopontoasertestada', 'Entre com a camada de REFERÊNCIA do tipo PONTO a ser testada ', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Pol_rod_p', 'Pol_rod_P', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(19, model_feedback)
        results = {}
        outputs = {}

        # Calculadora de campo
        alg_params = {
            'FIELD_LENGTH': 5,
            'FIELD_NAME': 'geometria_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': "'Não'",
            'INPUT': parameters['entrecomacamadaderefernciadotipopontoasertestada'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Consulta por TAGs do OSM
        alg_params = {
            'EXTENT': parameters['definaareadeinteresse2'],
            'KEY': parameters['EntrecomaChaveOSM'],
            'SERVER': 'https://lz4.overpass-api.de/api/interpreter',
            'TIMEOUT': 25,
            'VALUE': parameters['EntrecomoValorOSM']
        }
        outputs['ConsultaPorTagsDoOsm'] = processing.run('quickosm:buildqueryextent', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
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

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo
        alg_params = {
            'FIELD_LENGTH': 5,
            'FIELD_NAME': 'nome_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': "'Não'",
            'INPUT': outputs['CalculadoraDeCampo']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
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

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Pontos
        alg_params = {
            'INPUT_1': outputs['BaixarDados']['OUTPUT'],
            'INPUT_2': QgsExpression("'|layername=points'").evaluate()
        }
        outputs['Pontos'] = processing.run('native:stringconcatenation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Recortar (2)
        alg_params = {
            'INPUT': outputs['Pontos']['CONCATENATION'],
            'OVERLAY': parameters['definaareadeinteresse2'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Recortar2'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
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

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo_PT_INICIO(2)
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'PontoInicio',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 1,  # Integer (32 bit)
            'FORMULA': 'strpos(  "other_tags" , (\'"name"=>"\'))+9',
            'INPUT': outputs['ExtrairPorLocalizao']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo_pt_inicio2'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
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

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Descartar campo(s) (1)
        alg_params = {
            'COLUMN': 'PontoInicio',
            'INPUT': outputs['CalculadoraDeCampo_nome2']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DescartarCampos1'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Descartar campo(s) (2)
        alg_params = {
            'COLUMN': 'path',
            'INPUT': outputs['DescartarCampos1']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DescartarCampos2'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Descartar campo(s) (3)
        alg_params = {
            'COLUMN': 'layer',
            'INPUT': outputs['DescartarCampos2']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DescartarCampos3'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # Descartar campo(s) (4)
        alg_params = {
            'COLUMN': 'other_tags',
            'INPUT': outputs['DescartarCampos3']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DescartarCampos4'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(14)
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

        feedback.setCurrentStep(15)
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

        feedback.setCurrentStep(16)
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

        feedback.setCurrentStep(17)
        if feedback.isCanceled():
            return {}

        # Mesclar camadas vetoriais
        alg_params = {
            'CRS': 'ProjectCrs',
            'LAYERS': [outputs['CalculadoraDeCampo']['OUTPUT'],outputs['CalculadoraDeCampo']['OUTPUT']],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MesclarCamadasVetoriais'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(18)
        if feedback.isCanceled():
            return {}

        # Editar campos
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '"id"','length': -1,'name': 'id','precision': 0,'type': 2},{'expression': '"nome"','length': 150,'name': 'nome','precision': -1,'type': 10},{'expression': '"geometriaaproximada"','length': -1,'name': 'geometriaaproximada','precision': 0,'type': 2},{'expression': '"operacional"','length': -1,'name': 'operacional','precision': 0,'type': 2},{'expression': '"situacaofisica"','length': -1,'name': 'situacaofisica','precision': 0,'type': 2},{'expression': '"matconstr"','length': -1,'name': 'matconstr','precision': 0,'type': 2},{'expression': '"alturaaproximada"','length': -1,'name': 'alturaaproximada','precision': -1,'type': 6},{'expression': '"turistica"','length': -1,'name': 'turistica','precision': 0,'type': 2},{'expression': '"cultura"','length': -1,'name': 'cultura','precision': 0,'type': 2},{'expression': '"administracao"','length': -1,'name': 'administracao','precision': 0,'type': 2},{'expression': '"classeativecon"','length': -1,'name': 'classeativecon','precision': 0,'type': 10},{'expression': '"divisaoativecon"','length': -1,'name': 'divisaoativecon','precision': 0,'type': 10},{'expression': '"grupoativecon"','length': -1,'name': 'grupoativecon','precision': 0,'type': 10},{'expression': '"proprioadm"','length': -1,'name': 'proprioadm','precision': 0,'type': 2},{'expression': '"cep"','length': 80,'name': 'cep','precision': -1,'type': 10},{'expression': '"pais"','length': 80,'name': 'pais','precision': -1,'type': 10},{'expression': '"unidadefederacao"','length': 2,'name': 'unidadefederacao','precision': -1,'type': 10},{'expression': '"municipio"','length': 80,'name': 'municipio','precision': -1,'type': 10},{'expression': '"bairro"','length': 80,'name': 'bairro','precision': -1,'type': 10},{'expression': '"logradouro"','length': 200,'name': 'logradouro','precision': -1,'type': 10},{'expression': '"bloco"','length': 80,'name': 'bloco','precision': -1,'type': 10},{'expression': '"numerosequencial"','length': -1,'name': 'numerosequencial','precision': 0,'type': 2},{'expression': '"numerometrico"','length': -1,'name': 'numerometrico','precision': 0,'type': 2},{'expression': '"numeropavimentos"','length': -1,'name': 'numeropavimentos','precision': 0,'type': 2},{'expression': '"tipousoedif"','length': -1,'name': 'tipousoedif','precision': 0,'type': 2},{'expression': '"jurisdicao"','length': -1,'name': 'jurisdicao','precision': 0,'type': 2},{'expression': '"tipoedifpubcivil"','length': -1,'name': 'tipoedifpubcivil','precision': 0,'type': 10},{'expression': '"tx_comentario_producao"','length': -1,'name': 'tx_comentario_producao','precision': -1,'type': 10},{'expression': '"id_nomebngb"','length': -1,'name': 'id_nomebngb','precision': 0,'type': 2},{'expression': '"id_produtor"','length': -1,'name': 'id_produtor','precision': 0,'type': 2},{'expression': '"id_elementoprodutor"','length': -1,'name': 'id_elementoprodutor','precision': 0,'type': 2},{'expression': '"id_antigo"','length': -1,'name': 'id_antigo','precision': 0,'type': 2},{'expression': '"cd_situacao_do_objeto"','length': 2,'name': 'cd_situacao_do_objeto','precision': -1,'type': 10},{'expression': '"id_usuario"','length': -1,'name': 'id_usuario','precision': 0,'type': 2},{'expression': '"dt_atualizacao"','length': -1,'name': 'dt_atualizacao','precision': -1,'type': 16},{'expression': '"tx_geocodigo_municipio"','length': -1,'name': 'tx_geocodigo_municipio','precision': -1,'type': 10},{'expression': '"id_assentamento_precario"','length': -1,'name': 'id_assentamento_precario','precision': 0,'type': 2},{'expression': '"id_complexo_habitacional"','length': -1,'name': 'id_complexo_habitacional','precision': 0,'type': 2},{'expression': '"id_condominio"','length': -1,'name': 'id_condominio','precision': 0,'type': 2},{'expression': '"id_conjunto_habitacional"','length': -1,'name': 'id_conjunto_habitacional','precision': 0,'type': 2},{'expression': '"situacaonome"','length': -1,'name': 'situacaonome','precision': 0,'type': 2},{'expression': '"insumonome"','length': -1,'name': 'insumonome','precision': -1,'type': 10},{'expression': '"situacaoquantoaolimite"','length': -1,'name': 'situacaoquantoaolimite','precision': 0,'type': 2},{'expression': '"observacaong"','length': -1,'name': 'observacaong','precision': -1,'type': 10},{'expression': '"validacaobngb"','length': 1,'name': 'validacaobngb','precision': -1,'type': 10},{'expression': '"compatibilidadeng"','length': -1,'name': 'compatibilidadeng','precision': -1,'type': 10},{'expression': '"osm_id"','length': 10,'name': 'osm_id','precision': 0,'type': 10},{'expression': '"nome_osm"','length': 5,'name': 'nome_osm','precision': 3,'type': 10},{'expression': '"geometria_osm"','length': 5,'name': 'geometria_osm','precision': 3,'type': 10}],
            'INPUT': outputs['MesclarCamadasVetoriais']['OUTPUT'],
            'OUTPUT': parameters['Pol_rod_p']
        }
        outputs['EditarCampos'] = processing.run('qgis:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Pol_rod_p'] = outputs['EditarCampos']['OUTPUT']
        return results

    def name(self):
        return 'Policia_Rodoviaria'

    def displayName(self):
        return 'Policia_Rodoviaria'

    def group(self):
        return 'IBGE'

    def groupId(self):
        return 'IBGE'

    def createInstance(self):
        return Policia_rodoviaria()
