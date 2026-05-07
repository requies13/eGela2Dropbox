# -*- coding: UTF-8 -*-
import sys
from tkinter import messagebox
import requests
import urllib
from urllib.parse import unquote
from bs4 import BeautifulSoup
import time
import helper

class eGela:
    _login = 0
    _cookie = ""
    _curso = ""
    _refs = []
    _root = None

    def __init__(self, root):
        self._root = root

    def check_credentials(self, username, password, event=None):
        username = username.get()
        password = password.get()

        popup, progress_var, progress_bar = helper.progress("check_credentials", "Logging into eGela...")
        progress = 0
        progress_var.set(progress)
        progress_bar.update()

        print("##### 1. PETICION #####")
        metodo = 'GET'
        uri = "https://egela.ehu.eus/login/index.php"
        cabeceras = {
            'Host': "egela.ehu.eus",
        }
        print("Primera solicitud:")
        print(f"Método: {metodo} | URI: {uri}")

        respuesta = requests.request(metodo, uri, headers=cabeceras, allow_redirects=False)

        codigo = respuesta.status_code
        print(f"Respuesta: {codigo} {respuesta.reason}")

        html = BeautifulSoup(respuesta.content, 'html.parser')
        logintoken = html.find('input', attrs={'name': 'logintoken'})['value']

        progress = 25
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)


        print("\n##### 2. PETICION #####")
        moddleSession = respuesta.headers['Set-Cookie'].split(";")[0]
        print(f"Set-Cookie: {moddleSession}")

        metodo = 'POST'
        cabeceras = {'Content-Type': 'application/x-www-form-urlencoded',
                     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                     'Cookie': moddleSession
                     }

        cuerpo = {'logintoken': logintoken, 'username': username, 'password': password}

        cuerpo_encoded = urllib.parse.urlencode(cuerpo)
        cabeceras['Content-length'] = str(len(cuerpo_encoded))

        print("Segunda solicitud:")
        print(f"Método: {metodo} | URI: {uri}")
        print(f"logintoken: {logintoken} | username: {username} | password:")

        respuesta = requests.request(metodo, uri, headers=cabeceras, data=cuerpo_encoded, allow_redirects=False)

        # Codigo de estado HTTP
        codigo = respuesta.status_code
        print(f"Respuesta: {codigo} {respuesta.reason}")

        progress = 50
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        print("\n##### 3. PETICION #####")
        moddleSession = respuesta.headers.get('Set-Cookie', '').split(";")[0]

        if (moddleSession == ''):
            print("Inicio de sesion incorrecto")
            COMPROBACION_DE_LOG_IN = False
            messagebox.showinfo("Alert Message", "Login incorrect!")
            sys.exit(0)

        print(f"Set-Cookie: {moddleSession}")
        print(f"Location: {respuesta.headers['Location']}")
        metodo = 'GET'
        uri = respuesta.headers['Location']
        cabeceras = {
            'Host': "egela.ehu.eus",
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Cookie': moddleSession
        }
        print("Tercera solicitud:")
        print(f"Método: {metodo} | URI: {uri}")

        respuesta = requests.request(metodo, uri, headers=cabeceras, allow_redirects=False)

        codigo = respuesta.status_code
        print(f"Respuesta: {codigo} {respuesta.reason}")

        progress = 75
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)
        popup.destroy()

        print("\n##### 4. PETICION #####")
        print(f"Location: {respuesta.headers['Location']}")
        metodo = 'GET'
        uri = respuesta.headers['Location']
        cabeceras = {
            'User-Agent': 'Mozilla/5.0',
            'Cookie': moddleSession
        }
        print("Cuarta solicitud:")
        print(f"Método: {metodo} | URI: {uri}")
        respuesta = requests.request(metodo, uri, headers=cabeceras, allow_redirects=False)

        codigo = respuesta.status_code
        print(f"Respuesta: {codigo} {respuesta.reason}")

        html = BeautifulSoup(respuesta.content, 'html.parser')


        if (codigo != 200):
            print("Inicio de sesion incorrecto")
            COMPROBACION_DE_LOG_IN = False
            messagebox.showinfo("Alert Message", "Login incorrect!")

        else:
            COMPROBACION_DE_LOG_IN = True
            asig = html.find_all('div', {'class': 'w-100'})
            for a in asig:
                if a.get_text(strip=True) == "Sistemas Web":
                    enlace_tag = a.find('a')
                    if enlace_tag:
                        uri = enlace_tag['href']
                        break

        progress = 100
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)
        popup.destroy()


        if COMPROBACION_DE_LOG_IN:
            #############################################
            # ACTUALIZAR VARIABLES
            #############################################
            self._login = 1 #Variable que indica que el login ha sido correcto
            self._cookie = moddleSession #Cookie de sesion del usuario
            self._curso = uri #Uri de la asignatura Sistemas Web de eGela
            self._root.destroy()
        else:
            messagebox.showinfo("Alert Message", "Login incorrect!")

    def get_pdf_refs(self):
        popup, progress_var, progress_bar = helper.progress("get_pdf_refs", "Downloading PDF list...")
        progress = 0
        progress_var.set(progress)
        progress_bar.update()

        print("\n##### 4. PETICION (Página principal de la asignatura en eGela) #####")
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################
        metodo = 'GET'
        uri = self._curso
        cabeceras = {}
        cabeceras['Host'] = uri.split('//')[1].split('/')[0]
        cabeceras['Cookie'] = self._cookie

        respuesta = requests.request(metodo, uri, headers=cabeceras, allow_redirects=False) #Hacemos una petición a la página del curso de SW
        codigo = respuesta.status_code
        print(f"Respuesta: {codigo} {respuesta.reason}")

        html_parseado_curso = BeautifulSoup(respuesta.content, 'html.parser')

        div_secciones = html_parseado_curso.find('div', {'class': 'tabs-wrapper'}) #Obtenemos la sección DIV que tiene los enlaces a las secciones
        lista_a_secciones = div_secciones.find_all('a') #Nos quedamos con las secciones A del DIV que tiene la información general de la seccion

        if len(lista_a_secciones) != 0:
            NUMERO_DE_SECCIONES_EN_EGELA = len(lista_a_secciones) #Al haber tantos A como secciones, con contar cuántos elementos se han encontrado previamente, nos sirve
        else:
            print("No hay secciones en eGela")
            messagebox.showinfo("Alert Message", "¡No hay secciones en eGela!")
        #print("SECCIONES EN EGELA", NUMERO_DE_SECCIONES_EN_EGELA) Debugging




        progress_step = float(100.0 / NUMERO_DE_SECCIONES_EN_EGELA)


        print("\n##### Analisis del HTML... #####")
        #############################################
        # ANALISIS DE LA PAGINA DEL AULA EN EGELA
        # PARA BUSCAR PDFs
        #############################################

        for a_seccion in lista_a_secciones:  # Bucle que recorre todas las secciones del curso
            metodo = 'GET'
            uri_seccion = a_seccion.get('href')
            cabeceras = {}
            cabeceras['Host'] = a_seccion.get('href').split('//')[1].split('/')[0]
            cabeceras['Cookie'] = self._cookie

            respuesta = requests.request(metodo, uri_seccion, headers=cabeceras, allow_redirects=False)
            html_parseado_seccion = BeautifulSoup(respuesta.content, 'html.parser')

            ruta_seccion = html_parseado_seccion.find('a', {'href': uri_seccion})
            print("\n\n------------ Obteniendo referencias de la sección: " + ruta_seccion.get('title') + " ------------")

            a_ficheros = html_parseado_seccion.find_all('a', {'class': 'aalink stretched-link'})
            for i, a_fichero in enumerate(a_ficheros):  # Bucle que recorre cada fichero/entrada de la sección actual
                diccionario_seccion = {'pdf_name': '',
                                       'pdf_link': ''}

                enlace = a_fichero.get('href')
                metodo = 'GET'
                uri_fichero = enlace
                cabeceras = {}
                cabeceras['Host'] = enlace.split('//')[1].split('/')[0]
                cabeceras['Cookie'] = self._cookie

                print("\n##### Petición enlace " + str(i) + " de la sección #####")
                respuesta = requests.request(metodo, uri_fichero, headers=cabeceras,
                                             allow_redirects=False)  # Hacemos la petición a dicho fichero

                codigo = respuesta.status_code
                print(f"Respuesta: {codigo} {respuesta.reason}")

                if codigo == 303:  # Si el fichero realmente es correcto tiene que pedirnos redirigir
                    uri = respuesta.headers['Location']
                    cabeceras = {}
                    cabeceras['Host'] = respuesta.headers['Location'].split('//')[1].split('/')[0]
                    cabeceras['Cookie'] = self._cookie

                    respuesta = requests.request(metodo, uri, headers=cabeceras, allow_redirects=False)

                    if (respuesta.headers['Content-Type'] == 'application/pdf' or respuesta.headers[
                        'Content-Type'] == 'octet-stream'):  # Se trata de un fichero PDF que hay que descargar
                        diccionario_seccion['pdf_name'] = unquote(uri.split('//')[1].split('/')[-1]) #El unquote sirve para convertir un %C3%AD en una "i" latina con tilde (í)
                        print(diccionario_seccion['pdf_name'])
                        diccionario_seccion['pdf_link'] = uri #Guardamos la URI para descargar el fichero

                        self._refs.append(diccionario_seccion) # Metemos en el array de diccionarios el fichero

            # INICIALIZA Y ACTUALIZAR BARRA DE PROGRESO
            # POR CADA SECCIÓN AÑADIDO EN self._refs
            progress_step = float(100.0 / NUMERO_DE_SECCIONES_EN_EGELA)

            progress += progress_step
            progress_var.set(progress)
            progress_bar.update()
            time.sleep(0.1)


        popup.destroy()
        print(self._refs)
        sys.exit(-1) #TODO Lo he dejado así pa que veáis que funciona. Lógicamente hay que quitarlo y seguir haciendo
        return self._refs

    def get_pdf(self, selection):

        print("\t##### descargando  PDF... #####")
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################

        return pdf_name, pdf_content