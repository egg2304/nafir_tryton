import datetime
from decimal import Decimal
from trytond.pyson import Eval, Not
from trytond.model import fields, ModelSQL, ModelView, ModelSingleton, DeactivableMixin
from trytond.pool import Pool
from trytond.exceptions import UserError
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, StateTransition, Button
import qrcode
import os
import io


class Jugadores(ModelSQL, ModelView):
    """Jugadores"""
    __name__ = 'nafir.jugadores'

    dni = fields.Char(u'DNI')
    carnet = fields.Char(u'Numero de Carnet')
    numero_carnet = fields.Integer(u'Numero de Carnet')
    nombre = fields.Char(u'Nombre', required=True)
    apellido = fields.Char(u'Apellido', required=True)
    fecha_nacimiento = fields.Date(u'Fecha de Nacimiento')
    domicilio = fields.Char(u'Domicilio')
    categoria = fields.Many2One('nafir.categorias', 'Categoria', readonly=True)
    telefono = fields.Char(u'Telefono')
    lineas = fields.One2Many('nafir.jugadores.lineas', 'jugador', 'Fichaje')
    tipos_torneos = fields.One2Many('nafir.jugadores.tipo_torneo', 'jugador', 'Tipos de Torneo donde juega')
    fecha_inscripcion = fields.Date('Fecha de Inscripcion')
    ciudad = fields.Many2One('nafir.ciudades', 'Ciudad')
    grupo_sanguineo = fields.Selection([('', ''),('a', 'A'),('b', 'B'),('ab', 'AB'),('0', '0'),], u'Grupo Sanguineo')
    factor = fields.Selection([('', ''),('+', '+'),('-', '-'),], u'Factor Rh')
    nombre_padre = fields.Char(u'Nombre Padre')
    nombre_madre = fields.Char(u'Nombre Madre')
    observaciones = fields.Text(u'Observaciones')
    club = fields.Function(fields.Many2One('nafir.clubes', 'Club'), 'on_change_with_club', searcher='search_club')
    foto = fields.Binary('Foto')
    qr_image = fields.Binary('QR')

    @classmethod
    def __register__(cls, module_name):
        super(Jugadores, cls).__register__(module_name)
        jugadores_sin_qr = Jugadores.search([('qr_image', '=', None), ('numero_carnet', '!=', None)])
        for x in jugadores_sin_qr:
            x.generar_qr(True)

    @classmethod
    def __setup__(cls):
        super(Jugadores, cls).__setup__()
        cls._buttons.update({
            'obtener_qr': {'readonly': False},
            'agregar_fichaje': {'readonly': False},
        })

    @classmethod
    def create(cls, vlist):
        Categorias = Pool().get('nafir.categorias')

        vlist = [v.copy() for v in vlist]
        for values in vlist:
            if 'fecha_nacimiento' in values:
                try:
                    cat = Categorias.search([('anio', '=', values['fecha_nacimiento'].year)])
                    if cat:
                        values['categoria'] = cat[0].id
                except:
                    pass
        jugador = super(Jugadores, cls).create(vlist)
        jugador[0].generar_qr(True)
        return jugador

    @classmethod
    def write(cls, *args):
        Categorias = Pool().get('nafir.categorias')
        actions = iter(args)
        args = []
        for jugadores, values in zip(actions, actions):
            values = values.copy()
            for jugador in jugadores:
                if 'fecha_nacimiento' in values:
                    cat = Categorias.search([('anio', '=', values['fecha_nacimiento'].year)])
                    if cat:
                        values['categoria'] = cat[0].id
            args.extend((jugadores, values))
        super(Jugadores, cls).write(*args)

    @classmethod
    @ModelView.button_action('nafir.act_agregar_fichaje')
    def agregar_fichaje(cls, jugadores):
        pass

    @classmethod
    @ModelView.button
    def obtener_qr(cls, jugadores):
        for jug in jugadores:
            jug.generar_qr(True)

    def generar_qr(self, guardar):
        if self.numero_carnet:
            d = self.numero_carnet
            qr_image = qrcode.make(d)
            holder = io.BytesIO()
            qr_image.save(holder)
            qr_png = holder.getvalue()
            holder.close()
            self.qr_image = bytearray(qr_png)
            if guardar:
                self.save()

    @fields.depends('numero_carnet', 'qr_image')
    def on_change_nombre(self):
        if self.id <0:
            with Transaction().new_transaction() as transaction, transaction.connection.cursor() as cursor:
                cursor.execute('select max(numero_carnet) from nafir_jugadores')
                a=cursor.fetchall()
            self.numero_carnet = a[0][0] + 1
            self.generar_qr(False)

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
        if clause[1] == 'in':
            club = clause[2][0]
            busqueda = '='
        else:
            Clubes = Pool().get('nafir.clubes')
            clubes = Clubes.search([('nombre', clause[1], clause[2])])
            club = []
            for x in clubes:
                club.append(x.id)
            busqueda = 'in'
        lineas = JugadoresLineas.search([('club', busqueda, club), ('fecha_desde', '<=', datetime.date.today()), ('fecha_hasta', '>=', datetime.date.today())])
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
    """Fichaje de jugadores"""
    __name__ = 'nafir.jugadores.lineas'

    jugador = fields.Many2One('nafir.jugadores', 'Jugador', required=True)
    club = fields.Many2One('nafir.clubes', 'Club', required=True, readonly=True)
    linea = fields.Many2One('nafir.clubes.lineas', 'Linea', domain=[('club', '=', Eval('club'))], readonly=True)
    fecha_desde = fields.Date('Fecha Desde', required=True)
    anio_desde = fields.Integer('Anio desde')
    fecha_hasta = fields.Date('Fecha Hasta')
    requiere_libre_deuda = fields.Boolean('Requiere Libre Deuda', readonly=True)
    libre_deuda = fields.Boolean('Entrego Libre deuda', states={'invisible': ~Eval('requiere_libre_deuda')})
    mensajes = fields.Text('Mensajes', readonly=True)
    ultimo_fichaje = fields.Function(fields.Boolean('Es el Ultimo fichaje'), 'on_change_with_ultimo_fichaje')
    juego_tipo_torneo = fields.Function(fields.Boolean('Juego el tipo de Torneo'), 'on_change_with_juego_tipo_torneo', searcher='search_juego_tipo_torneo')

    @fields.depends('id')
    def on_change_with_ultimo_fichaje(self, name=None):
        if self.jugador and self.fecha_hasta:
            otros_fichajes = JugadoresLineas.search([('jugador', '=', self.jugador.id)], order=[('fecha_hasta', 'DESC')])
            if otros_fichajes:
                if otros_fichajes[0] == self:
                    return True
            return False

    @classmethod
    def __setup__(cls):
        super(JugadoresLineas, cls).__setup__()
        cls._order.insert(0, ('fecha_hasta', 'DESC'))
        cls._buttons.update({
            'renovar': {'invisible': Not(Eval('ultimo_fichaje'))},
        })

    @classmethod
    def renovar(cls, lineas):
        linea = lineas[0]
        if linea.fecha_hasta:
            if linea.fecha_hasta.year >= (datetime.date.today().year -1):
                linea.fecha_hasta = datetime.date(linea.fecha_hasta.year+1, linea.fecha_hasta.month, linea.fecha_hasta.day)
                linea.save()
            else:
                raise UserError(u'Solo se puede renovar un fichaje del año anterios o de este año')

    @fields.depends('id')
    def on_change_with_juego_tipo_torneo(self):
        return True

    @classmethod
    def search_juego_tipo_torneo(cls, name, clause):
        jug_tipos = JugadoresTiposTorneo.search([('tipo_torneo', '=', clause[2])])
        lista_ids = []
        for x in jug_tipos:
            lista_ids.append(x.jugador.id)
        return [('jugador', 'in' , lista_ids)]


