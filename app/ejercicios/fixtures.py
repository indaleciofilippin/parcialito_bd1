"""Casos borde: filas extra que se insertan DENTRO de una transacción (y después se deshacen)
para comprobar que las consultas de ausencia/presencia funcionan de verdad.

Con los datos originales, varias consultas de "los que NO tienen..." devuelven 0 filas,
y una consulta mal hecha también devolvería 0 filas. Con estos datos extra se nota la diferencia.
(Es exactamente lo que pide el ejercicio 21 de la Clase Semana 10.)
"""

CASOS_BORDE = """
INSERT INTO departamentos (id_departamento, nombre, presupuesto, fecha_creacion)
VALUES (901, 'Artes', 1500000.00, '2026-01-10');

INSERT INTO alumnos (id_alumno, nombre, apellido, dni, fecha_nacimiento, email, telefono, fecha_ingreso) VALUES
 (90001, 'Bruno', 'Sincursar', '99000001', '2001-05-05', 'borde1@mail.com', '3510000001', '2026-03-01'),
 (90002, 'Carla', 'Nueva', '99000002', '2002-06-06', 'borde2@mail.com', '3510000002', '2026-03-01');

INSERT INTO alumno_carrera (id_alumno, id_carrera, fecha_inscripcion, estado)
VALUES (90002, 1, '2026-03-01', 'activa');

INSERT INTO docentes (id_docente, nombre, apellido, email, fecha_ingreso, salario_base, id_departamento) VALUES
 (9001, 'Diego', 'Sincomision', 'borde.doc1@universidad.edu', '2026-02-01', 250000.00, 1),
 (9002, 'Elena', 'Libre', 'borde.doc2@universidad.edu', '2026-02-01', 260000.00, 2);

INSERT INTO aulas (id_aula, nombre, capacidad, tipo) VALUES
 (901, 'Aula Nueva N1', 30, 'normal'),
 (902, 'Laboratorio Nuevo L9', 20, 'laboratorio');

INSERT INTO carreras (id_carrera, nombre, titulo_otorgado, nivel, modalidad, duracion_anios, carga_horaria_total, id_departamento) VALUES
 (901, 'Tecnicatura en Robótica', 'Técnico en Robótica', 'tecnicatura', 'presencial', 3, 1800, 1),
 (902, 'Licenciatura en Arte Digital', 'Licenciado en Arte Digital', 'grado', 'virtual', 4, 2600, 901);

INSERT INTO asignaturas (id_asignatura, nombre, creditos, carga_horaria, es_obligatoria, id_departamento)
VALUES (9001, 'Taller de Robótica', 6, 64, 0, 1);

INSERT INTO comisiones (id_comision, id_asignatura, id_docente, id_aula, anio, cuatrimestre, cupo, tipo) VALUES
 (90001, 1, 1, 1, 2026, 2, 40, 'teorica'),
 (90002, 2, 2, 2, 2026, 2, 35, 'practica');
"""

DESCRIPCION = [
    "Departamento 901 «Artes» sin docentes ni asignaturas.",
    "Alumnos 90001 y 90002 sin ninguna inscripción a comisiones (90002 sí está en una carrera).",
    "Docentes 9001 y 9002 sin comisiones asignadas.",
    "Aulas 901 y 902 que nunca se usaron.",
    "Carreras 901 y 902 sin alumnos.",
    "Asignatura 9001 sin comisiones ni correlatividades.",
    "Comisiones 90001 y 90002 sin alumnos inscriptos.",
]
