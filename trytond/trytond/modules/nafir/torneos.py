import datetime
from decimal import Decimal
from trytond.pyson import Eval
from trytond.model import fields, ModelSQL, ModelView, ModelSingleton, DeactivableMixin
from trytond.pool import Pool
from trytond.exceptions import UserError
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, StateTransition, Button
import random

#falta revisar lo de local visitante
#agregar funcion de renovar masivo


class Torneos(ModelSQL, ModelView):
    """Torneos"""
    __name__ = 'nafir.torneos'
    _rec_name = 'nombre'

    nombre = fields.Char(u'Nombre', required=True)
    tipo = fields.Many2One('nafir.tipo_torneo', 'Tipo', required=True)
    solicitar_categoria = fields.Function(fields.Boolean(u'Solicitar Categoria', states={'invisible': True}), 'on_change_with_solicitar_categoria')
    categoria_desde = fields.Many2One('nafir.categorias', 'Categoria Desde',
                                      states={'invisible': ~Eval('solicitar_categoria', False),
                                              'required': Eval('solicitar_categoria', True)})
    categoria_hasta = fields.Many2One('nafir.categorias', 'Categoria Hasta',
                                      states={'invisible': ~Eval('solicitar_categoria', False),
                                              'required': Eval('solicitar_categoria', True)})
    clubes = fields.One2Many('nafir.torneos.clubes', 'torneo', 'Clubes')
    lineas = fields.One2Many('nafir.torneos.lineas', 'torneo', 'Lineas')
    fechas = fields.One2Many('nafir.torneos.fechas', 'torneo', 'Fechas')
    estado = fields.Selection([
        ('borrador', u'Borrador'),
        ('iniciado', u'Iniciado'),
        ('finalizado', u'Finalizado'),
        ], u'Estado', readonly=True, required=True)
    fecha_inicio = fields.Date('Fecha Inicio', readonly=True)
    fecha_fin = fields.Date('Fecha Finalizado', readonly=True)

    @classmethod
    def copy(cls, torneos, default=None):
        if len(torneos) >1:
            raise UserError(u'No se pueden duplicar mas de un torneo a la vez')
        if default is None:
            default = {}
        else:
            default = default.copy()
        default.setdefault('estado', 'borrador')
        default.setdefault('fechas', None)
        default.setdefault('clubes.partidos_locales', None)
        default.setdefault('lineas.partidos_locales', None)
        default.setdefault('clubes.partidos_visitantes', None)
        default.setdefault('lineas.partidos_visitantes', None)
        torneos_creados = super(Torneos, cls).copy(torneos, default=default)
        Torneos.borrador(torneos_creados)
        return torneos_creados


    @fields.depends('tipo')
    def on_change_with_solicitar_categoria(self, name=None):
        return self.tipo.solicitar_categoria if self.tipo else None

    @classmethod
    def default_estado(cls):
        return 'borrador'

    @classmethod
    def __setup__(cls):
        super(Torneos, cls).__setup__()
        cls._buttons.update({
            'agregar_club': {'invisible': (Eval('estado').in_(['iniciado','finalizado']))},
            'borrador': {'invisible': (Eval('estado').in_(['borrador','finalizado']))},
            'iniciar': {'invisible': (Eval('estado').in_(['iniciado','finalizado']))},
            'finalizar': {'invisible': (Eval('estado').in_(['borrador','finalizado']))},
        })

    @classmethod
    def borrador(cls, torneos):
        config = Pool().get('nafir.configuracion')(1)
        for x in torneos:
            TorneosFechas.delete(x.fechas)
            linea_libre = TorneosLineas.search([('torneo', '=', x.id), ('club', '=', config.club_libre.id)])
            club_libre = TorneosClubes.search([('torneo', '=', x.id), ('club', '=', config.club_libre.id)])
            TorneosLineas.delete(linea_libre)
            TorneosClubes.delete(club_libre)

            x.fecha_inicio = None
            x.estado = 'borrador'
            x.save()

    @classmethod
    def iniciar(cls, torneos):
        Categorias = Pool().get('nafir.categorias')
        for x in torneos:
            x.fecha_inicio = datetime.date.today()
            x.estado = 'iniciado'
            if len(x.lineas) % 2 != 0:
                config = Pool().get('nafir.configuracion')(1)
                a_crear = [{'torneo': x.id, 'club': config.club_libre.id}]
                club = TorneosClubes.create(a_crear)
                a_crear = [{'torneo': x.id, 'club': config.club_libre.id, 'linea': config.linea_libre.id, 'torneo_club': club[0].id, 'es_libre': True}]
                TorneosLineas.create(a_crear)
                x.save()

            categ_desde = x.categoria_desde.anio
            categ_hasta = x.categoria_hasta.anio
            categorias = Categorias.search([('anio', '>=', categ_desde), ('anio', '<=', categ_hasta)])
            categorias_crear = []
            categorias_libre_crear = []
            for categ in categorias:
                categorias_crear.append({'categoria': categ.id, 'es_libre': False})
                categorias_libre_crear.append({'categoria': categ.id, 'es_libre': True})
            a_crear_fechas = []
            equipos = []
            for linea in x.lineas:
                equipos.append(linea)
            equipos = sorted(equipos, key=lambda y: random.randint(0, len(equipos)))
            fechas = {}
            #partidos_ya_creados = {}
            #partidos = {}
            indices_locales = []
            equipos_locales_fecha_anterior = []
            equipos_locales_fecha_anterior_anterior = []
            equipos_locales_fecha_actual = []
            for i in range(1, len(x.lineas)):
                indices_locales.append(i)
            for i in range(len(x.lineas)-1):
                fechas[i] = []
                #partidos_ya_creados[i] = []
                #partidos[i] = []
                indice_equipo1 = 0
                num_partido = 0
                while num_partido < int(len(x.lineas)/2):
                    indice_contrario_equipo1 = indices_locales[(len(indices_locales)-1)-num_partido]
                    equipo_1 = equipos[indice_equipo1]
                    equipo_2 = equipos[indice_contrario_equipo1]
                    if equipo_1.id in equipos_locales_fecha_anterior and equipo_2 not in equipos_locales_fecha_anterior:
                        equipo_temp = equipo_2
                        equipo_2 = equipo_1
                        equipo_1 = equipo_temp
                    elif equipo_1.id in equipos_locales_fecha_anterior_anterior and equipo_2 not in equipos_locales_fecha_anterior_anterior:
                        equipo_temp = equipo_2
                        equipo_2 = equipo_1
                        equipo_1 = equipo_temp
                    #partidos_ya_creados[i].append(equipo_1.id)
                    #partidos_ya_creados[i].append(equipo_2.id)
                    #partidos[i].append([equipo_1.id, equipo_2.id])
                    fechas[i].append({'club_linea_local': equipo_1.id,
                                      'club_linea_visitante': equipo_2.id,
                                      'es_libre': True if equipo_1.es_libre or equipo_2.es_libre else False,
                                      'cancha': equipo_1.club.cancha if equipo_1.club.cancha and equipo_1.club.cancha != '' else 'No indicado',
                                      'torneo_club_local': equipo_1.torneo_club.id,
                                      'torneo_club_visitante': equipo_2.torneo_club.id,
                                      'club_local': equipo_1.club.id,
                                      'club_visitante': equipo_2.club.id,
                                      'categorias': [('create', categorias_libre_crear)]  if equipo_1.es_libre or equipo_2.es_libre else [('create', categorias_crear)]
                                      })
                    indice_equipo1 = indices_locales[num_partido]
                    num_partido += 1
                    equipos_locales_fecha_actual.append(equipo_1.id)
                indices_locales += [indices_locales.pop(0)]
                equipos_locales_fecha_anterior_anterior = equipos_locales_fecha_anterior
                equipos_locales_fecha_anterior = equipos_locales_fecha_actual
                equipos_locales_fecha_actual = []

            for i in range(len(x.lineas)-1):
                a_crear_fechas.append({'torneo': x.id,
                                       'numero': i+1,
                                       'partidos':[('create', fechas[i])]
                                       })
            TorneosFechas.create(a_crear_fechas)
            x.save()

    @classmethod
    def finalizar(cls, torneos):
        for x in torneos:
            x.fecha_fin = datetime.date.today()
            x.estado = 'finalizado'
            x.save()

    @classmethod
    @ModelView.button_action('nafir.act_agregar_club_wizard')
    def agregar_club(cls, torneos):
        pass


