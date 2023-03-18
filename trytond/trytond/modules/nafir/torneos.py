import datetime
from decimal import Decimal
from trytond.pyson import Eval
from trytond.model import fields, ModelSQL, ModelView, ModelSingleton, DeactivableMixin
from trytond.pool import Pool
from trytond.exceptions import UserError
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, StateTransition, Button


class Torneos(ModelSQL, ModelView):
    """Torneos"""
    __name__ = 'nafir.torneos'
    _rec_name = 'nombre'

    nombre = fields.Char(u'Nombre', required=True)
    clubes = fields.One2Many('nafir.torneos.clubes', 'torneo', 'Clubes')
    categorias = fields.One2Many('nafir.torneos.categorias', 'torneo', 'Categorias')
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
    def default_estado(cls):
        return 'borrador'

    @classmethod
    def __setup__(cls):
        super(Torneos, cls).__setup__()
        cls._buttons.update({
            'agregar_linea': {'invisible': (Eval('estado').in_(['iniciado','finalizado']))},
            'borrador': {'invisible': (Eval('estado').in_(['borrador','finalizado']))},
            'iniciar': {'invisible': (Eval('estado').in_(['iniciado','finalizado']))},
            'finalizar': {'invisible': (Eval('estado').in_(['borrador','finalizado']))},
        })

    @classmethod
    def borrador(cls, torneos):
        for x in torneos:
            x.fecha_inicio = None
            x.estado = 'borrador'
            x.save()

    @classmethod
    def iniciar(cls, torneos):
        for x in torneos:
            x.fecha_inicio = datetime.date.today()
            x.estado = 'iniciado'
            x.save()

    @classmethod
    def finalizar(cls, torneos):
        for x in torneos:
            x.fecha_fin = datetime.date.today()
            x.estado = 'finalizado'
            x.save()

    @classmethod
    @ModelView.button_action('nafir.act_agregar_linea_wizard')
    def agregar_linea(cls, torneos):
        pass


class TorneosClubes(ModelSQL, ModelView):
    """Torneos - Clubes"""
    __name__ = 'nafir.torneos.clubes'

    torneo = fields.Many2One('nafir.torneos', 'Torneo', required=True)
    club = fields.Many2One('nafir.clubes', 'Club', required=True)

    def get_rec_name(self, name):
        if self.club:
            return self.club.rec_name

    @classmethod
    def search_rec_name(cls, name, clause):
        return ['OR',
            ('club',) + tuple(clause[1:]),
            ]


class TorneosCategorias(ModelSQL, ModelView):
    """Torneos - Categorias"""
    __name__ = 'nafir.torneos.categorias'

    torneo = fields.Many2One('nafir.torneos', 'Torneo', required=True)
    categoria = fields.Many2One('nafir.categorias', 'Categoria', required=True)

    def get_rec_name(self, name):
        if self.categoria:
            return self.categoria.rec_name

    @classmethod
    def search_rec_name(cls, name, clause):
        return ['OR',
            ('categoria',) + tuple(clause[1:]),
            ]

class TorneosLineas(ModelSQL, ModelView):
    """Torneos - Lineas"""
    __name__ = 'nafir.torneos.lineas'

    torneo = fields.Many2One('nafir.torneos', 'Torneo', required=True)
    club = fields.Many2One('nafir.clubes', 'Club', required=True)
    categoria = fields.Many2One('nafir.categorias', 'Categoria', required=True)
    linea = fields.Many2One('nafir.clubes.lineas', 'Linea', required=True)

    def get_rec_name(self, name):
        if self.club and self.linea and self.categoria:
            return self.club.rec_name + ' - ' + self.categoria.rec_name + ' - ' + self.linea.rec_name

    @classmethod
    def search_rec_name(cls, name, clause):
        return ['OR',
            ('categoria',) + tuple(clause[1:]),
            ('club',) + tuple(clause[1:]),
            ('linea',) + tuple(clause[1:]),
            ]

class TorneosFechas(ModelSQL, ModelView):
    """Torneos - Fechas"""
    __name__ = 'nafir.torneos.fechas'

    torneo = fields.Many2One('nafir.torneos', 'Torneo', required=True)
    numero = fields.Integer('Numero', required=True)
    fecha = fields.Date('Fecha', required=True)
    partidos = fields.One2Many('nafir.torneos.fechas.partidos', 'fecha', 'Partidos')

    def get_rec_name(self, name):
        if self.fecha and self.numero:
            return str(self.numero) + '-' + str(self.fecha)


