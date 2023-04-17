import datetime
from decimal import Decimal
from trytond.pyson import Eval
from trytond.model import fields, ModelSQL, ModelView, ModelSingleton, DeactivableMixin
from trytond.pool import Pool
from trytond.exceptions import UserError
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, StateTransition, Button
import qrcode


class Configuracion(ModelSingleton, ModelSQL, ModelView):
    """Configuracion"""
    __name__ = 'nafir.configuracion'

    club_libre = fields.Many2One('nafir.clubes', 'Club', required=True)
    linea_libre = fields.Many2One('nafir.clubes.lineas', 'Linea', required=True, domain=[('club', '=', Eval('club_libre'))])


class Ciudades(ModelSQL, ModelView):
    """Ciudades"""
    __name__ = 'nafir.ciudades'
    _rec_name = 'nombre'

    nombre = fields.Char(u'Nombre', required=True)
    clubes = fields.One2Many('nafir.clubes', 'ciudad', 'Clubes')
    jugadores = fields.One2Many('nafir.jugadores', 'ciudad', 'Jugadores')


class TipoTorneo(ModelSQL, ModelView):
    """Tipos de Torneos"""
    __name__ = 'nafir.tipo_torneo'
    _rec_name = 'nombre'

    nombre = fields.Char(u'Nombre', required=True)
    solicitar_categoria = fields.Boolean(u'Solicitar Categoria')
    torneos = fields.One2Many('nafir.torneos', 'tipo', 'Torneos')


class Categorias(ModelSQL, ModelView):
    """Categorias"""
    __name__ = 'nafir.categorias'
    _rec_name = 'anio'

    anio = fields.Char(u'Año', required=True)
    categoria_previa = fields.Many2One('nafir.categorias', 'Categoria Previa')
    jugadores = fields.One2Many('nafir.jugadores', 'categoria', 'Jugadores')


class Clubes(ModelSQL, ModelView):
    """Clubes"""
    __name__ = 'nafir.clubes'
    _rec_name = 'nombre'

    nombre = fields.Char(u'Nombre', required=True)
    domicilio = fields.Char(u'Domicilio')
    telefono = fields.Char(u'Telefono')
    personeria = fields.Char(u'Personeria')
    cancha = fields.Char(u'Nombre de la cancha')
    observaciones = fields.Text(u'Observaciones')
    ciudad = fields.Many2One('nafir.ciudades', 'Ciudad')
    fecha_fundacion = fields.Date('Fecha Fundacion')
    lineas = fields.One2Many('nafir.clubes.lineas', 'club', 'Lineas')
    jugadores = fields.One2Many('nafir.jugadores', 'club', 'Jugadores')


class Lineas(ModelSQL, ModelView):
    """Lineas de Clubes"""
    __name__ = 'nafir.clubes.lineas'

    club = fields.Many2One('nafir.clubes', 'Club', required=True)
    nombre = fields.Char(u'Nombre', required=True)
    jugadores = fields.One2Many('nafir.jugadores.lineas', 'linea', 'Jugadores')

    def get_rec_name(self, name):
        if self.club and self.nombre:
            return self.club.rec_name + ' - ' + str(self.nombre)

    @classmethod
    def search_rec_name(cls, name, clause):
        return ['OR',
            ('nombre',) + tuple(clause[1:]),
            ('club',) + tuple(clause[1:]),
            ]