class TorneosClubes(ModelSQL, ModelView):
    """Torneos - Clubes"""
    __name__ = 'nafir.torneos.clubes'

    torneo = fields.Many2One('nafir.torneos', 'Torneo', required=True)
    club = fields.Many2One('nafir.clubes', 'Club', required=True)
    partidos_locales = fields.One2Many('nafir.torneos.fechas.partidos', 'torneo_club_local', 'Partidos de Local')
    partidos_visitantes = fields.One2Many('nafir.torneos.fechas.partidos', 'torneo_club_visitante', 'Partidos de visitante')

    def get_rec_name(self, name):
        if self.club:
            return self.club.rec_name

    @classmethod
    def search_rec_name(cls, name, clause):
        return ['OR',
            ('club',) + tuple(clause[1:]),
            ]


class TorneosLineas(ModelSQL, ModelView):
    """Torneos - Lineas"""
    __name__ = 'nafir.torneos.lineas'

    torneo = fields.Many2One('nafir.torneos', 'Torneo', required=True)
    club = fields.Many2One('nafir.clubes', 'Club', required=True)
    linea = fields.Many2One('nafir.clubes.lineas', 'Linea', required=True)
    torneo_club = fields.Many2One('nafir.torneos.clubes', 'Torneo Club')
    partidos_locales = fields.One2Many('nafir.torneos.fechas.partidos', 'club_linea_local', 'Partidos de Local')
    partidos_visitantes = fields.One2Many('nafir.torneos.fechas.partidos', 'club_linea_visitante', 'Partidos de visitante')
    es_libre = fields.Boolean('Es Libre')
    def get_rec_name(self, name):
        if self.linea:
            return self.linea.rec_name

    @classmethod
    def search_rec_name(cls, name, clause):
        return ['OR',
            ('linea',) + tuple(clause[1:]),
            ]


class TorneosFechas(ModelSQL, ModelView):
    """Torneos - Fechas"""
    __name__ = 'nafir.torneos.fechas'

    torneo = fields.Many2One('nafir.torneos', 'Torneo', required=True, readonly=True)
    numero = fields.Integer('Numero', required=True, readonly=True)
    partidos = fields.One2Many('nafir.torneos.fechas.partidos', 'fecha', 'Partidos')

    def get_rec_name(self, name):
        rec = ''
        if self.numero:
            rec = str(self.numero)
        return rec


class TorneosPartidos(ModelSQL, ModelView):
    """Partidos"""
    __name__ = 'nafir.torneos.fechas.partidos'

    fecha = fields.Many2One('nafir.torneos.fechas', 'Fecha', required=True, readonly=True, ondelete='CASCADE')
    categorias = fields.One2Many('nafir.torneos.fechas.partidos.categorias', 'partido', 'Categorias')
    club_linea_local = fields.Many2One('nafir.torneos.lineas', 'Club Linea Local', required=True, readonly=True)
    club_linea_visitante = fields.Many2One('nafir.torneos.lineas', 'Club Linea Visitante', required=True, readonly=True)
    torneo_club_local = fields.Many2One('nafir.torneos.clubes', 'Torneo Club Local')
    torneo_club_visitante = fields.Many2One('nafir.torneos.clubes', 'Torneo Club Visitante')
    club_local = fields.Many2One('nafir.clubes', 'Club Local')
    club_visitante = fields.Many2One('nafir.clubes', 'Club Visitante')
    cancha = fields.Char('Cancha', required=True)
    hora = fields.Char('Hora')
    es_libre = fields.Boolean('Es Libre')
    #club_local = fields.Function(fields.Many2One('nafir.clubes', 'Club Local', states={'invisible': True}), 'on_change_with_club_local')
    #linea_local = fields.Function(fields.Many2One('nafir.clubes.lineas', 'Linea Local', states={'invisible': True}), 'on_change_with_linea_local')

    # @fields.depends('club_linea_local')
    # def on_change_with_club_local(self, name=None):
    #     return self.club_linea_local.club.id if self.club_linea_local else None
    #
    # @fields.depends('club_linea_local')
    # def on_change_with_linea_local(self, name=None):
    #     return self.club_linea_local.linea.id if self.club_linea_local else None
    #
    # @fields.depends('cancha')
    # def on_change_club_linea_local(self):
    #     self.cancha = self.club_linea_local.club.cancha if self.club_linea_local else ''

    def get_rec_name(self, name):
        if self.fecha and self.club_linea_local and self.club_linea_visitante:
            return self.fecha.rec_name + ' - ' + self.club_linea_local.rec_name + ' Vrs ' + self.club_linea_visitante.rec_name

    @classmethod
    def search_rec_name(cls, name, clause):
        return ['OR',
            ('fecha',) + tuple(clause[1:]),
            ('club_linea_local',) + tuple(clause[1:]),
            ('club_linea_visitante',) + tuple(clause[1:]),
            ]


