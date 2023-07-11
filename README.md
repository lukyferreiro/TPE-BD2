# TPE-BD2 - AFK System

## Autores
- [Tomas Alvarez Escalante](https://github.com/tomalvarezz)
- [Lucas Agustin Ferreiro](https://github.com/lukyferreiro)
- [Roman Gomez Kiss](https://github.com/rgomezkiss)

# Introducción

En este TPE se implemento AFK System: un sistema de pago electronico basado en un híbrido de reconocidos sistemas de Argentina y Brasil.
Para ello se implemento una API utilizando FastApi para modelar los endpoints de nuestro sistema.
Nuestro sistema cuenta con:
- Una base de datos PosgreSQL para almacenar y consultar los usuarios, claves AFK y entidades financieras.
- Una base de datos MongoDB para almacenar las transacciones realizadas entre los usuarios.

La idea principal es que un usuario pueda asociar un CBU de cualquier entidad financiera a una clave AFK. De esta forma, un usuario
podra transferir dinero a otro usuario (de cualquier entidad financiera) utilizando unicamente la clave AFK.

Para realizar pruebas tambien se modelo una API bancaria para representar aquella a la cual nuestro
sistema se conectaría para consultar saldos, transferir o descontar dinero o asociar al CBU una clave AFK.

# Requisitos

- Docker
- Python

# Funcionamiento

## 1. Levantar API de las entidades

Posicionado en la carpeta /src/Banks se debe ejecutar:

```shell
./init.sh
```

Esto levantara un container de Docker con la base de datos de una entidad financiera.
Luego se debe ejecutar: 

```shell
./run.sh
```

Esto levantara la API del banco que estara conectada a la base de datos montada en el contenedor de Docker.

### IMPORTANTE
Ahora se debe copiar la URL base de esta API y copiarla en la variable API_LINK_1 del archivo /src/AFK_Sytem/init.sh

# 2. Levantar API de AFK system

Posicionado en la carpeta /src/AFK_Sytem se debe ejecutar:

```shell
./init.sh
```

Esto levantara dos container de Docker con las bases de datos PosgreSQL y MongoDB para nuestro sistema.
Luego se debe ejecutar: 

```shell
./run.sh
```
Esto levantara la API de nuestro sistema que estara conectada a ambas bases de datos montadas en los contenedores.