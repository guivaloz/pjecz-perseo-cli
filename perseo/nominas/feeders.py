"""
Perseo - Nominas - Feeders
"""
from sqlalchemy import Column, ForeignKey, Integer, Numeric, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from config.settings import Settings
from lib.database import get_session
from lib.fechas import crear_clave_quincena
from lib.universal_mixin import UniversalMixin
from perseo.nominas.classes import Nomina

Base = declarative_base()


class CentroTrabajo(Base, UniversalMixin):
    """CentroTrabajo"""

    # Nombre de la tabla
    __tablename__ = "centros_trabajos"

    # Clave primaria
    id = Column(Integer, primary_key=True)

    # Columnas
    clave = Column(String(16), unique=True, nullable=False)
    descripcion = Column(String(256), nullable=False)

    # Hijos
    percepciones_deducciones = relationship("PercepcionDeduccion", back_populates="centro_trabajo")


class Concepto(Base, UniversalMixin):
    """Concepto"""

    # Nombre de la tabla
    __tablename__ = "conceptos"

    # Clave primaria
    id = Column(Integer, primary_key=True)

    # Columnas
    clave = Column(String(16), unique=True, nullable=False)
    descripcion = Column(String(256), nullable=False)

    # Hijos
    percepciones_deducciones = relationship("PercepcionDeduccion", back_populates="concepto")


class Persona(Base, UniversalMixin):
    """Persona"""

    # Nombre de la tabla
    __tablename__ = "personas"

    # Clave primaria
    id = Column(Integer, primary_key=True)

    # Columnas
    rfc = Column(String(13), nullable=False, unique=True)
    nombres = Column(String(256), nullable=False)
    apellido_primero = Column(String(256), nullable=False)
    apellido_segundo = Column(String(256), nullable=False, default="")
    curp = Column(String(18), nullable=False, default="")

    # Hijos
    percepciones_deducciones = relationship("PercepcionDeduccion", back_populates="persona")


class Plaza(Base, UniversalMixin):
    """Plaza"""

    # Nombre de la tabla
    __tablename__ = "plazas"

    # Clave primaria
    id = Column(Integer, primary_key=True)

    # Columnas
    clave = Column(String(16), unique=True, nullable=False)
    descripcion = Column(String(256), nullable=False)

    # Hijos
    percepciones_deducciones = relationship("PercepcionDeduccion", back_populates="plaza")


class PercepcionDeduccion(Base, UniversalMixin):
    """Percepcion-Deduccion"""

    # Nombre de la tabla
    __tablename__ = "percepciones_deducciones"

    # Clave primaria
    id = Column(Integer, primary_key=True)

    # Claves foráneas
    centro_trabajo_id = Column(Integer, ForeignKey("centros_trabajos.id"), index=True, nullable=False)
    centro_trabajo = relationship("CentroTrabajo", back_populates="percepciones_deducciones")
    concepto_id = Column(Integer, ForeignKey("conceptos.id"), index=True, nullable=False)
    concepto = relationship("Concepto", back_populates="percepciones_deducciones")
    persona_id = Column(Integer, ForeignKey("personas.id"), index=True, nullable=False)
    persona = relationship("Persona", back_populates="percepciones_deducciones")
    plaza_id = Column(Integer, ForeignKey("plazas.id"), index=True, nullable=False)
    plaza = relationship("Plaza", back_populates="percepciones_deducciones")

    # Columnas
    quincena = Column(String(6), nullable=False)
    importe = Column(Numeric(precision=24, scale=4), nullable=False)


def feed_nominas(settings: Settings, nominas: list[Nomina]) -> int:
    """Alimentar conceptos"""

    # Inicializar contador en cero
    contador = 0

    # Cargar sesion de la base de datos
    session = get_session(settings)

    # Bucle por las nominas
    for nomina in nominas:
        # Revisar si el Concepto existe, de lo contrario SE OMITE
        concepto = session.query(Concepto).filter_by(clave=nomina.concepto_clave).first()
        if concepto is None:
            continue

        # Revisar si el Centro de Trabajo existe, de lo contrario insertarlo
        centro_trabajo = session.query(CentroTrabajo).filter_by(clave=nomina.centro_trabajo_clave).first()
        if centro_trabajo is None:
            centro_trabajo = CentroTrabajo(clave=nomina.centro_trabajo_clave, descripcion="ND")
            session.add(centro_trabajo)

        # Revisar si la Persona existe, de lo contrario insertarlo
        persona = session.query(Persona).filter_by(rfc=nomina.rfc).first()
        if persona is None:
            persona = Persona(
                rfc=nomina.rfc,
                nombres=nomina.nombres,
                apellido_primero=nomina.apellido_primero,
                apellido_segundo=nomina.apellido_segundo,
            )
            session.add(persona)

        # Revisar si la Plaza existe, de lo contrario insertarla
        plaza = session.query(Plaza).filter_by(clave=nomina.plaza_clave).first()
        if plaza is None:
            plaza = Plaza(clave=nomina.plaza_clave, descripcion="ND")
            session.add(plaza)

        # Definir Quincena
        quincena = crear_clave_quincena(settings.FECHA)

        # Alimentar
        session.add(
            PercepcionDeduccion(
                centro_trabajo=centro_trabajo,
                concepto=concepto,
                persona=persona,
                plaza=plaza,
                quincena=quincena,
                importe=nomina.importe,
            )
        )

        # Incrementar contador
        contador += 1

    # Cerrar la sesion para que se carguen los datos
    session.commit()
    session.close()

    # Terminar
    return contador
