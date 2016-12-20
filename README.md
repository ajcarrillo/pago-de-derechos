# Billy - Servicio de pago de derechos para Siem

## Dependencias

```
Django==1.10
MySQL-python==1.2.5
django-debug-toolbar==1.5
djangorestframework==3.3.3
factory-boy==2.7.0
fake-factory==0.5.7
ipaddress==1.0.16
python-dateutil==2.5.3
requests==2.11.1
six==1.10.0
sqlparse==0.2.0
wsgiref==0.1.2

```

##### PentahoReport
* Clonar la rama para python del proyecto PentahoReport, en un directorio de tu proyecto. 

```
git clone -b report-designer-python  https://gitlab.com/educacionqroomx/PentahoReport.git
```

## :baby_symbol: Baby steps I

* Hacer una copia del archivo ```local_settings.template.py``` y cambiar nombre a ```local_settings.py``` 

Instalar dependencias:

```
$ pip install -r requirements.txt
```

### Actualizar dependencias (Backend)

Si instalas un paquete de python deberás actualizar el archivo ```requirements.txt``` y añadir tu nuevo paquete ya sea 
manualmente ó utilizando el comando ```$ pip freeze > requirements.txt```

**Nota: El comando ```$ pip freeze > requirements.txt``` te devuelve todos los paquetes instalados en tu environment, incluidos
los paquetes que no usas en el proyecto, es muy importante que mantengas limpio este archivo de paquetes que no son 
dependencias para el proyecto.**

## :baby_symbol: Baby steps II

### Base de datos

Configuración de tu base de datos.

```python
DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.mysql',
		'NAME': 'YourDatabaseName',
		'USER': 'YourUsername',
		'PASSWORD': 'YourPassword',
		'HOST': 'SomeIPAddress',
		'PORT': 'ThePort',
	}
}
```

Ejecutar el siguiente comando para aplicar las migraciones e inicializar la base de datos

```
$ ./manage.py migrate
```

Si por alguna razón necesitas reiniciar la base de datos tienes disponible el siguiente comando.

```
$ ./manage.py reset_db
```

**Nota: el comando ```reset_db``` elimina TODAS las tablas de de la base de datos, ```TODAS```, por lo cual después de
 ejecutar el comando deberás aplicar las migraciones nuevamente**
 
 Happy Coding!! :slight_smile::upside_down:
 
 P.S. Alimentate sanamente, come frutas y verduras. :tomato::hot_pepper::corn:



