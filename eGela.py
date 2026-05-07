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
        moddleSession = respuesta.headers['Set-Cookie'].split(";")[0]
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
            sys.exit(0)

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
            self._login = 1
            self._cookie = moddleSession
            self._curso = uri
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

        progress_step = float(100.0 / len(NUMERO_DE_PDF_EN_EGELA))


        print("\n##### Analisis del HTML... #####")
        #############################################
        # ANALISIS DE LA PAGINA DEL AULA EN EGELA
        # PARA BUSCAR PDFs
        #############################################

        # INICIALIZA Y ACTUALIZAR BARRA DE PROGRESO
        # POR CADA PDF ANIADIDO EN self._refs

        progress_step = float(100.0 / len(NUMERO_DE_PDF_EN_EGELA))

        progress += progress_step
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(0.1)

        popup.destroy()
        return self._refs

    def get_pdf(self, selection):

        print("\t##### descargando  PDF... #####")
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################

        return pdf_name, pdf_content