class TorneosPartidosCategorias(ModelSQL, ModelView):
    """Partidos - Categorias"""
    __name__ = 'nafir.torneos.fechas.partidos.categorias'

    partido = fields.Many2One('nafir.torneos.fechas.partidos', 'Partido', required=True, readonly=True, ondelete='CASCADE')
    categoria = fields.Many2One('nafir.categorias', 'Categoria', required=True, readonly=True)
    resultado_local = fields.Integer('Resultado Local')
    resultado_visitante = fields.Integer('Resultado Visitante')
    es_libre = fields.Boolean('Es Libre')
    tipo_torneo = fields.Function(fields.Many2One('nafir.tipo_torneo', 'Tipo', states={'invisible': True}), 'on_change_with_tipo_torneo')
    club_local = fields.Function(fields.Many2One('nafir.clubes', 'Club Local'),
                                 'on_change_with_club_local')
    club_visitante = fields.Function(fields.Many2One('nafir.clubes', 'Club Visitante'),
                                     'on_change_with_club_visitante')
    hoy = fields.Function(fields.Date('Hoy', states={'invisible': True}), 'on_change_with_hoy')
    jugadores_locales = fields.Many2Many('nafir.torneos.asistencia.local',
                                         'categoria', 'jugador', 'Jugadores Equipo local',
                                         domain=[('club', '=', Eval('club_local')),
                                                 ('juego_tipo_torneo', '=', Eval('tipo_torneo')),
                                                 ('fecha_desde', '<=', Eval('hoy')),
                                                 ['OR', ('fecha_hasta', '=', None), ('fecha_hasta', '>=', Eval('hoy'))],
                                                 ['OR', ('requiere_libre_deuda', '=', False), (('requiere_libre_deuda', '=', True), ('libre_deuda', '=', True))]],
                                         depends=['club_local', 'hoy'])
    jugadores_visitantes = fields.Many2Many('nafir.torneos.asistencia.visitante',
                                         'categoria', 'jugador', 'Jugadores Equipo visitante',
                                         domain=[('club', '=', Eval('club_visitante')),
                                                 ('juego_tipo_torneo', '=', Eval('tipo_torneo')),
                                                 ('fecha_desde', '<=', Eval('hoy')),
                                                 ['OR', ('fecha_hasta', '=', None), ('fecha_hasta', '>=', Eval('hoy'))],
                                                 ['OR', ('requiere_libre_deuda', '=', False), (('requiere_libre_deuda', '=', True), ('libre_deuda', '=', True))]],
                                         depends=['club_visitante', 'hoy'])

    @fields.depends('partido')
    def on_change_with_tipo_torneo(self, name=None):
        if self.partido:
            return self.partido.fecha.torneo.tipo.id

    @fields.depends('partido')
    def on_change_with_club_local(self, name=None):
        return self.partido.club_linea_local.club.id if self.partido.club_linea_local else None

    @fields.depends('partido')
    def on_change_with_club_visitante(self, name=None):
        return self.partido.club_linea_visitante.club.id if self.partido.club_linea_visitante else None

    @fields.depends('id')
    def on_change_with_hoy(self, name=None):
        return datetime.date.today()

    def get_rec_name(self, name):
        if self.partido and self.categoria:
            return self.partido.rec_name + ' - ' + self.categoria.rec_name

    @classmethod
    def __setup__(cls):
        super(TorneosPartidosCategorias, cls).__setup__()
        cls._buttons.update({
            'cargar_resultado': {},
        })

    @classmethod
    @ModelView.button_action('nafir.act_cargar_resultado_wizard')
    def cargar_resultado(cls, torneos):
        pass


class TorneosAsistenciaClubLocal(ModelSQL):
    'Agregar Asistencia - Club Local'
    __name__ = 'nafir.torneos.asistencia.local'
    _table = 'nafir_torneos_asistencia_local'

    categoria = fields.Many2One('nafir.torneos.fechas.partidos.categorias', 'Partido-Categoria',
            ondelete='CASCADE', select=True, required=True)
    club_local = fields.Function(fields.Many2One('nafir.clubes', 'Club Local', states={'invisible': True}),
                                 'on_change_with_club_local')
    club_visitante = fields.Function(fields.Many2One('nafir.clubes', 'Club Visitante', states={'invisible': True}),
                                 'on_change_with_club_visitante')
    jugador = fields.Many2One('nafir.jugadores.lineas', 'Jugador',
                              ondelete='RESTRICT', select=True, required=True,)
                              #domain = [('club', '=', Eval('club_local'))],
                              #depends = ['club_local'])

    @fields.depends('categoria')
    def on_change_with_club_local(self, name=None):
        return self.categoria.partido.club_linea_local.club.id if self.categoria.partido.club_linea_local else None

    @fields.depends('categoria')
    def on_change_with_club_visitante(self, name=None):
        return self.categoria.partido.club_linea_visitante.club.id if self.categoria.partido.club_linea_visitante else None


