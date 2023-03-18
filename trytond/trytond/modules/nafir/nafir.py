import datetime
from decimal import Decimal
from trytond.pyson import Eval
from trytond.model import fields, ModelSQL, ModelView, ModelSingleton, DeactivableMixin
from trytond.pool import Pool
from trytond.exceptions import UserError
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, StateTransition, Button


class Ciudades(ModelSQL, ModelView):
    """Ciudades"""
    __name__ = 'nafir.ciudades'
    _rec_name = 'nombre'

    nombre = fields.Char(u'Nombre', required=True)
    clubes = fields.One2Many('nafir.clubes', 'ciudad', 'Clubes')
    jugadores = fields.One2Many('nafir.jugadores', 'ciudad', 'Jugadores')


class Categorias(ModelSQL, ModelView):
    """Categorias"""
    __name__ = 'nafir.categorias'
    _rec_name = 'anio'

    anio = fields.Char(u'Año', required=True)
    categoria_previa = fields.Many2One('nafir.categorias', 'Categoria Previa')
    lineas = fields.One2Many('nafir.clubes.lineas', 'categoria', 'Lineas')
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

    nombre = fields.Char(u'Nombre', required=True)
    categoria = fields.Many2One('nafir.categorias', 'Categoria', required=True)
    club = fields.Many2One('nafir.clubes', 'Club', required=True)
    jugadores = fields.One2Many('nafir.jugadores.lineas', 'linea', 'Jugadores')

    def get_rec_name(self, name):
        if self.club and self.categoria and self.nombre:
            return self.club.rec_name + ' - ' + self.categoria.rec_name + ' - ' + str(self.nombre)

    @classmethod
    def search_rec_name(cls, name, clause):
        return ['OR',
            ('nombre',) + tuple(clause[1:]),
            ('club',) + tuple(clause[1:]),
            ('categoria',) + tuple(clause[1:]),
            ]


class Jugadores(ModelSQL, ModelView):
    """Jugadores"""
    __name__ = 'nafir.jugadores'

    dni = fields.Char(u'DNI')
    carnet = fields.Char(u'Numero de Carnet')
    nombre = fields.Char(u'Nombre', required=True)
    apellido = fields.Char(u'Apellido', required=True)
    fecha_nacimiento = fields.Date(u'Fecha de Nacimiento')
    domicilio = fields.Char(u'Domicilio')
    categoria = fields.Function(fields.Many2One('nafir.categorias', 'Categoria'), 'on_change_with_categoria', searcher='search_categoria')
    telefono = fields.Char(u'Telefono')
    lineas = fields.One2Many('nafir.jugadores.lineas', 'jugador', 'Lineas')
    fecha_inscripcion = fields.Date('Fecha de Inscripcion')
    ciudad = fields.Many2One('nafir.ciudades', 'Ciudad')
    grupo_sanguineo = fields.Selection([('', ''),('a', 'A'),('b', 'B'),('ab', 'AB'),('0', '0'),], u'Grupo Sanguineo')
    factor = fields.Selection([('', ''),('+', '+'),('-', '-'),], u'Factor Rh')
    nombre_padre = fields.Char(u'Nombre Padre')
    nombre_madre = fields.Char(u'Nombre Madre')
    observaciones = fields.Text(u'Observaciones')
    club = fields.Function(fields.Many2One('nafir.clubes', 'Club'), 'on_change_with_club', searcher='search_club')
    #qr?

    @fields.depends('fecha_nacimiento')
    def on_change_with_categoria(self, name=None):
        if self.fecha_nacimiento:
            cat = Categorias.search([('anio', '=', self.fecha_nacimiento.year)])
            if cat:
                return cat[0].id

    @classmethod
    def search_categoria(cls, name, clause):
        categ = Categorias(clause[2][0])
        fecha_desde = datetime.date(int(categ.anio),1,1)
        fecha_hasta = datetime.date(int(categ.anio),12,31)
        return [('fecha_nacimiento', '>=', fecha_desde),
                ('fecha_nacimiento', '<=', fecha_hasta)]

    def obtener_club_actual(self):
        if self.lineas:
            for x in self.lineas:
                if x.fecha_desde:
                    if x.fecha_desde < datetime.date.today() and (x.fecha_hasta is None or x.fecha_hasta >= datetime.date.today()):
                        return x.club
        return None

    @fields.depends('lineas')
    def on_change_with_club(self, name=None):
        club = self.obtener_club_actual()
        return club.id if club else None

    def get_rec_name(self, name):
        if self.nombre and self.apellido:
            return self.nombre + ' ' + str(self.apellido)

    @classmethod
    def search_club(cls, name, clause):
        lineas = JugadoresLineas.search([('club', '=', clause[2][0])])
        lista_ids = []
        for x in lineas:
            lista_ids.append(x.jugador.id)
        return [('id', 'in' if clause[2] else 'not in', lista_ids)]

    @classmethod
    def search_rec_name(cls, name, clause):
        return ['OR',
            ('nombre',) + tuple(clause[1:]),
            ('apellido',) + tuple(clause[1:]),
            ]


class JugadoresLineas(ModelSQL, ModelView):
    """Lineas de Jugadores"""
    __name__ = 'nafir.jugadores.lineas'

    jugador = fields.Many2One('nafir.jugadores', 'Jugador', required=True)
    categoria = fields.Function(fields.Many2One('nafir.categorias', 'Categoria'), 'on_change_with_categoria', searcher='search_categoria')
    club = fields.Many2One('nafir.clubes', 'Club', required=True)
    linea = fields.Many2One('nafir.clubes.lineas', 'Linea', domain=[('club', '=', Eval('club')), ('categoria', '=', Eval('categoria'))])
    fecha_desde = fields.Date('Fecha Desde', required=True)
    fecha_hasta = fields.Date('Fecha Hasta')

    @fields.depends('jugador', '_parent_jugador.fecha_nacimiento')
    def on_change_with_categoria(self, name=None):
        if self.jugador and self.jugador.fecha_nacimiento:
            cat = Categorias.search([('anio', '=', self.jugador.fecha_nacimiento.year)])
            if cat:
                return cat[0].id

    @classmethod
    def search_categoria(cls, name, clause):
        lineas = Lineas.search([('categoria', '=', clause[2][0])])
        lista_ids = []
        for x in lineas:
            lista_ids.append(x.id)
        return [('linea', 'in' if clause[2] else 'not in', lista_ids)]