class JugadoresTiposTorneo(ModelSQL, ModelView):
    """Tipos de torneos donde juegan los jugadores"""
    __name__ = 'nafir.jugadores.tipo_torneo'

    jugador = fields.Many2One('nafir.jugadores', 'Jugador', required=True)
    tipo_torneo = fields.Many2One('nafir.tipo_torneo', 'Tipo de Torneo', required=True)


class AgregarFichaje(Wizard):
    """AgregarFichaje - wizard"""
    __name__ = 'nafir.agregar_fichaje'

    start = StateView('nafir.agregar_fichaje.start', 'nafir.agregar_fichaje_start_view_form', [
        Button('Cancelar', 'end', 'tryton-cancel'),
        Button('Guardar', 'accept', 'tryton-ok')])
    accept = StateTransition()


    def default_start(self, fields):
        default = {'jugador': Transaction().context['active_id']}
        return default

    def transition_accept(self):
        JugadoresLineas.create([{'jugador': self.start.jugador.id,
                                 'club': self.start.club.id,
                                 'linea': self.start.linea.id,
                                 'fecha_desde': self.start.fecha_desde,
                                 'anio_desde': self.start.anio_desde,
                                 'fecha_hasta': self.start.fecha_hasta,
                                 'requiere_libre_deuda': self.start.requiere_libre_deuda,
                                 'libre_deuda': self.start.libre_deuda,
                                 'mensajes': self.start.mensajes,
                                 }])
        return 'end'


