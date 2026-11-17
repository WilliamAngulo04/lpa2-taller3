-- Datos iniciales para la API de Música (paso 2 del taller).
-- Ejecutar en DBeaver sobre musica.db (SQL Editor > Execute SQL Script, Alt+X).
-- Las tablas las crea la aplicación al iniciar (uvicorn main:app).

INSERT INTO usuario (nombre, correo, fecha_registro) VALUES
  ('Laura Gómez',     'laura.gomez@mail.com',     CURRENT_TIMESTAMP),
  ('Carlos Ruiz',     'carlos.ruiz@mail.com',     CURRENT_TIMESTAMP),
  ('María Fernández', 'maria.fernandez@mail.com', CURRENT_TIMESTAMP),
  ('Andrés Torres',   'andres.torres@mail.com',   CURRENT_TIMESTAMP),
  ('Valentina Díaz',  'valentina.diaz@mail.com',  CURRENT_TIMESTAMP);

INSERT INTO cancion (titulo, artista, album, duracion, "año", genero, fecha_creacion) VALUES
  ('Bohemian Rhapsody',      'Queen',          'A Night at the Opera',   355, 1975, 'Rock',      CURRENT_TIMESTAMP),
  ('Hotel California',       'Eagles',         'Hotel California',       391, 1976, 'Rock',      CURRENT_TIMESTAMP),
  ('Billie Jean',            'Michael Jackson','Thriller',               294, 1982, 'Pop',       CURRENT_TIMESTAMP),
  ('La Bicicleta',           'Carlos Vives',   'Vives',                  227, 2016, 'Vallenato', CURRENT_TIMESTAMP),
  ('Hips Don''t Lie',        'Shakira',        'Oral Fixation Vol. 2',   218, 2006, 'Pop',       CURRENT_TIMESTAMP),
  ('A Dios le Pido',         'Juanes',         'Un Día Normal',          206, 2002, 'Rock',      CURRENT_TIMESTAMP),
  ('Smells Like Teen Spirit','Nirvana',        'Nevermind',              301, 1991, 'Grunge',    CURRENT_TIMESTAMP),
  ('Despacito',              'Luis Fonsi',     'Vida',                   229, 2017, 'Reggaetón', CURRENT_TIMESTAMP),
  ('Imagine',                'John Lennon',    'Imagine',                183, 1971, 'Rock',      CURRENT_TIMESTAMP),
  ('Tusa',                   'Karol G',        'KG0516',                 200, 2019, 'Reggaetón', CURRENT_TIMESTAMP);

-- Verificación
SELECT COUNT(*) AS usuarios FROM usuario;
SELECT COUNT(*) AS canciones FROM cancion;
