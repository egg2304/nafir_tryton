import datetime
from decimal import Decimal
from trytond.pyson import Eval
from trytond.model import fields, ModelSQL, ModelView, ModelSingleton, DeactivableMixin
from trytond.pool import Pool
from trytond.exceptions import UserError
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, StateTransition, Button
import qrcode
import os
import io
import random

class CargarDatosDePrueba(Wizard):
    """Cargar datos de prueba - wizard"""
    __name__ = 'nafir.cargar_datos_prueba'

    start = StateView('nafir.cargar_datos_prueba.start', 'nafir.cargar_datos_prueba_start_view_form', [
        Button('Cancelar', 'end', 'tryton-cancel'),
        Button('Guardar', 'accept', 'tryton-ok')])
    accept = StateTransition()

    def transition_accept(self):
        Jugadores = Pool().get('nafir.jugadores')
        Categorias = Pool().get('nafir.categorias')
        Clubes = Pool().get('nafir.clubes')
        Lineas = Pool().get('nafir.clubes.lineas')
        JugadoresLinea = Pool().get('nafir.jugadores.lineas')
        JugadoresTorneos = Pool().get('nafir.jugadores.tipo_torneo')
        # Agrego Lineas
        clubes_sin_linea = Clubes.search([])
        lineas_desc = ['Blanca', 'Azul', 'Roja']
        lineas_a_crear = []
        for club in clubes_sin_linea:
            if not(club.lineas):
                if len(lineas_desc) == 1:
                    lineas_desc = ['Blanca', 'Azul', 'Roja']
                elif len(lineas_desc) == 3:
                    lineas_desc = ['Blanca', 'Azul']
                elif len(lineas_desc) == 2:
                    lineas_desc = ['Blanca']
                for linea in lineas_desc:
                    lineas_a_crear.append({'club': club.id,
                                           'nombre': linea})
        Lineas.create(lineas_a_crear)

        # Agrego la categoria a los jugadores
        jugadores = Jugadores.search([('categoria', '=', None)])
        for jug in jugadores:
            if jug.fecha_nacimiento:
                cat = Categorias.search([('anio', '=', jug.fecha_nacimiento.year)])
                if cat:
                    jug.categoria = cat[0].id
                    jug.save()

        # Agrego fichajes
        a_crear_jugadores_lineas = []
        jugadores = Jugadores.search([('fecha_nacimiento', '!=', None)])
        lineas = Lineas.search([])
        count = 0
        for jug in jugadores:
            count +=1
            if jug.lineas:
                continue
            categorias = Categorias.search([('anio', '>=', jug.fecha_nacimiento.year + 10), ('anio', '<=', datetime.date.today().year)])
            anios = []
            for x in categorias:
                juega_este_anio = random.randint(0, 4)
                if juega_este_anio > 1: #60% de probabilidad que si juegue
                    anios.append(int(x.anio))
            va_cambiando_de_equipos = random.randint(0, 4) #20% de probabilidad que cambie de equipo
            va_cambiando_de_equipos = True if va_cambiando_de_equipos == 0 else False
            linea = lineas[random.randint(0, len(lineas)-1)]
            for anio in anios:
                a_crear_jugadores_lineas.append({'jugador': jug.id,
                                                 'club': linea.club.id,
                                                 'linea': linea.id,
                                                 'fecha_desde': datetime.date(anio, 1,1),
                                                 'fecha_hasta': datetime.date(anio, 12,31),
                                                 'anio_desde': anio,
                                                 })
                if va_cambiando_de_equipos:
                    cambiar_este_anio = random.randint(0, 2)
                    if cambiar_este_anio == 0:
                        linea = lineas[random.randint(0, len(lineas) - 1)]

            if count == 500:
                count = 0
                JugadoresLinea.create(a_crear_jugadores_lineas)
                a_crear_jugadores_lineas = []
        JugadoresLinea.create(a_crear_jugadores_lineas)

        #inicializar los tipos de torneos de los jugadores
        jugadores = Jugadores.search([])
        Tipos = Pool().get('nafir.tipo_torneo')
        tipos = Tipos.search([])
        a_crear_tipos = []
        count = 0
        for jug in jugadores:
            count +=1
            if jug.tipos_torneos:
                continue
            #probabilidad de agregarle todos los tipos 50%
            agrego_todos_tipos  = random.randint(0, 1)
            for tipo in tipos:
                #probabilidad de agregarle cada uno 50%
                agrego_este_tipo = random.randint(0, 1)
                if agrego_todos_tipos == 1 or agrego_este_tipo == 1:
                    a_crear_tipos.append({'jugador': jug.id,
                                          'tipo_torneo': tipo.id})
            if count == 500:
                count = 0
                JugadoresTorneos.create(a_crear_tipos)
                a_crear_tipos = []
        JugadoresTorneos.create(a_crear_tipos)
        return 'end'


class CargarDatosDePruebaStart(ModelSQL, ModelView):
    """Cargar datos de prueba - start"""
    __name__='nafir.cargar_datos_prueba.start'