class AgregarFichajeStart(ModelSQL, ModelView):
    """AgregarFichaje - start"""
    __name__='nafir.agregar_fichaje.start'

    jugador = fields.Many2One('nafir.jugadores', 'Jugador', required=True, readonly=True)
    club = fields.Many2One('nafir.clubes', 'Club', required=True)
    linea = fields.Many2One('nafir.clubes.lineas', 'Linea', domain=[('club', '=', Eval('club'))])
    fecha_desde = fields.Date('Fecha Desde', required=True, depends=['jugador', 'club'])
    anio_desde = fields.Integer('Anio desde', depends=['fecha_desde', 'jugador', 'club'])
    fecha_hasta = fields.Date('Fecha Hasta', depends=['fecha_desde', 'jugador', 'club'])
    requiere_libre_deuda = fields.Boolean('Requiere Libre Deuda', depends=['fecha_desde', 'jugador', 'club'], readonly=True)
    libre_deuda = fields.Boolean('Entrego Libre deuda', states={'invisible': ~Eval('requiere_libre_deuda')})
    mensajes = fields.Text('Mensajes', readonly=True, depends=['fecha_desde', 'jugador', 'club'])

    #@fields.depends('fecha_hasta', 'anio_desde', 'requiere_libre_deuda', 'mensajes')
    @fields.depends('fecha_desde', 'jugador', 'club')
    #@fields.depends('fecha_desde')
    def on_change_fecha_desde(self):
        if self.fecha_desde and self.jugador and self.club:
            self.fecha_hasta = datetime.date(self.fecha_desde.year,12,31)
            self.anio_desde = self.fecha_desde.year
            otro_fichaje = JugadoresLineas.search([('jugador', '=', self.jugador.id),
                                                   ('anio_desde', '=', self.fecha_desde.year - 1),
                                                   ('club', '!=', self.club.id)])
            mensajes = ''
            if otro_fichaje:
                self.requiere_libre_deuda = True
                mensajes += 'El jugador pertenecia a otro club el año pasado, por lo que debe presentar libre deuda \n'

            otro_fichaje = JugadoresLineas.search([('jugador', '=', self.jugador),
                                                   ('anio_desde', '=', self.fecha_desde.year)])
            if otro_fichaje:
                mensajes += 'El jugador ya tiene otro fichaje para el mismo anio \n'
            self.mensajes = mensajes

