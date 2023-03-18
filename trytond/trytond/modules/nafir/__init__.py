from trytond.pool import Pool

def register():
    from . import nafir
    from . import torneos

    Pool.register(
        nafir.Ciudades,
        nafir.Categorias,
        nafir.Clubes,
        nafir.Lineas,
        nafir.Jugadores,
        nafir.JugadoresLineas,
        torneos.Torneos,
        torneos.TorneosCategorias,
        torneos.TorneosClubes,
        torneos.TorneosLineas,
        torneos.AgregarLineaStart,
        torneos.AgregarLineaDetalle,
        torneos.TorneosFechas,
        torneos.TorneosPartidos,
        module='nafir', type_='model')

    Pool.register(
        torneos.AgregarLinea,
        module='nafir', type_='wizard')
