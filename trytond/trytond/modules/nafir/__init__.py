from trytond.pool import Pool

def register():
    from . import nafir
    from . import jugadores
    from . import torneos
    from . import datos_prueba

    Pool.register(
        nafir.Configuracion,
        nafir.Ciudades,
        nafir.Categorias,
        nafir.Clubes,
        nafir.Lineas,
        jugadores.Jugadores,
        nafir.TipoTorneo,
        jugadores.JugadoresLineas,
        jugadores.JugadoresTiposTorneo,
        torneos.Torneos,
        torneos.TorneosClubes,
        torneos.TorneosLineas,
        torneos.AgregarClubStart,
        torneos.AgregarClubDetalle,
        torneos.TorneosFechas,
        torneos.TorneosPartidos,
        torneos.TorneosPartidosCategorias,
        torneos.TorneosAsistenciaClubLocal,
        torneos.TorneosAsistenciaClubVisitante,
        torneos.CargarResultadoStart,
        datos_prueba.CargarDatosDePruebaStart,
        jugadores.AgregarFichajeStart,
        module='nafir', type_='model')

    Pool.register(
        jugadores.AgregarFichaje,
        torneos.AgregarClub,
        torneos.CargarResultado,
        datos_prueba.CargarDatosDePrueba,
        module='nafir', type_='wizard')
