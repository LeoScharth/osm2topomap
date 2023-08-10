"""
Model exported as python.
Name : Relevo Fisiografico Natural
Group : IBGE
With QGIS : 33201
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsExpression
import processing


class RelevoFisiograficoNatural(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterString('EntrecomaChaveOSM', 'Entre com a Chave OSM', optional=True, multiLine=False, defaultValue='natural'))
        self.addParameter(QgsProcessingParameterString('EntrecomoValorOSM', 'Entre com o Valor OSM', optional=True, multiLine=False, defaultValue='peak'))
        self.addParameter(QgsProcessingParameterVectorLayer('definaareadeinteresse2', 'Defina a área de interesse', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('entrecomacamadaderefernciadotipopolgonoasertestada', 'Entre com a camada de REFERÊNCIA do tipo POLÍGONO a ser testada ', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('entrecomacamadaderefernciadotipopontoasertestada', 'Entre com a camada de REFERÊNCIA do tipo PONTO a ser testada ', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterString('entrecomo2valorosm', 'Entre com o 2° Valor OSM', multiLine=False, defaultValue='beach'))
        self.addParameter(QgsProcessingParameterFeatureSink('Elem_fisio_natural_p', 'Elem_Fisio_Natural_P', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Elem_fisio_natural_a', 'Elem_Fisio_Natural_A', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(93, model_feedback)
        results = {}
        outputs = {}

        # Consulta por TAGs do OSM (2)
        alg_params = {
            'EXTENT': parameters['definaareadeinteresse2'],
            'KEY': parameters['EntrecomaChaveOSM'],
            'SERVER': 'https://lz4.overpass-api.de/api/interpreter',
            'TIMEOUT': 25,
            'VALUE': parameters['entrecomo2valorosm']
        }
        outputs['ConsultaPorTagsDoOsm2'] = processing.run('quickosm:buildqueryextent', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Selecionar por atributo ELEMNAT
        alg_params = {
            'FIELD': 'tipoelemnat',
            'INPUT': parameters['entrecomacamadaderefernciadotipopontoasertestada'],
            'METHOD': 0,  # creating new selection
            'OPERATOR': 0,  # =
            'VALUE': '2'
        }
        outputs['SelecionarPorAtributoElemnat'] = processing.run('qgis:selectbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Extrair por expressão Restos
        alg_params = {
            'EXPRESSION': '"nome" IS NOT NULL OR "tipoelemnat" != \'12\'',
            'INPUT': parameters['entrecomacamadaderefernciadotipopolgonoasertestada'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorExpressoRestos'] = processing.run('native:extractbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Extrair por expressão (replace2)
        alg_params = {
            'EXPRESSION': '"tipoelemnat" = \'12\' AND "nome" IS NULL',
            'INPUT': parameters['entrecomacamadaderefernciadotipopolgonoasertestada'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorExpressoReplace2'] = processing.run('native:extractbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Selecionar por atributo Replace(1)
        alg_params = {
            'FIELD': 'tipoelemnat',
            'INPUT': parameters['entrecomacamadaderefernciadotipopolgonoasertestada'],
            'METHOD': 0,  # creating new selection
            'OPERATOR': 0,  # =
            'VALUE': '12'
        }
        outputs['SelecionarPorAtributoReplace1'] = processing.run('qgis:selectbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo_1
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'geometria_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': "'Não'",
            'INPUT': parameters['entrecomacamadaderefernciadotipopontoasertestada'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo_1'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
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

        feedback.setCurrentStep(7)
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

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Selecionar por atributo NOME MORRO
        alg_params = {
            'FIELD': 'nome',
            'INPUT': outputs['SelecionarPorAtributoElemnat']['OUTPUT'],
            'METHOD': 1,  # adding to current selection
            'OPERATOR': 6,  # begins with
            'VALUE': 'Morro'
        }
        outputs['SelecionarPorAtributoNomeMorro'] = processing.run('qgis:selectbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Selecionar por atributo ELEMNAT (2)
        alg_params = {
            'FIELD': 'tipoelemnat',
            'INPUT': outputs['SelecionarPorAtributoNomeMorro']['OUTPUT'],
            'METHOD': 0,  # creating new selection
            'OPERATOR': 0,  # =
            'VALUE': '22'
        }
        outputs['SelecionarPorAtributoElemnat2'] = processing.run('qgis:selectbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Baixar arquivo (2)
        alg_params = {
            'DATA': '',
            'METHOD': 0,  # GET
            'URL': outputs['ConsultaPorTagsDoOsm2']['OUTPUT_URL'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['BaixarArquivo2'] = processing.run('native:filedownloader', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Extrair feições selecionadas
        alg_params = {
            'INPUT': outputs['SelecionarPorAtributoNomeMorro']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairFeiesSelecionadas'] = processing.run('native:saveselectedfeatures', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Buffer (2)
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 0.001129,
            'END_CAP_STYLE': 0,  # Round
            'INPUT': outputs['ExtrairFeiesSelecionadas']['OUTPUT'],
            'JOIN_STYLE': 0,  # Round
            'MITER_LIMIT': 2,
            'SEGMENTS': 16,
            'SEPARATE_DISJOINT': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Buffer2'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # Extrair feições selecionadas Replace(1)
        alg_params = {
            'INPUT': outputs['SelecionarPorAtributoReplace1']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairFeiesSelecionadasReplace1'] = processing.run('native:saveselectedfeatures', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo_2
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'nome_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': "'Não'",
            'INPUT': outputs['CalculadoraDeCampo_1']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo_2'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo_3
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'tipoelemnat2',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': '"tipoelemnat"',
            'INPUT': outputs['CalculadoraDeCampo_2']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo_3'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(16)
        if feedback.isCanceled():
            return {}

        # Selecionar por atributo NOME PICO
        alg_params = {
            'FIELD': 'nome',
            'INPUT': outputs['SelecionarPorAtributoElemnat2']['OUTPUT'],
            'METHOD': 1,  # adding to current selection
            'OPERATOR': 6,  # begins with
            'VALUE': 'Pico'
        }
        outputs['SelecionarPorAtributoNomePico'] = processing.run('qgis:selectbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(17)
        if feedback.isCanceled():
            return {}

        # Pontos Praia
        alg_params = {
            'INPUT_1': outputs['BaixarArquivo2']['OUTPUT'],
            'INPUT_2': QgsExpression("'|layername=points'").evaluate()
        }
        outputs['PontosPraia'] = processing.run('native:stringconcatenation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(18)
        if feedback.isCanceled():
            return {}

        # Recortar (3)
        alg_params = {
            'INPUT': outputs['PontosPraia']['CONCATENATION'],
            'OVERLAY': parameters['definaareadeinteresse2'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Recortar3'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(19)
        if feedback.isCanceled():
            return {}

        # Pontos
        alg_params = {
            'INPUT_1': outputs['BaixarDados']['OUTPUT'],
            'INPUT_2': QgsExpression("'|layername=points'").evaluate()
        }
        outputs['Pontos'] = processing.run('native:stringconcatenation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(20)
        if feedback.isCanceled():
            return {}

        # Poligonos Praia
        alg_params = {
            'INPUT_1': outputs['BaixarArquivo2']['OUTPUT'],
            'INPUT_2': QgsExpression("'|layername=multipolygons'").evaluate()
        }
        outputs['PoligonosPraia'] = processing.run('native:stringconcatenation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(21)
        if feedback.isCanceled():
            return {}

        # Extrair por Morro
        alg_params = {
            'FIELD': 'name',
            'INPUT': outputs['Pontos']['CONCATENATION'],
            'OPERATOR': 6,  # begins with
            'VALUE': 'Morro',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorMorro'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(22)
        if feedback.isCanceled():
            return {}

        # Extrair feições selecionadas
        alg_params = {
            'INPUT': outputs['SelecionarPorAtributoNomePico']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairFeiesSelecionadas'] = processing.run('native:saveselectedfeatures', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(23)
        if feedback.isCanceled():
            return {}

        # Fixar geometrias
        alg_params = {
            'INPUT': outputs['PoligonosPraia']['CONCATENATION'],
            'METHOD': 1,  # Structure
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['FixarGeometrias'] = processing.run('native:fixgeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(24)
        if feedback.isCanceled():
            return {}

        # Descartar campo(s)
        alg_params = {
            'COLUMN': 'tipoelemnat',
            'INPUT': outputs['CalculadoraDeCampo_3']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DescartarCampos'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(25)
        if feedback.isCanceled():
            return {}

        # Extrair por Pico
        alg_params = {
            'FIELD': 'name',
            'INPUT': outputs['Pontos']['CONCATENATION'],
            'OPERATOR': 6,  # begins with
            'VALUE': 'Pico',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorPico'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(26)
        if feedback.isCanceled():
            return {}

        # Selecionar por atributo  ELEMNAT (3)
        alg_params = {
            'FIELD': 'tipoelemnat',
            'INPUT': outputs['SelecionarPorAtributoNomePico']['OUTPUT'],
            'METHOD': 0,  # creating new selection
            'OPERATOR': 0,  # =
            'VALUE': '12'
        }
        outputs['SelecionarPorAtributoElemnat3'] = processing.run('qgis:selectbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(27)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo OG
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'tipoelemnat',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': '"tipoelemnat2"',
            'INPUT': outputs['DescartarCampos']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoOg'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(28)
        if feedback.isCanceled():
            return {}

        # Extrair por localização_3
        alg_params = {
            'INPUT': outputs['Recortar3']['OUTPUT'],
            'INTERSECT': outputs['ExtrairFeiesSelecionadasReplace1']['OUTPUT'],
            'PREDICATE': [2],  # disjoint
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorLocalizao_3'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(29)
        if feedback.isCanceled():
            return {}

        # Selecionar por atributo NOME PRAIA
        alg_params = {
            'FIELD': 'nome',
            'INPUT': outputs['SelecionarPorAtributoElemnat3']['OUTPUT'],
            'METHOD': 1,  # adding to current selection
            'OPERATOR': 6,  # begins with
            'VALUE': 'Praia'
        }
        outputs['SelecionarPorAtributoNomePraia'] = processing.run('qgis:selectbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(30)
        if feedback.isCanceled():
            return {}

        # Recortar (2)
        alg_params = {
            'INPUT': outputs['ExtrairPorMorro']['OUTPUT'],
            'OVERLAY': parameters['definaareadeinteresse2'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Recortar2'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(31)
        if feedback.isCanceled():
            return {}

        # Buffer_1
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 0.001129,
            'END_CAP_STYLE': 0,  # Round
            'INPUT': outputs['ExtrairFeiesSelecionadas']['OUTPUT'],
            'JOIN_STYLE': 0,  # Round
            'MITER_LIMIT': 2,
            'SEGMENTS': 16,
            'SEPARATE_DISJOINT': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Buffer_1'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(32)
        if feedback.isCanceled():
            return {}

        # Extrair feições selecionadas Das PRAIAS
        alg_params = {
            'INPUT': outputs['SelecionarPorAtributoNomePraia']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairFeiesSelecionadasDasPraias'] = processing.run('native:saveselectedfeatures', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(33)
        if feedback.isCanceled():
            return {}

        # Recortar (4)
        alg_params = {
            'INPUT': outputs['FixarGeometrias']['OUTPUT'],
            'OVERLAY': parameters['definaareadeinteresse2'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Recortar4'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(34)
        if feedback.isCanceled():
            return {}

        # Buffer_3
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 0.001129,
            'END_CAP_STYLE': 0,  # Round
            'INPUT': outputs['ExtrairFeiesSelecionadasDasPraias']['OUTPUT'],
            'JOIN_STYLE': 0,  # Round
            'MITER_LIMIT': 2,
            'SEGMENTS': 16,
            'SEPARATE_DISJOINT': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Buffer_3'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(35)
        if feedback.isCanceled():
            return {}

        # Extrair por localização Restante
        alg_params = {
            'INPUT': outputs['ExtrairPorExpressoReplace2']['OUTPUT'],
            'INTERSECT': outputs['ExtrairFeiesSelecionadasDasPraias']['OUTPUT'],
            'PREDICATE': 0,  # intersect
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorLocalizaoRestante'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(36)
        if feedback.isCanceled():
            return {}

        # Extrair por atributo
        alg_params = {
            'FIELD': 'name',
            'INPUT': outputs['ExtrairPorLocalizao_3']['OUTPUT'],
            'OPERATOR': 6,  # begins with
            'VALUE': 'Praia',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorAtributo'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(37)
        if feedback.isCanceled():
            return {}

        # Extrair por localização_4
        alg_params = {
            'INPUT': outputs['ExtrairPorExpressoReplace2']['OUTPUT'],
            'INTERSECT': outputs['ExtrairFeiesSelecionadasDasPraias']['OUTPUT'],
            'PREDICATE': [2],  # disjoint
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorLocalizao_4'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(38)
        if feedback.isCanceled():
            return {}

        # Extrair por localização_1
        alg_params = {
            'INPUT': outputs['Recortar2']['OUTPUT'],
            'INTERSECT': outputs['Buffer2']['OUTPUT'],
            'PREDICATE': [2],  # disjoint
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorLocalizao_1'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(39)
        if feedback.isCanceled():
            return {}

        # Recortar
        alg_params = {
            'INPUT': outputs['ExtrairPorPico']['OUTPUT'],
            'OVERLAY': parameters['definaareadeinteresse2'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Recortar'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(40)
        if feedback.isCanceled():
            return {}

        # Extrair por localização_5
        alg_params = {
            'INPUT': outputs['Recortar4']['OUTPUT'],
            'INTERSECT': outputs['Buffer_3']['OUTPUT'],
            'PREDICATE': [2],  # disjoint
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorLocalizao_5'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(41)
        if feedback.isCanceled():
            return {}

        # Mesclar camadas vetoriais RestosPraia
        alg_params = {
            'CRS': 'ProjectCrs',
            'LAYERS': [outputs['ExtrairPorExpressoRestos']['OUTPUT'],outputs['ExtrairPorLocalizaoRestante']['OUTPUT']],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MesclarCamadasVetoriaisRestospraia'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(42)
        if feedback.isCanceled():
            return {}

        # Distância para o ponto central mais próximo (pontos)
        alg_params = {
            'FIELD': 'nome',
            'HUBS': outputs['ExtrairFeiesSelecionadasDasPraias']['OUTPUT'],
            'INPUT': outputs['ExtrairPorAtributo']['OUTPUT'],
            'UNIT': 0,  # Meters
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DistnciaParaOPontoCentralMaisPrximoPontos'] = processing.run('qgis:distancetonearesthubpoints', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(43)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo PolPraia (1)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'nome_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': "'Não'",
            'INPUT': outputs['MesclarCamadasVetoriaisRestospraia']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoPolpraia1'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(44)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo_PT_INICIO(2)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'PontoInicio',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 1,  # Integer (32 bit)
            'FORMULA': 'strpos(  "other_tags" , (\'"name"=>"\'))+9',
            'INPUT': outputs['ExtrairPorLocalizao_1']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo_pt_inicio2'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(45)
        if feedback.isCanceled():
            return {}

        # Unir atributos pela posição
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': outputs['ExtrairPorLocalizao_4']['OUTPUT'],
            'JOIN': outputs['Recortar4']['OUTPUT'],
            'JOIN_FIELDS': '',
            'METHOD': 1,  # Take attributes of the first matching feature only (one-to-one)
            'PREDICATE': 0,  # intersect
            'PREFIX': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['UnirAtributosPelaPosio'] = processing.run('qgis:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(46)
        if feedback.isCanceled():
            return {}

        # Extrair por localização PraiaPolAdd
        alg_params = {
            'INPUT': outputs['ExtrairPorLocalizao_5']['OUTPUT'],
            'INTERSECT': parameters['entrecomacamadaderefernciadotipopolgonoasertestada'],
            'PREDICATE': 2,  # disjoint
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorLocalizaoPraiapoladd'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(47)
        if feedback.isCanceled():
            return {}

        # Extrair por localização_2
        alg_params = {
            'INPUT': outputs['Recortar']['OUTPUT'],
            'INTERSECT': outputs['Buffer_1']['OUTPUT'],
            'PREDICATE': [2],  # disjoint
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorLocalizao_2'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(48)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo PolPraia(3)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'nome_no_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': '"name"',
            'INPUT': outputs['UnirAtributosPelaPosio']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoPolpraia3'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(49)
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

        feedback.setCurrentStep(50)
        if feedback.isCanceled():
            return {}

        # Extrair por atributo praia
        alg_params = {
            'FIELD': 'HubDist',
            'INPUT': outputs['DistnciaParaOPontoCentralMaisPrximoPontos']['OUTPUT'],
            'OPERATOR': 2,  # >
            'VALUE': '125',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairPorAtributoPraia'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(51)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo Pico1
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'nome_no_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': '"name"',
            'INPUT': outputs['ExtrairPorLocalizao_2']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoPico1'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(52)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo PolPraia (2)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'geometria_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': "'Não'",
            'INPUT': outputs['CalculadoraDeCampoPolpraia1']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoPolpraia2'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(53)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo Add(1)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'osm_id',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': 'if("osm_id" IS NULL,"osm_way_id","osm_id")',
            'INPUT': outputs['ExtrairPorLocalizaoPraiapoladd']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoAdd1'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(54)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo Praia1
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'nome_no_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': '"name"',
            'INPUT': outputs['ExtrairPorAtributoPraia']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoPraia1'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(55)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo PolPraia(4)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'nome_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': 'if( "nome_no_osm" IS NOT NULL,  \'Sim\' ,\'Não\')',
            'INPUT': outputs['CalculadoraDeCampoPolpraia3']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoPolpraia4'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(56)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo PolPraia (5)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'geometria_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': "'Não'",
            'INPUT': outputs['CalculadoraDeCampoPolpraia4']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoPolpraia5'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(57)
        if feedback.isCanceled():
            return {}

        # Descartar campo(s) (1)
        alg_params = {
            'COLUMN': 'PontoInicio',
            'INPUT': outputs['CalculadoraDeCampo_nome2']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DescartarCampos1'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(58)
        if feedback.isCanceled():
            return {}

        # Descartar campo(s) (2)
        alg_params = {
            'COLUMN': 'path',
            'INPUT': outputs['DescartarCampos1']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DescartarCampos2'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(59)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo Add(2)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'nome_no_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': '"name"',
            'INPUT': outputs['CalculadoraDeCampoAdd1']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoAdd2'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(60)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo Pico2
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'nome_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': 'if( "nome_no_osm" IS NOT NULL,  \'Sim\' ,\'Não\')',
            'INPUT': outputs['CalculadoraDeCampoPico1']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoPico2'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(61)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo Add(3)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'nome_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': 'if( "nome_no_osm" IS NOT NULL,  \'Sim\' ,\'Não\')',
            'INPUT': outputs['CalculadoraDeCampoAdd2']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoAdd3'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(62)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo Praia2
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'nome_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': 'if( "nome_no_osm" IS NOT NULL,  \'Sim\' ,\'Não\')',
            'INPUT': outputs['CalculadoraDeCampoPraia1']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoPraia2'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(63)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo Pico3
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'geometria_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': "'Sim'",
            'INPUT': outputs['CalculadoraDeCampoPico2']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoPico3'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(64)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo PolPraia (6)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'nome',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': '"name"',
            'INPUT': outputs['CalculadoraDeCampoPolpraia5']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoPolpraia6'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(65)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo Praia3
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'geometria_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': "'Sim'",
            'INPUT': outputs['CalculadoraDeCampoPraia2']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoPraia3'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(66)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo Pico3.5
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'tipoelemnat',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': "'Pico'",
            'INPUT': outputs['CalculadoraDeCampoPico3']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoPico35'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(67)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo PolPraia (7)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'osm_id',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': 'if("osm_id" IS NULL,"osm_way_id","osm_id")',
            'INPUT': outputs['CalculadoraDeCampoPolpraia6']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoPolpraia7'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(68)
        if feedback.isCanceled():
            return {}

        # Descartar campo(s) (3)
        alg_params = {
            'COLUMN': 'layer',
            'INPUT': outputs['DescartarCampos2']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DescartarCampos3'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(69)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo Praia4
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'tipoelemnat',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': "'Praia'",
            'INPUT': outputs['CalculadoraDeCampoPraia3']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoPraia4'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(70)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo Pico4
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'nome',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': '"nome_no_osm"',
            'INPUT': outputs['CalculadoraDeCampoPico35']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoPico4'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(71)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo Praia5
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'nome',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': '"nome_no_osm"',
            'INPUT': outputs['CalculadoraDeCampoPraia4']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoPraia5'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(72)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo Add(4)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'geometria_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': "'Sim'",
            'INPUT': outputs['CalculadoraDeCampoAdd3']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoAdd4'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(73)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo Add(5)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'nome',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': '"name"',
            'INPUT': outputs['CalculadoraDeCampoAdd4']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoAdd5'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(74)
        if feedback.isCanceled():
            return {}

        # Descartar campo(s) (4)
        alg_params = {
            'COLUMN': 'other_tags',
            'INPUT': outputs['DescartarCampos3']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DescartarCampos4'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(75)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo Add(6)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'tipoelemnat',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 1,  # Integer (32 bit)
            'FORMULA': '12',
            'INPUT': outputs['CalculadoraDeCampoAdd5']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoAdd6'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(76)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo NOME_OSM (1)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'nome_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': 'if( "nome_no_osm" IS NOT NULL,  \'Sim\' ,\'Não\')',
            'INPUT': outputs['DescartarCampos4']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoNome_osm1'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(77)
        if feedback.isCanceled():
            return {}

        # Mesclar camadas vetoriais_2
        alg_params = {
            'CRS': 'ProjectCrs',
            'LAYERS': [outputs['CalculadoraDeCampoAdd6']['OUTPUT'],outputs['CalculadoraDeCampoPolpraia2']['OUTPUT'],outputs['CalculadoraDeCampoPolpraia7']['OUTPUT']],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MesclarCamadasVetoriais_2'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(78)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo GEOM_OSM (1)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'geometria_osm',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': "'Sim'",
            'INPUT': outputs['CalculadoraDeCampoNome_osm1']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoGeom_osm1'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(79)
        if feedback.isCanceled():
            return {}

        # Editar campos_2
        alg_params = {
            'FIELDS_MAPPING': [{'alias': '','comment': '','expression': '"id"','length': -1,'name': 'id','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'alias': '','comment': '','expression': '"nome"','length': 150,'name': 'nome','precision': -1,'sub_type': 0,'type': 10,'type_name': 'text'},{'alias': '','comment': '','expression': '"geometriaaproximada"','length': -1,'name': 'geometriaaproximada','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'alias': '','comment': '','expression': '"tipoelemnat"','length': 10,'name': 'tipoelemnat','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},{'alias': '','comment': '','expression': '"tx_comentario_producao"','length': -1,'name': 'tx_comentario_producao','precision': -1,'sub_type': 0,'type': 10,'type_name': 'text'},{'alias': '','comment': '','expression': '"id_nomebngb"','length': -1,'name': 'id_nomebngb','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'alias': '','comment': '','expression': '"id_produtor"','length': -1,'name': 'id_produtor','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'alias': '','comment': '','expression': '"id_elementoprodutor"','length': -1,'name': 'id_elementoprodutor','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'alias': '','comment': '','expression': '"id_antigo"','length': -1,'name': 'id_antigo','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'alias': '','comment': '','expression': '"cd_situacao_do_objeto"','length': 2,'name': 'cd_situacao_do_objeto','precision': -1,'sub_type': 0,'type': 10,'type_name': 'text'},{'alias': '','comment': '','expression': '"id_usuario"','length': -1,'name': 'id_usuario','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'alias': '','comment': '','expression': '"dt_atualizacao"','length': -1,'name': 'dt_atualizacao','precision': -1,'sub_type': 0,'type': 16,'type_name': 'datetime'},{'alias': '','comment': '','expression': '"tx_geocodigo_municipio"','length': -1,'name': 'tx_geocodigo_municipio','precision': -1,'sub_type': 0,'type': 10,'type_name': 'text'},{'alias': '','comment': '','expression': '"formarocha"','length': -1,'name': 'formarocha','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'alias': '','comment': '','expression': '"situacaonome"','length': -1,'name': 'situacaonome','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'alias': '','comment': '','expression': '"insumonome"','length': -1,'name': 'insumonome','precision': -1,'sub_type': 0,'type': 10,'type_name': 'text'},{'alias': '','comment': '','expression': '"situacaoquantoaolimite"','length': -1,'name': 'situacaoquantoaolimite','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'alias': '','comment': '','expression': '"observacaong"','length': -1,'name': 'observacaong','precision': -1,'sub_type': 0,'type': 10,'type_name': 'text'},{'alias': '','comment': '','expression': '"validacaobngb"','length': 1,'name': 'validacaobngb','precision': -1,'sub_type': 0,'type': 10,'type_name': 'text'},{'alias': '','comment': '','expression': '"compatibilidadeng"','length': -1,'name': 'compatibilidadeng','precision': -1,'sub_type': 0,'type': 10,'type_name': 'text'},{'alias': '','comment': '','expression': '"fixa"','length': -1,'name': 'fixa','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'alias': '','comment': '','expression': '"osm_id"','length': 10,'name': 'osm_id','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},{'alias': '','comment': '','expression': '"nome_no_osm"','length': 255,'name': 'nome_no_osm','precision': 3,'sub_type': 0,'type': 10,'type_name': 'text'},{'alias': '','comment': '','expression': '"nome_osm"','length': 5,'name': 'nome_osm','precision': 3,'sub_type': 0,'type': 10,'type_name': 'text'},{'alias': '','comment': '','expression': '"geometria_osm"','length': 5,'name': 'geometria_osm','precision': 3,'sub_type': 0,'type': 10,'type_name': 'text'}],
            'INPUT': outputs['MesclarCamadasVetoriais_2']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['EditarCampos_2'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(80)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo NEW
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'tipoelemnat',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': "'Morro'",
            'INPUT': outputs['CalculadoraDeCampoGeom_osm1']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampoNew'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(81)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo_4
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'nome',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': '"nome_no_osm"',
            'INPUT': outputs['CalculadoraDeCampoNew']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CalculadoraDeCampo_4'] = processing.run('native:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(82)
        if feedback.isCanceled():
            return {}

        # Mapear Atributos (7)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'tipoelemnat',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': 'if( "tipoelemnat" =\'1\',\'Serra\', "tipoelemnat" )',
            'INPUT': outputs['EditarCampos_2']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MapearAtributos7'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(83)
        if feedback.isCanceled():
            return {}

        # 'Mapear Atributos (8)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'tipoelemnat',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': 'if( "tipoelemnat" =\'12\',\'Praia\', "tipoelemnat" )',
            'INPUT': outputs['MapearAtributos7']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MapearAtributos8'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(84)
        if feedback.isCanceled():
            return {}

        # Mesclar camadas vetoriais_1
        alg_params = {
            'CRS': 'ProjectCrs',
            'LAYERS': [outputs['CalculadoraDeCampoOg']['OUTPUT'],outputs['CalculadoraDeCampoPico4']['OUTPUT'],outputs['CalculadoraDeCampoPraia5']['OUTPUT'],outputs['CalculadoraDeCampo_4']['OUTPUT']],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MesclarCamadasVetoriais_1'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(85)
        if feedback.isCanceled():
            return {}

        # Editar campos_1
        alg_params = {
            'FIELDS_MAPPING': [{'alias': '','comment': '','expression': '"id"','length': -1,'name': 'id','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'alias': '','comment': '','expression': '"nome"','length': 150,'name': 'nome','precision': -1,'sub_type': 0,'type': 10,'type_name': 'text'},{'alias': '','comment': '','expression': '"geometriaaproximada"','length': -1,'name': 'geometriaaproximada','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'alias': '','comment': '','expression': '"tipoelemnat"','length': 10,'name': 'tipoelemnat','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},{'alias': '','comment': '','expression': '"tx_comentario_producao"','length': -1,'name': 'tx_comentario_producao','precision': -1,'sub_type': 0,'type': 10,'type_name': 'text'},{'alias': '','comment': '','expression': '"id_nomebngb"','length': -1,'name': 'id_nomebngb','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'alias': '','comment': '','expression': '"id_produtor"','length': -1,'name': 'id_produtor','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'alias': '','comment': '','expression': '"id_elementoprodutor"','length': -1,'name': 'id_elementoprodutor','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'alias': '','comment': '','expression': '"id_antigo"','length': -1,'name': 'id_antigo','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'alias': '','comment': '','expression': '"cd_situacao_do_objeto"','length': 2,'name': 'cd_situacao_do_objeto','precision': -1,'sub_type': 0,'type': 10,'type_name': 'text'},{'alias': '','comment': '','expression': '"id_usuario"','length': -1,'name': 'id_usuario','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'alias': '','comment': '','expression': '"dt_atualizacao"','length': -1,'name': 'dt_atualizacao','precision': -1,'sub_type': 0,'type': 16,'type_name': 'datetime'},{'alias': '','comment': '','expression': '"tx_geocodigo_municipio"','length': -1,'name': 'tx_geocodigo_municipio','precision': -1,'sub_type': 0,'type': 10,'type_name': 'text'},{'alias': '','comment': '','expression': '"formarocha"','length': -1,'name': 'formarocha','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'alias': '','comment': '','expression': '"situacaonome"','length': -1,'name': 'situacaonome','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'alias': '','comment': '','expression': '"insumonome"','length': -1,'name': 'insumonome','precision': -1,'sub_type': 0,'type': 10,'type_name': 'text'},{'alias': '','comment': '','expression': '"situacaoquantoaolimite"','length': -1,'name': 'situacaoquantoaolimite','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'alias': '','comment': '','expression': '"observacaong"','length': -1,'name': 'observacaong','precision': -1,'sub_type': 0,'type': 10,'type_name': 'text'},{'alias': '','comment': '','expression': '"validacaobngb"','length': 1,'name': 'validacaobngb','precision': -1,'sub_type': 0,'type': 10,'type_name': 'text'},{'alias': '','comment': '','expression': '"compatibilidadeng"','length': -1,'name': 'compatibilidadeng','precision': -1,'sub_type': 0,'type': 10,'type_name': 'text'},{'alias': '','comment': '','expression': '"fixa"','length': -1,'name': 'fixa','precision': 0,'sub_type': 0,'type': 2,'type_name': 'integer'},{'alias': '','comment': '','expression': '"osm_id"','length': 0,'name': 'osm_id','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'},{'alias': '','comment': '','expression': '"nome_osm"','length': 5,'name': 'nome_osm','precision': 3,'sub_type': 0,'type': 10,'type_name': 'text'},{'alias': '','comment': '','expression': '"geometria_osm"','length': 5,'name': 'geometria_osm','precision': 3,'sub_type': 0,'type': 10,'type_name': 'text'}],
            'INPUT': outputs['MesclarCamadasVetoriais_1']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['EditarCampos_1'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(86)
        if feedback.isCanceled():
            return {}

        # 'Mapear Atributos (9)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'tipoelemnat',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': 'if( "tipoelemnat" =\'23\',\'Rocha\', "tipoelemnat" )',
            'INPUT': outputs['MapearAtributos8']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': parameters['Elem_fisio_natural_a']
        }
        outputs['MapearAtributos9'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Elem_fisio_natural_a'] = outputs['MapearAtributos9']['OUTPUT']

        feedback.setCurrentStep(87)
        if feedback.isCanceled():
            return {}

        # Mapear Atributos (1)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'tipoelemnat',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': 'if( "tipoelemnat" =\'2\',\'Morro\', "tipoelemnat" )',
            'INPUT': outputs['EditarCampos_1']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MapearAtributos1'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(88)
        if feedback.isCanceled():
            return {}

        # Mapear Atributos (2)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'tipoelemnat',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': 'if( "tipoelemnat" =\'22\',\'Pico\', "tipoelemnat" )',
            'INPUT': outputs['MapearAtributos1']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MapearAtributos2'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(89)
        if feedback.isCanceled():
            return {}

        # Mapear Atributos (3)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'tipoelemnat',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': 'if( "tipoelemnat" =\'12\',\'Praia\', "tipoelemnat" )',
            'INPUT': outputs['MapearAtributos2']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MapearAtributos3'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(90)
        if feedback.isCanceled():
            return {}

        # Mapear Atributos (4)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'tipoelemnat',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': 'if( "tipoelemnat" =\'10\',\'Ponta\', "tipoelemnat" )',
            'INPUT': outputs['MapearAtributos3']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MapearAtributos4'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(91)
        if feedback.isCanceled():
            return {}

        # Mapear Atributos (5)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'tipoelemnat',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': 'if( "tipoelemnat" =\'11\',\'Cabo\', "tipoelemnat" )',
            'INPUT': outputs['MapearAtributos4']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MapearAtributos5'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(92)
        if feedback.isCanceled():
            return {}

        # Mapear Atributos (6)
        alg_params = {
            'FIELD_LENGTH': 255,
            'FIELD_NAME': 'tipoelemnat',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2,  # Text (string)
            'FORMULA': 'if( "tipoelemnat" =\'99\',\'Outros\', "tipoelemnat" )',
            'INPUT': outputs['MapearAtributos5']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': parameters['Elem_fisio_natural_p']
        }
        outputs['MapearAtributos6'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Elem_fisio_natural_p'] = outputs['MapearAtributos6']['OUTPUT']
        return results

    def name(self):
        return 'Relevo Fisiografico Natural'

    def displayName(self):
        return 'Relevo Fisiografico Natural'

    def group(self):
        return 'IBGE'

    def groupId(self):
        return 'IBGE'

    def createInstance(self):
        return RelevoFisiograficoNatural()
