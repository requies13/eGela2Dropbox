import posixpath

import requests
import urllib
import webbrowser
from socket import AF_INET, socket, SOCK_STREAM
import json
import helper

app_key = 'yvw6a3nqm23ze9b'
app_secret = '8lhylr3lwovusgn'
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
        print("\n/list_folder")
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
        codigo = respuesta.status_code
        print(f"Respuesta: {codigo} {respuesta.reason}")

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
        print("\n/upload")
        print("Subiendo archivo " + file_path)
        uri = 'https://content.dropboxapi.com/2/files/upload'
        # https://www.dropbox.com/developers/documentation/http/documentation#files-upload
        # 2. Construir la ruta completa INCLUYENDO el nombre del archivo
        path_dropbox = f"{file_path}"
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
        print("\n/delete_file")
        print("Borrando " + file_path)
        # uri = 'https://api.dropboxapi.com/2/files/delete'
        uri = 'https://api.dropboxapi.com/2/files/delete_v2'
        # https://www.dropbox.com/developers/documentation/http/documentation#files-delete


        # 2. Construir la ruta completa INCLUYENDO el nombre del archivo
        path_dropbox = f"{file_path}".replace("//", "/")

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
        print("\n/create_folder")
        print("Creando directorio " + path)
        uri = 'https://api.dropboxapi.com/2/files/create_folder_v2'
       # https://www.dropbox.com/developers/documentation/http/documentation#files-create_folder
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################
        # 2. Construir la ruta completa INCLUYENDO el nombre del archivo
        path_dropbox = f"{path}".replace("//", "/")
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

    def share_file(self, path, email):
        print("\n/share_file")
        print("Compartiendo fichero " + path)
        uri = 'https://api.dropboxapi.com/2/sharing/add_file_member'
       # https://www.dropbox.com/developers/documentation/http/documentation#sharing-add_file_member
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################
        # 2. Construir la ruta completa INCLUYENDO el nombre del archivo
        path_dropbox = f"{path}".replace("//", "/")
        # 3. Configuración de la ruta para Dropbox (la raíz debe ser "")
        if not path_dropbox.startswith("/"):
            path_dropbox = "/" + path_dropbox
        # 4. Configuración de cabeceras y datos
        datos = {
            "file": path_dropbox,
            "access_level": "viewer",
            "members": [
                {
                    ".tag": "email",
                    "email": email
                }
            ],
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
            print("\t##### Fichero compartido con éxito #####")
            return True
        else:
            print(f"\t##### Error {respuesta.status_code} al compartir el fichero #####")
            print(respuesta.text)
            return False

    def list_shared_members(self, path):
        print("\n/list_shared_members")
        print("Obteniendo lista de personas compartidas el fichero " + path)
        uri = 'https://api.dropboxapi.com/2/sharing/list_file_members'
       # https://www.dropbox.com/developers/documentation/http/documentation#sharing-list_file_members
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################
        # 2. Construir la ruta completa INCLUYENDO el nombre del archivo
        path_dropbox = f"{path}".replace("//", "/")
        # 3. Configuración de la ruta para Dropbox (la raíz debe ser "")
        if not path_dropbox.startswith("/"):
            path_dropbox = "/" + path_dropbox
        # 4. Configuración de cabeceras y datos
        datos = {
            "file": path_dropbox,
        }

        cabeceras = {
            'Authorization': 'Bearer ' + self._access_token,
            'Content-Type': 'application/json',
        }

        # 5. Realizar la petición POST
        respuesta = requests.post(uri, headers=cabeceras, data=json.dumps(datos))
        emails = []
        # 6. Procesar la respuesta
        if respuesta.status_code == 200:
            contenido_json = respuesta.json()
            for user in contenido_json.get('users', []):
                email_user = user.get('user', '').get('email', '')
                if email_user:
                    emails.append(email_user)
            print("\t##### Lista de miembros con los que se ha compartido el fichero obtenido correctamente #####")
        else:
            print(f"\t##### Error {respuesta.status_code} al obtener lista de miembors #####")
            print(respuesta.text)

        return emails

    def revoke_access(self, path, email):
        print(f"\n/revoke_access para {email} en {path}")
        uri = 'https://api.dropboxapi.com/2/sharing/remove_file_member_2'

        datos = {
            "file": path,
            "member": {
                ".tag": "email",
                "email": email
            }
        }

        cabeceras = {
            'Authorization': 'Bearer ' + self._access_token,
            'Content-Type': 'application/json',
        }

        respuesta = requests.post(uri, headers=cabeceras, data=json.dumps(datos))

        if respuesta.status_code == 200:
            print(f"\t##### Acceso revocado con éxito a {email} #####")
            return True
        else:
            print(f"\t##### Error {respuesta.status_code} al revocar acceso #####")
            print(respuesta.text)
            return False
