import posixpath

import requests
import urllib
import webbrowser
from socket import AF_INET, socket, SOCK_STREAM
import json
import helper

app_key = '2lsfvvkg2jwwva6'
app_secret = 'a0yuz0jqtrso1l4'
server_addr = "localhost"
server_port = 8070
redirect_uri = "http://" + server_addr + ":" + str(server_port)

class Dropbox:
    _access_token = ""
    _path = "/"
    _files = []
    _root = None
    _msg_listbox = None

    def __init__(self, root):
        self._root = root

    def local_server(self):
        # por el puerto 8070 esta escuchando el servidor que generamos
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind((server_addr, server_port))
        server_socket.listen(1)
        print("\tLocal server listening on port " + str(server_port))

        # recibe la redireccion 302 del navegador
        client_connection, client_address = server_socket.accept()
        peticion = client_connection.recv(1024)
        print("\tRequest from the browser received at local server:")
        print (peticion)

        # buscar en solicitud el "auth_code"
        primera_linea =peticion.decode('UTF8').split('\n')[0]
        aux_auth_code = primera_linea.split(' ')[1]
        auth_code = aux_auth_code[7:].split('&')[0]
        print ("\tauth_code: " + auth_code)

        # devolver una respuesta al usuario
        http_response = "HTTP/1.1 200 OK\r\n\r\n" \
                        "<html>" \
                        "<head><title>Proba</title></head>" \
                        "<body>The authentication flow has completed. Close this window.</body>" \
                        "</html>"
        client_connection.sendall(http_response)
        client_connection.close()
        server_socket.close()

        return auth_code

    def do_oauth(self):
        #############################################
        # RELLENAR CON CODIGO DE LAS PETICIONES HTTP
        # Y PROCESAMIENTO DE LAS RESPUESTAS HTTP
        # PARA LA OBTENCION DEL ACCESS TOKEN
        #############################################

        print("\nStep 1.- Send a request to DropBox's OAuth 2.0 server")

        uri = "https://www.dropbox.com/oauth2/authorize"
        datos = {'client_id': app_key,
                 'redirect_uri': redirect_uri,
                 'response_type': 'code',
                 }
        datos_encoded = urllib.parse.urlencode(datos)

        print("\tOpenning browser...")
        webbrowser.open_new((uri + '?' + datos_encoded))


        # Crear servidor local que escucha por el puerto 8070
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind(('localHost', 8070))
        server_socket.listen(1)
        print("\tLocal server listening on port 8070")
        # Recibir la solicitudes 302 del navegador
        client_connection, client_address = server_socket.accept()
        peticion = client_connection.recv(1024)
        print("\tRequest from the browser received at local server:")
        # Buscar en la petición el "auth_code"
        primera_linea = peticion.decode('UTF8').split('\n')[0]
        print(primera_linea)
        aux_auth_code = primera_linea.split(' ')[1]
        auth_code = aux_auth_code[7:].split('&')[0]
        print("\tauth_code:" + auth_code)
        # Devolver una respuesta al usuario
        http_response = "HTTP/1.1 200 OK\r\n\r\n" \
                        "<html>" \
                        "<head><title>Prueba</title></head>" \
                        "<body>The authentication flow has completed. Close this window.</body>" \
                        "</html>"
        client_connection.sendall(http_response.encode(encoding="utf-8"))
        client_connection.close()
        server_socket.close()

        ###################################################################################
        # ACCESS_TOKEN: Obtener el TOKEN https://www.api.dropboxapi.com/1/oauth2/token #
        ###################################################################################
        params = {'code': auth_code,
                  'grant_type': 'authorization_code',
                  'client_id': app_key,
                  'client_secret': app_secret,
                  'redirect_uri': redirect_uri}
        cabeceras = {'User-Agent': 'Python Client',
                     'Content-Type': 'application/x-www-form-urlencoded'}
        uri = 'https://api.dropboxapi.com/oauth2/token'
        respuesta = requests.post(uri, headers=cabeceras, data=params)
        print(respuesta.status_code)
        json_respuesta = json.loads(respuesta.content)
        access_token = json_respuesta['access_token']
        print("Access_Token:" + access_token)

        self._access_token = access_token
        self._root.destroy()

    def list_folder(self, msg_listbox):
        print("/list_folder")
        uri = 'https://api.dropboxapi.com/2/files/list_folder'
        # https://www.dropbox.com/developers/documentation/http/documentation#files-list_folder
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################

        self._path = posixpath.normpath(self._path).replace("\\", "/")
        if self._path in ['.', '/.']:
            self._path = "/"

        # 2. Configuración de cabeceras
        cabeceras = {
            'Authorization': 'Bearer ' + self._access_token,
            'Content-Type': 'application/json'
        }

        # 3. Configuración de la ruta para Dropbox (la raíz debe ser "")
        path_dropbox = "" if self._path == "/" else self._path

        datos = {
            "path": path_dropbox,
        }

        # 4. Realizar la petición POST
        respuesta = requests.post(uri, headers=cabeceras, data=json.dumps(datos))

        # 5. Procesar la respuesta
        if respuesta.status_code == 200:
            contenido_json = respuesta.json()
            # Esta línea actualiza tu interfaz gráfica con los archivos recibidos
            self._files = helper.update_listbox2(msg_listbox, self._path, contenido_json)
            print("\t##### Carpeta listada con éxito #####")
        else:
            print(f"\t##### Error {respuesta.status_code} al listar la carpeta #####")
            print(respuesta.text)


    def transfer_file(self, file_path, file_data):
        print("/upload")
        uri = 'https://content.dropboxapi.com/2/files/upload'
        # https://www.dropbox.com/developers/documentation/http/documentation#files-upload
        self._path = posixpath.normpath(self._path).replace("\\", "/")
        if self._path in ['.', '/.']:
            self._path = "/"
        # 2. Construir la ruta completa INCLUYENDO el nombre del archivo
        path_dropbox = f"{self._path}{file_path}".replace("//", "/")
        # 3. Configuración de la ruta para Dropbox (la raíz debe ser "")
        if not path_dropbox.startswith("/"):
            path_dropbox = "/" + path_dropbox
        # 4. Configuración de cabeceras y datos
        datos = {
            "autorename": False,
            "mode": "add",
            "path": path_dropbox
        }

        cabeceras = {
            'Authorization': 'Bearer ' + self._access_token,
            'Content-Type': 'application/octet-stream',
            'Dropbox-API-Arg': json.dumps(datos)
        }

        # 5. Realizar la petición POST
        respuesta = requests.post(uri, headers=cabeceras, data=file_data)

        # 6. Procesar la respuesta
        if respuesta.status_code == 200:
            contenido_json = respuesta.json()
            print("\t##### Archivo transferido con éxito #####")
        else:
            print(f"\t##### Error {respuesta.status_code} al transferir el archivo #####")
            print(respuesta.text)


    def delete_file(self, file_path):
        print("/delete_file")
        uri = 'https://api.dropboxapi.com/2/files/delete_v2'
        # https://www.dropbox.com/developers/documentation/http/documentation#files-delete

        self._path = posixpath.normpath(self._path).replace("\\", "/")
        if self._path in ['.', '/.']:
            self._path = "/"

        # 2. Construir la ruta completa INCLUYENDO el nombre del archivo
        path_dropbox = f"{self._path}{file_path}".replace("//", "/")

        # 3. Configuración de la ruta para Dropbox (la raíz debe ser "")
        if not path_dropbox.startswith("/"):
            path_dropbox = "/" + path_dropbox

        # 4. Configuración de cabeceras y datos
        datos = {
            "path": path_dropbox
        }

        cabeceras = {
            'Authorization': 'Bearer ' + self._access_token,
            'Content-Type': 'application/json'
        }

        # 5. Realizar la petición POST
        respuesta = requests.post(uri, headers=cabeceras, data=json.dumps(datos))

        # 6. Procesar la respuesta
        if respuesta.status_code == 200:
            contenido_json = respuesta.json()
            print("\t##### Archivo eliminado con éxito #####")
        else:
            print(f"\t##### Error {respuesta.status_code} al eliminar el archivo #####")
            print(respuesta.text)

    def create_folder(self, path):
        print("/create_folder")
        uri = 'https://api.dropboxapi.com/2/files/create_folder_v2'
       # https://www.dropbox.com/developers/documentation/http/documentation#files-create_folder
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################

        self._path = posixpath.normpath(self._path).replace("\\", "/")
        if self._path in ['.', '/.']:
            self._path = "/"

        # 2. Construir la ruta completa INCLUYENDO el nombre del archivo
        path_dropbox = f"{self._path}{path}".replace("//", "/")

        # 3. Configuración de la ruta para Dropbox (la raíz debe ser "")
        if not path_dropbox.startswith("/"):
            path_dropbox = "/" + path_dropbox

        # 4. Configuración de cabeceras y datos
        datos = {
            "autorename": False,
            "path": path_dropbox
        }

        cabeceras = {
            'Authorization': 'Bearer ' + self._access_token,
            'Content-Type': 'application/json',
        }

        # 5. Realizar la petición POST
        respuesta = requests.post(uri, headers=cabeceras, data=json.dumps(datos))

        # 6. Procesar la respuesta
        if respuesta.status_code == 200:
            contenido_json = respuesta.json()
            print("\t##### Carpeta creada con éxito #####")
        else:
            print(f"\t##### Error {respuesta.status_code} al crear la carpeta #####")
            print(respuesta.text)