class TorneosPartidos(ModelSQL, ModelView):
    """Partidos"""
    __name__ = 'nafir.torneos.fechas.partidos'

    fecha = fields.Many2One('nafir.torneos.fechas', 'Fecha', required=True)
    categoria = fields.Many2One('nafir.torneos.categorias', 'Categoria', required=True)
    club_local = fields.Many2One('nafir.torneos.clubes', 'Club Local', required=True)
    club_visitante = fields.Many2One('nafir.torneos.clubes', 'Club Visitante', required=True)
    cancha = fields.Char('Cancha', required=True)
    hora = fields.Char('Hora', required=True)


    def get_rec_name(self, name):
        if self.fecha and self.club_local and self.club_visitante:
            return self.fecha.rec_name + ' - ' + self.club_local.rec_name + ' Vrs ' + self.club_visitante.rec_name

    @classmethod
    def search_rec_name(cls, name, clause):
        return ['OR',
            ('fecha',) + tuple(clause[1:]),
            ('club_local',) + tuple(clause[1:]),
            ('club_visitante',) + tuple(clause[1:]),
            ]

class Asistencia(ModelSQL, ModelView):
    """Asistencia de Jugadores"""
    __name__ = 'nafir.torneos.partidos.asistencias'

    partido = fields.Many2One('nafir.torneos.fechas.partidos', 'Partido')


class AgregarLinea(Wizard):
    """Agregar Linea - wizard"""
    __name__ = 'nafir.torneos.agregar_linea'

    start = StateView('nafir.torneos.agregar_linea.start', 'nafir.agregar_linea_start_view_form', [
        Button('Cancelar', 'end', 'tryton-cancel'),
        Button('Guardar', 'accept', 'tryton-ok')])
    accept = StateTransition()


    def default_start(self, fields):
        default = {'torneo': Transaction().context['active_id']}
        return default

    def transition_accept(self):
        torneo = self.start.torneo
        a_crear_clubes = []
        a_crear_categorias = []
        a_crear_lineas = []
        for x in self.start.detalle:
            ya_existe = TorneosClubes.search([('torneo', '=', torneo.id), ('club', '=', x.club.id)])
            if not ya_existe:
                a_crear = {'torneo': torneo.id, 'club': x.club.id}
                if a_crear not in a_crear_clubes:
                    a_crear_clubes.append(a_crear)
            ya_existe = TorneosCategorias.search([('torneo', '=', torneo.id), ('categoria', '=', x.linea.categoria.id)])
            if not ya_existe:
                a_crear = {'torneo': torneo.id, 'categoria': x.linea.categoria.id}
                if a_crear not in a_crear_categorias:
                    a_crear_categorias.append(a_crear)
            ya_existe = TorneosLineas.search([('torneo', '=', torneo.id), ('linea', '=', x.linea.id)])
            if not ya_existe:
                a_crear = {'torneo': torneo.id, 'club': x.club.id, 'categoria': x.linea.categoria.id, 'linea': x.linea.id}
                if a_crear not in a_crear_lineas:
                    a_crear_lineas.append(a_crear)

        TorneosClubes.create(a_crear_clubes)
        TorneosCategorias.create(a_crear_categorias)
        TorneosLineas.create(a_crear_lineas)
        return 'end'


class AgregarLineaStart(ModelSQL, ModelView):
    """Agregar Linea - start"""
    __name__='nafir.torneos.agregar_linea.start'

    torneo = fields.Many2One('nafir.torneos', 'Torneo')
    detalle = fields.One2Many('nafir.torneos.agregar_linea.detalle', None, 'Lineas')


class AgregarLineaDetalle(ModelSQL, ModelView):
    """Agregar Linea - Detalle"""
    __name__='nafir.torneos.agregar_linea.detalle'

    club = fields.Many2One('nafir.clubes', 'Club', required=True)
    linea = fields.Many2One('nafir.clubes.lineas', 'Linea', domain=[('club', '=', Eval('club'))], required=True)