# -*- encoding: utf-8 -*-
import decimal

from app.solicitud_pago.models import Concepto

conceptos = (
	('001', 350, 'Análisis y calificación para la autorización a particulares para impartir educación preescolar'),
	('002', 350, 'Análisis y calificación para la autorización a particulares para impartir educación primaria'),
	('003', 350, 'Análisis y calificación para la autorización a particulares para impartir educación secundaria'),
	('004', 500, 'Análisis y calificación para la autorización a particulares para impartir educación normal'),
	('005', 1.5, 'Análisis y calificación para el seguimiento y control escolar a particulares que imparten educación preescolar, en cada ciclo escolar, por alumno'),
	('006', 1.5, 'Análisis y calificación para el seguimiento y control escolar a particulares que imparten educación primaria, en cada ciclo escolar, por alumno'),
	('007', 1.5, 'Análisis y calificación para el seguimiento y control escolar a particulares que imparten educación secundaria, en cada ciclo escolar, por alumno'),
	('008', 1.5, 'Análisis y calificación para el seguimiento y control escolar a particulares que imparten educación normal, en cada ciclo escolar, por alumno'),
	('009', 60, 'Refrendo y/o actualización del acuerdo de incorporación a particulares que imparten educación preescolar, en cada ciclo escolar'),
	('010', 60, 'Refrendo y/o actualización del acuerdo de incorporación a particulares que imparten educación primaria, en cada ciclo escolar'),
	('011', 60, 'Refrendo y/o actualización del acuerdo de incorporación a particulares que imparten educación secundaria, en cada ciclo escolar'),
	('012', 60, 'Refrendo y/o actualización del acuerdo de incorporación a particulares que imparten educación normal, en cada ciclo escolar'),
	('013', 1.4, 'Certificaciones de estudios de educación primaria, por alumno'),
	('014', 1.4, 'Certificaciones de estudios de educación secundaria, por alumno'),
	('015', 1.4, 'Certificaciones de estudios de educación normal, por alumno'),
	('016', 1.5, 'Exámenes extraordinarios de regularización de educación secundaria, por asignatura'),
	('017', 1.5, 'Exámenes extraordinarios de regularización de educación normal, por asignatura'),
	('018', 6.5, 'Evaluación general de conocimientos de educación primaria, por alumno'),
	('019', 6.5, 'Evaluación general de conocimientos de educación secundaria, por alumno'),
	('020', 50, 'Exámenes profesionales de educación normal, por alumno'),
	('021', 4.5, 'Revalidación de estudios de educación primaria'),
	('022', 4.5, 'Revalidación de estudios de educación secundaria'),
	('023', 8, 'Equivalencia de estudios de educación secundaria'),
	('024', 1, 'Expedición de constancia de registro de control escolar'),
	('025', 1, 'Reposición de cartillas de educación básica'),
	('026', 3.3, 'Proceso de asignación al nivel medio superior (PAENMS)')
)
for c in conceptos:
	concepto = Concepto()
	concepto.clave = c[0]
	concepto.salarios_minimos = decimal.Decimal(c[1])
	concepto.descripcion = c[2]
	concepto.save()

print 'carga de conceptos terminada\n'
