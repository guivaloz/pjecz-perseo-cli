"""
Perseo app
"""
import typer

from perseo.dispersiones_bancos.app import app as dispersiones_bancos_app
from perseo.dispersiones_monederos.app import app as dispersiones_monederos_app
from perseo.pensiones.app import app as pensiones_app

app = typer.Typer()
app.add_typer(dispersiones_bancos_app, name="bancos")
app.add_typer(dispersiones_monederos_app, name="monederos")
app.add_typer(pensiones_app, name="pensiones")


if __name__ == "__main__":
    app()