class TorneosAsistenciaClubVisitante(ModelSQL):
    'Agregar Asistencia - Club visitante'
    __name__ = 'nafir.torneos.asistencia.visitante'
    _table = 'nafir_torneos_asistencia_visitante'

    categoria = fields.Many2One('nafir.torneos.fechas.partidos.categorias', 'Partido-Categoria',
            ondelete='CASCADE', select=True, required=True)
    jugador = fields.Many2One('nafir.jugadores.lineas', 'Jugador',
                              ondelete='RESTRICT', select=True, required=True,)


class CargarResultado(Wizard):
    """Cargar resultado de un partido en una categoria - wizard"""
    __name__ = 'nafir.torneos.cargar_resultado'

    start = StateView('nafir.torneos.cargar_resultado.start', 'nafir.cargar_resultado_start_view_form', [
        Button('Cancelar', 'end', 'tryton-cancel'),
        Button('Guardar', 'accept', 'tryton-ok')])
    accept = StateTransition()

    def default_start(self, fields):
        default = {'categoria': Transaction().context['active_id']}
        return default

    def transition_accept(self):
        categoria = self.start.categoria
        categoria.resultado_local = self.start.resultado_local
        categoria.resultado_visitante = self.start.resultado_visitante
        categoria.save()
        return 'end'


class CargarResultadoStart(ModelSQL, ModelView):
    """Cargar resultado de un partido en una categoria - start"""
    __name__='nafir.torneos.cargar_resultado.start'

    categoria = fields.Many2One('nafir.torneos.fechas.partidos.categorias', 'Partido-Categoria', readonly=True)
    resultado_local = fields.Integer('Resultado Local', required=True)
    resultado_visitante = fields.Integer('Resultado Visitante', required=True)


class AgregarClub(Wizard):
    """Agregar Club - wizard"""
    __name__ = 'nafir.torneos.agregar_club'

    start = StateView('nafir.torneos.agregar_club.start', 'nafir.agregar_club_start_view_form', [
        Button('Cancelar', 'end', 'tryton-cancel'),
        Button('Guardar', 'accept', 'tryton-ok')])
    accept = StateTransition()

    def default_start(self, fields):
        default = {'torneo': Transaction().context['active_id']}
        return default

    def transition_accept(self):
        torneo = self.start.torneo
        a_crear_clubes = []
        a_crear_lineas = []
        for x in self.start.detalle:
            ya_existe = TorneosClubes.search([('torneo', '=', torneo.id), ('club', '=', x.id)])
            if not ya_existe:
                a_crear = {'torneo': torneo.id, 'club': x.id}
                if a_crear not in a_crear_clubes:
                    a_crear_clubes.append(a_crear)

                for linea in x.lineas:
                    a_crear = {'torneo': torneo.id, 'club': x.id, 'linea': linea.id}
                    if a_crear not in a_crear_lineas:
                        a_crear_lineas.append(a_crear)

        torneos_clubes = TorneosClubes.create(a_crear_clubes)
        for linea in a_crear_lineas:
            for club in torneos_clubes:
                if club.club.id == linea['club']:
                    linea['torneo_club'] = club.id
        TorneosLineas.create(a_crear_lineas)
        return 'end'


class AgregarClubStart(ModelSQL, ModelView):
    """Agregar Club - start"""
    __name__='nafir.torneos.agregar_club.start'

    torneo = fields.Many2One('nafir.torneos', 'Torneo')
    #detalle = fields.One2Many('nafir.torneos.agregar_club.detalle', None, 'Clubes')
    detalle = fields.Many2Many('nafir.torneos.agregar_club.start-nafir.clubes', None, 'club', 'Clubes')


class AgregarClubDetalle(ModelSQL):
    """Agregar Club - Detalle"""
    __name__='nafir.torneos.agregar_club.start-nafir.clubes'

    club = fields.Many2One('nafir.clubes', 'Club', required=True)
